"""BYS360 canonical score calculator (methodology v1.0.0).

Deterministically computes the 7 category scores and the two composite
scores (LIVE_READINESS, TRANSFERABILITY) from:
  - config/quality/bys360_scoring_methodology_v1.json (the formula/weights)
  - config/quality/bys360_technical_debt_registry.json (open-debt penalties)
  - live re-execution of each category's quality gates (ruff/mypy/coverage/
    secret-gate/ops-audit/quality9/handover-docs-contract)

Portability: gate commands are declared in the methodology config as
structured {kind, module|script, args} entries, never a hardcoded
absolute path. The interpreter used to run them is resolved at runtime,
in order: --python CLI flag > BYS360_QUALITY_PYTHON environment variable
> sys.executable (the interpreter currently running this script). The
resolved interpreter and its source are reported in the output, and any
gate with a declared expected_version is version-checked before being
trusted -- a wrong-version tool result is reported as VERSION_MISMATCH,
never silently scored as PASS.

Gates that are structurally impossible to verify in a local run (e.g. the
PostgreSQL migration-integrity gate, which needs a live PostgreSQL 15
service) are scored UNKNOWN unless a fresh result is supplied via
--evidence, per the methodology's missing-evidence policy: UNKNOWN
contributes 0 and is never silently treated as PASS. VERSION_MISMATCH is
treated identically to UNKNOWN for scoring purposes.

Legacy scores (68/61/etc.) are never read, referenced, or used as a
calibration target by this script -- they exist only as a fixed, separate
"legacy snapshot" block in the output report, sourced from
docs/governance/BYS360_SCORING_METHODOLOGY_V1.md's own literal text.

Read-only against the repository: this script never edits source files.
It only executes read-only quality-gate scripts as subprocesses and writes
its own output report(s).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

LEGACY_SNAPSHOT = {
    "Code Quality": 68,
    "Test Assurance": 61,
    "Security": 70,
    "CI-Release": 79,
    "Operations": 64,
    "Documentation-Handover": 55,
    "Maintainability": 65,
    "LIVE_READINESS": 68,
    "TRANSFERABILITY": 61,
    "note": (
        "Historical, pre-methodology-v1 snapshot values. Not derived from any "
        "formula found in this repository; preserved for continuity only. "
        "Methodology v1.0.0 scores below are NOT a like-for-like trend against "
        "these numbers -- the methodology, categories' measurement basis, and "
        "the debt registry all differ from whatever produced this snapshot."
    ),
}

GATE_TIMEOUT_SECONDS = 240
UNVERIFIED_STATUSES = {"UNKNOWN", "VERSION_MISMATCH"}
LOCAL_OR_REMOTE_BY_PASS_RULE = {
    "exit_code_0": "LOCAL",
    "json_ok_field_true": "LOCAL",
    "exit_code_0_or_supplied_evidence": "REMOTE_OR_EVIDENCE_SUPPLIED",
    "boolean": "REGISTRY_DERIVED",
}


@dataclass
class GateResult:
    name: str
    status: str  # PASS | FAIL | UNKNOWN | VERSION_MISMATCH
    detail: str
    local_or_remote: str = "LOCAL"


@dataclass
class CategoryScore:
    category: str
    gate_component: float
    rubric_component: float
    raw_before_penalty: float
    debt_penalty: float
    final_score: float
    gate_results: list[GateResult] = field(default_factory=list)
    rubric_trace: list[str] = field(default_factory=list)
    gate_contributions: list[dict[str, Any]] = field(default_factory=list)
    rubric_contributions: list[dict[str, Any]] = field(default_factory=list)
    missing_evidence: list[dict[str, Any]] = field(default_factory=list)
    debt_penalty_breakdown: list[dict[str, Any]] = field(default_factory=list)
    debt_penalty_raw_total: float = 0.0
    debt_penalty_cap_applied: bool = False
    unverified_count: int = 0


def resolve_python(cli_python: str | None) -> tuple[str, str]:
    """Resolve the interpreter used for gate commands: --python > env var > sys.executable."""
    if cli_python:
        if not Path(cli_python).exists():
            raise SystemExit(f"--python path does not exist: {cli_python}")
        return cli_python, "explicit"
    import os

    env_python = os.environ.get("BYS360_QUALITY_PYTHON")
    if env_python:
        if not Path(env_python).exists():
            raise SystemExit(f"BYS360_QUALITY_PYTHON path does not exist: {env_python}")
        return env_python, "env"
    return sys.executable, "default-sys.executable"


def _run_argv(argv: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=GATE_TIMEOUT_SECONDS,
            shell=False,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except OSError as exc:
        return -1, f"OSError: {exc}"


def _build_argv(gate: dict[str, Any], python_path: str) -> list[str] | None:
    kind = gate.get("kind")
    if kind == "python_module":
        return [python_path, "-m", gate["module"], *gate.get("args", [])]
    if kind == "python_script":
        return [python_path, gate["script"], *gate.get("args", [])]
    return None


def _check_tool_version(python_path: str, module: str, expected: str, cwd: Path) -> tuple[bool, str]:
    returncode, output = _run_argv([python_path, "-m", module, "--version"], cwd)
    if returncode != 0:
        return False, f"could not determine {module} version (exit {returncode})"
    first_line = output.strip().splitlines()[0] if output.strip() else ""
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
    actual = match.group(1) if match else first_line
    return actual == expected, actual


def _evaluate_gate(gate: dict[str, Any], python_path: str, python_source: str, cwd: Path, evidence: dict[str, Any]) -> GateResult:
    name = gate["name"]
    pass_rule = gate.get("pass_rule", "exit_code_0")
    local_or_remote = LOCAL_OR_REMOTE_BY_PASS_RULE.get(pass_rule, "LOCAL")

    if pass_rule == "boolean":
        return GateResult(name, "UNKNOWN", "computed separately (registry-derived), not a subprocess gate", local_or_remote)

    if pass_rule == "exit_code_0_or_supplied_evidence":
        supplied = evidence.get(name)
        if supplied is not None:
            status = "PASS" if supplied is True else "FAIL"
            return GateResult(name, status, f"supplied via --evidence (interpreter irrelevant): {supplied}", local_or_remote)
        return GateResult(name, "UNKNOWN", gate.get("evidence_note", "not measurable locally; no --evidence supplied"), local_or_remote)

    expected_version = gate.get("expected_version")
    if expected_version and gate.get("kind") == "python_module":
        version_ok, actual_version = _check_tool_version(python_path, gate["module"], expected_version, cwd)
        if not version_ok:
            return GateResult(
                name, "VERSION_MISMATCH",
                f"expected {gate['module']}=={expected_version}, found '{actual_version}' via {python_source} interpreter ({python_path})",
                local_or_remote,
            )

    argv = _build_argv(gate, python_path)
    if argv is None:
        return GateResult(name, "UNKNOWN", "gate has no runnable command definition (kind must be python_module or python_script)", local_or_remote)

    returncode, output = _run_argv(argv, cwd)

    if pass_rule == "json_ok_field_true":
        try:
            payload = json.loads(output.strip().splitlines()[-1]) if output.strip() else {}
            if not isinstance(payload, dict):
                raise ValueError("not a dict")
        except Exception:
            try:
                start = output.index("{")
                payload = json.loads(output[start:])
            except Exception:
                return GateResult(name, "UNKNOWN", f"could not parse JSON output (returncode={returncode})", local_or_remote)
        ok = bool(payload.get("ok"))
        return GateResult(name, "PASS" if ok else "FAIL", f"ok={payload.get('ok')} finding_count={payload.get('finding_count')}", local_or_remote)

    status = "PASS" if returncode == 0 else "FAIL"
    detail = "exit_code=0" if returncode == 0 else f"exit_code={returncode}"
    return GateResult(name, status, detail, local_or_remote)


def _registry_open_items(registry: dict[str, Any]) -> list[dict[str, Any]]:
    active = {"OPEN", "BLOCKED", "IN_PROGRESS", "DEFERRED", "ACCEPTED_RISK"}
    return [item for item in registry.get("items", []) if item.get("status") in active]


def _open_count_in_category(registry: dict[str, Any], category: str) -> int:
    return sum(1 for item in _registry_open_items(registry) if item.get("category") == category)


def _debt_penalty(registry: dict[str, Any], category: str, policy: dict[str, Any]) -> tuple[float, list[str], list[dict[str, Any]]]:
    weights = policy["severity_weights"]
    cap = policy["penalty_cap_per_category"]
    trace: list[str] = []
    breakdown: list[dict[str, Any]] = []
    total = 0.0
    for item in _registry_open_items(registry):
        if item.get("category") != category:
            continue
        severity = item.get("severity")
        mapping_status = "DIRECT_MATCH" if severity in weights else "FALLBACK_UNCLASSIFIED_DEFAULT"
        weight = weights.get(severity, weights["UNCLASSIFIED"])
        total += weight
        trace.append(f"-{weight} for OPEN {item['id']} (severity={severity})")
        breakdown.append({
            "debt_id": item["id"],
            "severity": severity,
            "mapping_status": mapping_status,
            "category_impact": category,
            "penalty_points": weight,
        })
    capped = min(total, cap)
    if capped < total:
        trace.append(f"penalty capped at {cap} (raw total was {total})")
    return capped, trace, breakdown


def _coverage_pct(coverage_baseline_path: Path) -> float | None:
    if not coverage_baseline_path.exists():
        return None
    try:
        data = json.loads(coverage_baseline_path.read_text(encoding="utf-8"))
        return float(data.get("combined_pct"))
    except Exception:
        return None


def _score_category(
    category_name: str,
    category_config: dict[str, Any],
    registry: dict[str, Any],
    methodology: dict[str, Any],
    cwd: Path,
    evidence: dict[str, Any],
    python_path: str,
    python_source: str,
) -> CategoryScore:
    gate_results: list[GateResult] = []
    for gate in category_config.get("gates", []):
        gate_results.append(_evaluate_gate(gate, python_path, python_source, cwd, evidence))

    if category_name == "Maintainability":
        open_p0_p1 = sum(
            1 for item in _registry_open_items(registry) if item.get("severity") in ("P0", "P1")
        )
        boolean_result = open_p0_p1 == 0
        gate_results = [GateResult(
            "no_open_p0_or_p1_anywhere",
            "PASS" if boolean_result else "FAIL",
            f"open P0/P1 items across whole registry = {open_p0_p1}",
            "REGISTRY_DERIVED",
        )]

    applicable = len(gate_results) or 1
    passed = sum(1 for g in gate_results if g.status == "PASS")
    unverified = sum(1 for g in gate_results if g.status in UNVERIFIED_STATUSES)
    gate_component_weight = category_config["gate_component_weight"] * 100
    gate_component = gate_component_weight * (passed / applicable)

    points_possible_per_gate = gate_component_weight / applicable
    gate_contributions = []
    missing_evidence: list[dict[str, Any]] = []
    for g in gate_results:
        points_awarded = points_possible_per_gate if g.status == "PASS" else 0.0
        gate_contributions.append({
            "name": g.name, "status": g.status, "local_or_remote": g.local_or_remote,
            "points_awarded": round(points_awarded, 4), "points_possible": round(points_possible_per_gate, 4),
        })
        if g.status in UNVERIFIED_STATUSES:
            missing_evidence.append({"name": g.name, "kind": "GATE", "reason": g.detail})

    rubric_trace: list[str] = []
    rubric_contributions: list[dict[str, Any]] = []
    rubric_component_weight = category_config["rubric_component_weight"] * 100
    rubric_component = 0.0

    for rubric in category_config.get("rubric", []):
        source = rubric["source"]
        if source == "registry_open_count_in_category":
            open_count = _open_count_in_category(registry, category_name)
            per_item = 2.0 if rubric_component_weight <= 20 else 4.0
            value = max(0.0, rubric_component_weight - per_item * open_count)
            rubric_trace.append(f"{rubric['name']}: {rubric_component_weight} - {per_item}*{open_count} open items = {value}")
            rubric_contributions.append({
                "name": rubric["name"], "source": source, "value_used": open_count,
                "points_awarded": round(value, 4), "points_possible": round(rubric_component_weight, 4),
            })
            rubric_component += value
        elif source == "coverage_baseline.combined_pct":
            coverage_baseline_path = cwd / "reports" / "quality" / "coverage_baseline.json"
            pct = _coverage_pct(coverage_baseline_path)
            if pct is None:
                rubric_trace.append(f"{rubric['name']}: UNKNOWN (coverage_baseline.json unreadable)")
                missing_evidence.append({"name": rubric["name"], "kind": "RUBRIC", "reason": "coverage_baseline.json unreadable"})
                value = 0.0
            else:
                value = rubric_component_weight * min(pct / 50.0, 1.0)
                rubric_trace.append(f"{rubric['name']}: {rubric_component_weight}*min({pct}/50,1) = {value:.2f}")
            rubric_contributions.append({
                "name": rubric["name"], "source": source, "value_used": pct,
                "points_awarded": round(value, 4), "points_possible": round(rubric_component_weight, 4),
            })
            rubric_component += value
        elif source == "registry.reconciliation_status":
            status = registry.get("reconciliation_status")
            has_note = bool(registry.get("reconciliation_note"))
            if status == "FULLY_RECONCILED":
                value = rubric_component_weight
            elif status == "PARTIALLY_RECONCILED" and has_note:
                value = rubric_component_weight * 0.5
            else:
                value = 0.0
            rubric_trace.append(f"{rubric['name']}: reconciliation_status={status}, documented={has_note} -> {value:.2f}")
            rubric_contributions.append({
                "name": rubric["name"], "source": source, "value_used": status,
                "points_awarded": round(value, 4), "points_possible": round(rubric_component_weight, 4),
            })
            rubric_component += value
        else:
            rubric_trace.append(f"{rubric['name']}: UNKNOWN source '{source}', contributes 0")
            missing_evidence.append({"name": rubric["name"], "kind": "RUBRIC", "reason": f"unknown source '{source}'"})
            rubric_contributions.append({
                "name": rubric["name"], "source": source, "value_used": None,
                "points_awarded": 0.0, "points_possible": round(rubric_component_weight, 4),
            })

    raw_before_penalty = round(gate_component + rubric_component, 2)
    penalty_policy = methodology["debt_penalty_policy"]
    debt_penalty, penalty_trace, debt_breakdown = _debt_penalty(registry, category_name, penalty_policy)
    debt_penalty_raw_total = round(sum(d["penalty_points"] for d in debt_breakdown), 2)
    debt_penalty_cap_applied = debt_penalty_raw_total > penalty_policy["penalty_cap_per_category"]
    rubric_trace.extend(penalty_trace)

    final_score = round(max(0.0, min(100.0, raw_before_penalty - debt_penalty)), 2)

    return CategoryScore(
        category=category_name,
        gate_component=round(gate_component, 2),
        rubric_component=round(rubric_component, 2),
        raw_before_penalty=raw_before_penalty,
        debt_penalty=debt_penalty,
        final_score=final_score,
        gate_results=gate_results,
        rubric_trace=rubric_trace,
        gate_contributions=gate_contributions,
        rubric_contributions=rubric_contributions,
        missing_evidence=missing_evidence,
        debt_penalty_breakdown=debt_breakdown,
        debt_penalty_raw_total=debt_penalty_raw_total,
        debt_penalty_cap_applied=debt_penalty_cap_applied,
        unverified_count=unverified,
    )


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _composite(category_scores: dict[str, CategoryScore], weights: dict[str, float]) -> tuple[float, list[dict[str, Any]]]:
    total = 0.0
    contributions = []
    for category, weight in weights.items():
        contribution = category_scores[category].final_score * weight
        total += contribution
        contributions.append({
            "category": category, "final_score": category_scores[category].final_score,
            "weight": weight, "contribution": round(contribution, 4),
        })
    return total, contributions


def compute_report(
    methodology: dict[str, Any],
    registry: dict[str, Any],
    cwd: Path,
    evidence: dict[str, Any],
    python_path: str = "",
    python_source: str = "not-resolved",
) -> dict[str, Any]:
    if not python_path:
        python_path = sys.executable
        python_source = "default-sys.executable"

    category_scores: dict[str, CategoryScore] = {}
    for category_name, category_config in methodology["categories"].items():
        category_scores[category_name] = _score_category(
            category_name, category_config, registry, methodology, cwd, evidence, python_path, python_source,
        )

    total_unverified = sum(cs.unverified_count for cs in category_scores.values())
    fully_verified = total_unverified == 0
    reconciled = registry.get("reconciliation_status") == "FULLY_RECONCILED"

    ceiling_cfg = methodology["evidence_completeness_ceiling"]
    ceiling_applies = (not fully_verified) or (not reconciled)
    ceiling_value = ceiling_cfg["value"] if ceiling_applies else 100

    live_weights = methodology["composites"]["LIVE_READINESS"]["weights"]
    transfer_weights = methodology["composites"]["TRANSFERABILITY"]["weights"]
    live_readiness_raw, live_contributions = _composite(category_scores, live_weights)
    transferability_raw, transfer_contributions = _composite(category_scores, transfer_weights)

    live_readiness_capped = min(live_readiness_raw, ceiling_value)
    transferability_capped = min(transferability_raw, ceiling_value)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "methodology_version": methodology["methodology_version"],
        "registry_version": registry.get("registry_version"),
        "interpreter": {"path": python_path, "source": python_source},
        "fully_verified": fully_verified,
        "unverified_evidence_count": total_unverified,
        "evidence_completeness_ceiling_applied": ceiling_applies,
        "evidence_completeness_ceiling_value": ceiling_value if ceiling_applies else None,
        "category_scores": {
            name: {
                "final_score": cs.final_score,
                "gate_component": cs.gate_component,
                "rubric_component": cs.rubric_component,
                "raw_before_penalty": cs.raw_before_penalty,
                "debt_penalty": cs.debt_penalty,
                "unverified_count": cs.unverified_count,
                "gate_contributions": cs.gate_contributions,
                "rubric_contributions": cs.rubric_contributions,
                "missing_evidence": cs.missing_evidence,
                "debt_penalty_breakdown": cs.debt_penalty_breakdown,
                "debt_penalty_raw_total": cs.debt_penalty_raw_total,
                "debt_penalty_cap_applied": cs.debt_penalty_cap_applied,
                "ceiling": {"applies": False},
                "gates": [{"name": g.name, "status": g.status, "detail": g.detail} for g in cs.gate_results],
                "rubric_trace": cs.rubric_trace,
            }
            for name, cs in category_scores.items()
        },
        "LIVE_READINESS": {
            "weights": live_weights,
            "contributions": live_contributions,
            "raw": round(live_readiness_raw, 4),
            "ceiling_applied_value": round(live_readiness_capped, 4),
            "rounding_rule": "ROUND_HALF_UP",
            "final": _round_half_up(live_readiness_capped),
        },
        "TRANSFERABILITY": {
            "weights": transfer_weights,
            "contributions": transfer_contributions,
            "raw": round(transferability_raw, 4),
            "ceiling_applied_value": round(transferability_capped, 4),
            "rounding_rule": "ROUND_HALF_UP",
            "final": _round_half_up(transferability_capped),
        },
        "legacy_snapshot": LEGACY_SNAPSHOT,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BYS360 Methodology V1 Score Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Methodology version: {report['methodology_version']}",
        f"Registry version: {report['registry_version']}",
        f"Interpreter: {report['interpreter']['path']} (source={report['interpreter']['source']})",
        f"Fully verified: {report['fully_verified']} (unverified_evidence_count={report['unverified_evidence_count']})",
        f"Evidence-completeness ceiling applied: {report['evidence_completeness_ceiling_applied']}"
        + (f" (value={report['evidence_completeness_ceiling_value']})" if report["evidence_completeness_ceiling_applied"] else ""),
        "",
        "## Category scores (Methodology V1)",
        "",
        "| Category | Final | Gate component | Rubric component | Debt penalty |",
        "|---|---|---|---|---|",
    ]
    for name, cs in report["category_scores"].items():
        lines.append(f"| {name} | {cs['final_score']} | {cs['gate_component']} | {cs['rubric_component']} | -{cs['debt_penalty']} |")

    lines += [
        "",
        f"## LIVE_READINESS = {report['LIVE_READINESS']['final']}",
        f"(raw {report['LIVE_READINESS']['raw']}, post-ceiling {report['LIVE_READINESS']['ceiling_applied_value']})",
        "",
        f"## TRANSFERABILITY = {report['TRANSFERABILITY']['final']}",
        f"(raw {report['TRANSFERABILITY']['raw']}, post-ceiling {report['TRANSFERABILITY']['ceiling_applied_value']})",
        "",
        "## Legacy snapshot (historical, NOT methodology V1, NOT a like-for-like trend)",
        "",
    ]
    for key, value in report["legacy_snapshot"].items():
        if key == "note":
            continue
        lines.append(f"- {key} = {value}")
    lines.append("")
    lines.append(report["legacy_snapshot"]["note"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 canonical score calculator (methodology v1.0.0)")
    parser.add_argument("--root", default=".")
    parser.add_argument("--methodology", default="config/quality/bys360_scoring_methodology_v1.json")
    parser.add_argument("--registry", default="config/quality/bys360_technical_debt_registry.json")
    parser.add_argument("--evidence", default=None, help="Optional JSON file supplying results for structurally-local-unverifiable gates")
    parser.add_argument("--python", default=None, help="Interpreter to use for gate commands (default: BYS360_QUALITY_PYTHON env var, else sys.executable)")
    parser.add_argument("--report-json", default=None)
    parser.add_argument("--report-md", default=None)
    parser.add_argument("--skip-gates", action="store_true", help="Score using only registry/debt data, treat all subprocess gates as UNKNOWN (fast, for tests)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    methodology = json.loads(Path(args.methodology).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8")) if args.evidence else {}

    python_path, python_source = resolve_python(args.python)

    if args.skip_gates:
        for category_config in methodology["categories"].values():
            for gate in category_config.get("gates", []):
                gate["pass_rule"] = "exit_code_0_or_supplied_evidence"
                gate.setdefault("evidence_note", "skipped via --skip-gates")

    report = compute_report(methodology, registry, root, evidence, python_path, python_source)

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.report_json:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.report_md:
        Path(args.report_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_md).write_text(render_markdown(report), encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
