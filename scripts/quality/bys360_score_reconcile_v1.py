"""BYS360 canonical score calculator (methodology v1.0.0).

Deterministically computes the 7 category scores and the two composite
scores (LIVE_READINESS, TRANSFERABILITY) from:
  - config/quality/bys360_scoring_methodology_v1.json (the formula/weights)
  - config/quality/bys360_technical_debt_registry.json (open-debt penalties)
  - live re-execution of each category's quality gates (ruff/mypy/coverage/
    secret-gate/ops-audit/quality9/handover-docs-contract)
  - config/quality/bys360_canonical_evidence.json (commit-bound remote
    evidence, when the currently-scored commit has any)

Portability: gate commands are declared in the methodology config as
structured {kind, module|script, args} entries, never a hardcoded
absolute path. The interpreter used to run them is resolved at runtime,
in order: --python CLI flag > BYS360_QUALITY_PYTHON environment variable
> sys.executable (the interpreter currently running this script). The
resolved interpreter and its source are reported in the output, and any
gate with a declared expected_version is version-checked before being
trusted -- a wrong-version tool result is a LOCAL diagnostic
(VERSION_MISMATCH), never silently scored as PASS.

Canonical evidence vs. local diagnostics: every gate's outcome is now
resolved through resolve_evidence(), which distinguishes CANONICAL PROJECT
EVIDENCE ("what is the verified state of this exact commit?") from LOCAL
ENVIRONMENT DIAGNOSTICS ("can this machine reproduce that state?"). A
commit-bound REMOTE_CI_VERIFIED entry in the evidence manifest always wins
for CANONICAL_PROJECT_SCORE, including when it disagrees with this
machine's own local execution -- a local VERSION_MISMATCH must never
invalidate valid matching remote evidence, and a matching remote FAIL must
never be overridden by a local PASS. When no matching-commit remote
evidence exists, a deterministically-verified local execution (correct
tool version, or no version pin) may still count as canonical
(LOCAL_VERIFIED) -- this is what makes an ordinary local run without any
manifest still fully functional. Evidence recorded for a *different*
commit SHA is never reused; it is rejected as stale. See
docs/governance/BYS360_SCORING_METHODOLOGY_V1.md's "Evidence precedence"
section for the full policy and worked examples.

Gates that are structurally impossible to verify in a local run (e.g. the
PostgreSQL migration-integrity gate, which needs a live PostgreSQL 15
service) are scored UNKNOWN unless a fresh result is supplied via
--evidence or matched via the canonical evidence manifest, per the
methodology's missing-evidence policy: UNKNOWN contributes 0 and is never
silently treated as PASS. VERSION_MISMATCH, LOCAL_TOOL_MISSING, and
LOCAL_EXECUTION_FAILURE are local-only diagnostic statuses -- none of them
are ever canonical evidence on their own, and none invalidate a valid
matching remote result.

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
import os
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

# Local-only diagnostic statuses: never canonical evidence on their own,
# never allowed to invalidate a valid matching-commit remote result.
LOCAL_DIAGNOSTIC_ONLY_STATUSES = {"VERSION_MISMATCH", "LOCAL_TOOL_MISSING", "LOCAL_EXECUTION_FAILURE", "UNKNOWN"}
# A local status eligible to stand in as CANONICAL evidence (tier 2) when no
# matching-commit remote evidence exists -- i.e. it was deterministically,
# correctly produced (right interpreter, right pinned tool version if any).
LOCAL_CANONICAL_ELIGIBLE_STATUSES = {"PASS", "FAIL"}
CANONICAL_UNVERIFIED_STATUSES = {"UNKNOWN"}
TRUSTED_EVIDENCE_TYPES = {"REMOTE_CI_VERIFIED", "LOCAL_VERIFIED", "REGISTRY_DERIVED", "STATIC_REPOSITORY_FACT", "UNKNOWN"}
VALID_MANIFEST_PROVENANCE = {"USER_SUPPLIED_REMOTE_PROOF", "AUTOMATED_INGESTION"}


@dataclass
class GateResult:
    name: str
    status: str  # PASS | FAIL | UNKNOWN | VERSION_MISMATCH | LOCAL_TOOL_MISSING | LOCAL_EXECUTION_FAILURE
    detail: str
    local_or_remote: str = "LOCAL"
    tool: str | None = None
    expected_version: str | None = None
    actual_version: str | None = None


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
    local_gate_component: float = 0.0
    local_final_score: float = 0.0
    local_environment_diagnostics: list[dict[str, Any]] = field(default_factory=list)


def resolve_scored_commit(cli_commit: str | None, cwd: Path) -> tuple[str, str]:
    """Resolve the commit SHA this run is scoring: --scored-commit CLI flag >
    `git rev-parse HEAD` in cwd > 'UNKNOWN_COMMIT' (git unavailable/not a repo).
    This SHA is what resolve_evidence() matches manifest entries against --
    getting it wrong silently accepts or rejects evidence for the wrong
    commit, so an explicit override always wins over auto-detection."""
    if cli_commit:
        return cli_commit, "explicit"
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, timeout=10, shell=False,
        )
        sha = proc.stdout.strip()
        if proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", sha):
            return sha, "git-rev-parse-HEAD"
    except OSError:
        pass
    return "UNKNOWN_COMMIT", "git-unavailable"


def resolve_python(cli_python: str | None) -> tuple[str, str]:
    """Resolve the interpreter used for gate commands: --python > env var > sys.executable."""
    if cli_python:
        if not Path(cli_python).exists():
            raise SystemExit(f"--python path does not exist: {cli_python}")
        return cli_python, "explicit"

    env_python = os.environ.get("BYS360_QUALITY_PYTHON")
    if env_python:
        if not Path(env_python).exists():
            raise SystemExit(f"BYS360_QUALITY_PYTHON path does not exist: {env_python}")
        return env_python, "env"
    return sys.executable, "default-sys.executable"


def _run_argv(argv: list[str], cwd: Path) -> tuple[int, str, str | None]:
    """Returns (returncode, combined_output, crash_kind). crash_kind is None for
    a normal execution (whatever its exit code), or 'LOCAL_TOOL_MISSING' /
    'LOCAL_EXECUTION_FAILURE' when the subprocess could not even complete --
    those must never be scored as an ordinary quality-gate FAIL."""
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=GATE_TIMEOUT_SECONDS,
            shell=False,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), None
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT", "LOCAL_EXECUTION_FAILURE"
    except OSError as exc:
        return -1, f"OSError: {exc}", "LOCAL_TOOL_MISSING"


def _build_argv(gate: dict[str, Any], python_path: str) -> list[str] | None:
    kind = gate.get("kind")
    if kind == "python_module":
        return [python_path, "-m", gate["module"], *gate.get("args", [])]
    if kind == "python_script":
        return [python_path, gate["script"], *gate.get("args", [])]
    return None


def _check_tool_version(python_path: str, module: str, expected: str, cwd: Path) -> tuple[bool, str, str | None]:
    returncode, output, crash_kind = _run_argv([python_path, "-m", module, "--version"], cwd)
    if crash_kind is not None:
        return False, f"could not launch {module} ({output})", crash_kind
    if returncode != 0:
        return False, f"could not determine {module} version (exit {returncode})", None
    first_line = output.strip().splitlines()[0] if output.strip() else ""
    match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
    actual = match.group(1) if match else first_line
    return actual == expected, actual, None


def _evaluate_gate(gate: dict[str, Any], python_path: str, python_source: str, cwd: Path, evidence: dict[str, Any]) -> GateResult:
    name = gate["name"]
    pass_rule = gate.get("pass_rule", "exit_code_0")
    local_or_remote = LOCAL_OR_REMOTE_BY_PASS_RULE.get(pass_rule, "LOCAL")
    tool = gate.get("module") or gate.get("script")
    expected_version = gate.get("expected_version")
    actual_version: str | None = None

    if pass_rule == "boolean":
        return GateResult(name, "UNKNOWN", "computed separately (registry-derived), not a subprocess gate", local_or_remote, tool)

    if pass_rule == "exit_code_0_or_supplied_evidence":
        supplied = evidence.get(name)
        if supplied is not None:
            status = "PASS" if supplied is True else "FAIL"
            return GateResult(name, status, f"supplied via --evidence (interpreter irrelevant): {supplied}", local_or_remote, tool)
        return GateResult(name, "UNKNOWN", gate.get("evidence_note", "not measurable locally; no --evidence supplied"), local_or_remote, tool)

    if expected_version and gate.get("kind") == "python_module":
        version_ok, actual_version, version_crash_kind = _check_tool_version(python_path, gate["module"], expected_version, cwd)
        if version_crash_kind is not None:
            return GateResult(
                name, version_crash_kind,
                f"could not check {gate['module']} version via {python_source} interpreter ({python_path}): {actual_version}",
                local_or_remote, tool, expected_version, actual_version,
            )
        if not version_ok:
            return GateResult(
                name, "VERSION_MISMATCH",
                f"expected {gate['module']}=={expected_version}, found '{actual_version}' via {python_source} interpreter ({python_path})",
                local_or_remote, tool, expected_version, actual_version,
            )

    argv = _build_argv(gate, python_path)
    if argv is None:
        return GateResult(name, "UNKNOWN", "gate has no runnable command definition (kind must be python_module or python_script)", local_or_remote, tool, expected_version, actual_version)

    returncode, output, crash_kind = _run_argv(argv, cwd)
    if crash_kind is not None:
        return GateResult(name, crash_kind, f"could not execute gate command ({output})", local_or_remote, tool, expected_version, actual_version)

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
                return GateResult(name, "UNKNOWN", f"could not parse JSON output (returncode={returncode})", local_or_remote, tool, expected_version, actual_version)
        ok = bool(payload.get("ok"))
        return GateResult(name, "PASS" if ok else "FAIL", f"ok={payload.get('ok')} finding_count={payload.get('finding_count')}", local_or_remote, tool, expected_version, actual_version)

    status = "PASS" if returncode == 0 else "FAIL"
    detail = "exit_code=0" if returncode == 0 else f"exit_code={returncode}"
    return GateResult(name, status, detail, local_or_remote, tool, expected_version, actual_version)


def resolve_evidence(
    metric_id: str,
    scored_commit: str,
    canonical_manifest: dict[str, Any],
    local_status: str,
    local_detail: str,
) -> dict[str, Any]:
    """Deterministically decides CANONICAL PROJECT evidence for one gate,
    separately from LOCAL ENVIRONMENT DIAGNOSTICS.

    Precedence (see docs/governance/BYS360_SCORING_METHODOLOGY_V1.md
    'Evidence precedence' section for the full policy):
      1. A commit-bound REMOTE_CI_VERIFIED manifest entry for the exact
         scored_commit wins unconditionally, including over a disagreeing
         local result -- a local VERSION_MISMATCH never invalidates valid
         matching remote evidence, and a matching remote FAIL is never
         overridden by a local PASS.
      2. Otherwise, a deterministically-verified local result (PASS/FAIL --
         i.e. produced with the correct interpreter and, if pinned, the
         correct tool version) may itself serve as canonical evidence.
      3. Otherwise: UNKNOWN. No unsupported points are ever awarded.
    Evidence recorded for a *different* commit SHA is never reused -- it is
    rejected as stale, whether or not a local fallback is available.
    Multiple manifest entries for the same gate+commit with disagreeing
    statuses is an EVIDENCE_CONFLICT: canonical becomes UNKNOWN, never an
    arbitrary pick between the two.
    """
    entries = [g for g in canonical_manifest.get("gates", []) if g.get("id") == metric_id]
    matching = [g for g in entries if g.get("commit_sha") == scored_commit]
    stale = [g for g in entries if g.get("commit_sha") != scored_commit]

    if matching:
        statuses = {g["status"] for g in matching}
        if len(statuses) > 1:
            return {
                "canonical_status": "UNKNOWN",
                "canonical_source": "EVIDENCE_CONFLICT",
                "local_status": local_status,
                "local_detail": local_detail,
                "precedence_reason": "EVIDENCE_CONFLICT",
                "provenance": None,
            }
        entry = matching[0]
        return {
            "canonical_status": entry["status"],
            "canonical_source": entry.get("evidence_type", "REMOTE_CI_VERIFIED"),
            "local_status": local_status,
            "local_detail": local_detail,
            "precedence_reason": "COMMIT_BOUND_REMOTE_VERIFIED",
            "provenance": entry.get("provenance"),
        }

    if local_status in LOCAL_CANONICAL_ELIGIBLE_STATUSES:
        return {
            "canonical_status": local_status,
            "canonical_source": "LOCAL_VERIFIED",
            "local_status": local_status,
            "local_detail": local_detail,
            "precedence_reason": (
                "STALE_COMMIT_EVIDENCE_REJECTED_LOCAL_FALLBACK" if stale else "LOCAL_VERIFIED_NO_MATCHING_REMOTE_EVIDENCE"
            ),
            "provenance": None,
        }

    return {
        "canonical_status": "UNKNOWN",
        "canonical_source": "NONE",
        "local_status": local_status,
        "local_detail": local_detail,
        "precedence_reason": (
            "STALE_COMMIT_EVIDENCE_REJECTED_NO_LOCAL_FALLBACK" if stale else "NO_VALID_EVIDENCE"
        ),
        "provenance": None,
    }


def validate_evidence_manifest(manifest: dict[str, Any]) -> list[str]:
    """Returns a list of validation problem strings; empty list = valid.

    Checks: schema shape, duplicate/malformed commit SHAs, invalid status
    or evidence_type values, REMOTE_CI_VERIFIED entries missing required
    provenance, invalid provenance values, and duplicate gate+commit
    entries that disagree on status (EVIDENCE_CONFLICT) -- the same
    conflict resolve_evidence() itself refuses to arbitrate at scoring
    time, caught earlier here so a broken manifest fails fast.
    """
    problems: list[str] = []
    by_key: dict[tuple[str, str], set[str]] = {}
    for idx, gate in enumerate(manifest.get("gates", [])):
        gid = gate.get("id")
        commit_sha = gate.get("commit_sha")
        status = gate.get("status")
        evidence_type = gate.get("evidence_type")
        provenance = gate.get("provenance")
        label = gid or f"<index {idx}, missing id>"
        if not gid:
            problems.append(f"gates[{idx}]: missing 'id'")
        if not commit_sha or not re.fullmatch(r"[0-9a-f]{40}", str(commit_sha)):
            problems.append(f"gates[{idx}] ({label}): missing or malformed commit_sha (must be a 40-hex-char SHA)")
        if status not in ("PASS", "FAIL"):
            problems.append(f"gates[{idx}] ({label}): invalid status '{status}' (manifest entries must be PASS or FAIL)")
        if evidence_type not in TRUSTED_EVIDENCE_TYPES:
            problems.append(f"gates[{idx}] ({label}): invalid evidence_type '{evidence_type}'")
        if evidence_type == "REMOTE_CI_VERIFIED" and not provenance:
            problems.append(f"gates[{idx}] ({label}): REMOTE_CI_VERIFIED evidence missing required 'provenance'")
        if provenance is not None and provenance not in VALID_MANIFEST_PROVENANCE:
            problems.append(f"gates[{idx}] ({label}): invalid provenance '{provenance}'")
        if gid and commit_sha and status in ("PASS", "FAIL"):
            by_key.setdefault((gid, commit_sha), set()).add(status)
    for (gid, commit_sha), statuses in by_key.items():
        if len(statuses) > 1:
            problems.append(f"EVIDENCE_CONFLICT: gate '{gid}' at commit {commit_sha} has disagreeing statuses {sorted(statuses)}")
    return problems


def resolve_evidence_file(cli_evidence_file: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve external commit-bound evidence: --evidence-file CLI flag >
    BYS360_CANONICAL_EVIDENCE_FILE environment variable > NO_EXTERNAL_EVIDENCE
    (pure local-fallback scoring). There is deliberately no third option that
    falls back to a committed 'live' evidence file in this repository --
    actual current-commit remote evidence is always supplied externally,
    precisely so that recording it never requires creating a new source
    commit (see docs/governance/BYS360_SCORING_METHODOLOGY_V1.md's
    'Self-attestation and the bootstrap problem' section: a version-controlled
    file describing commit X can never itself describe the commit that
    contains the file's own addition/edit, since editing it creates a new
    commit Y, making the file's evidence for X stale relative to HEAD=Y).

    An explicitly-supplied path (via either the flag or the env var) that
    does not exist, is not valid JSON, or fails validate_evidence_manifest(),
    fails the whole run fast -- it is never silently treated as though no
    evidence had been supplied. Silently falling back to local-only scoring
    on a bad path would hide a typo or a tampered file behind ordinary,
    unremarkable-looking local-fallback scoring, which is exactly the kind
    of silent-degradation this methodology's missing-evidence policy exists
    to forbid elsewhere.
    """
    path_str = cli_evidence_file
    source = "explicit"
    if not path_str:
        path_str = os.environ.get("BYS360_CANONICAL_EVIDENCE_FILE")
        source = "env" if path_str else "none"

    if not path_str:
        return {"gates": []}, {
            "path": None, "source": "NO_EXTERNAL_EVIDENCE", "loaded": False,
            "schema_version": None, "evidence_set_id": None,
            "commit_sha_or_commit_set": [], "validation_status": "NOT_APPLICABLE",
        }

    evidence_path = Path(path_str)
    if not evidence_path.exists():
        flag_name = "--evidence-file" if source == "explicit" else "BYS360_CANONICAL_EVIDENCE_FILE"
        raise SystemExit(f"EVIDENCE_FILE_NOT_FOUND: {flag_name} points at a path that does not exist: {evidence_path}")

    try:
        manifest = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"EVIDENCE_FILE_INVALID: {evidence_path} is not valid JSON: {exc}") from exc

    problems = validate_evidence_manifest(manifest)
    if problems:
        raise SystemExit(
            f"EVIDENCE_FILE_INVALID: {evidence_path} failed schema/provenance validation:\n  " + "\n  ".join(problems)
        )

    commit_shas = sorted({g["commit_sha"] for g in manifest.get("gates", [])})
    trace = {
        "path": str(evidence_path), "source": source, "loaded": True,
        "schema_version": manifest.get("schema_version"),
        "evidence_set_id": manifest.get("evidence_set_id"),
        "commit_sha_or_commit_set": commit_shas,
        "validation_status": "VALID",
    }
    return manifest, trace


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
    canonical_manifest: dict[str, Any],
    scored_commit: str,
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

    # Resolve CANONICAL evidence per gate, separately from each gate's raw
    # LOCAL execution result. Registry-derived gates are inherently
    # commit-bound already (their content IS part of the checked-out
    # commit) and bypass manifest resolution entirely.
    resolutions: list[dict[str, Any]] = []
    for g in gate_results:
        if g.local_or_remote == "REGISTRY_DERIVED":
            resolutions.append({
                "canonical_status": g.status, "canonical_source": "REGISTRY_DERIVED",
                "local_status": g.status, "local_detail": g.detail,
                "precedence_reason": "REGISTRY_DERIVED_INHERENTLY_COMMIT_BOUND", "provenance": None,
            })
        else:
            resolutions.append(resolve_evidence(g.name, scored_commit, canonical_manifest, g.status, g.detail))

    applicable = len(gate_results) or 1
    passed = sum(1 for r in resolutions if r["canonical_status"] == "PASS")
    unverified = sum(1 for r in resolutions if r["canonical_status"] in CANONICAL_UNVERIFIED_STATUSES)
    gate_component_weight = category_config["gate_component_weight"] * 100
    gate_component = gate_component_weight * (passed / applicable)

    local_passed = sum(1 for g in gate_results if g.status == "PASS")
    local_gate_component = gate_component_weight * (local_passed / applicable)

    points_possible_per_gate = gate_component_weight / applicable
    gate_contributions = []
    missing_evidence: list[dict[str, Any]] = []
    local_environment_diagnostics: list[dict[str, Any]] = []
    for g, r in zip(gate_results, resolutions, strict=True):
        points_awarded = points_possible_per_gate if r["canonical_status"] == "PASS" else 0.0
        gate_contributions.append({
            "name": g.name,
            "status": r["canonical_status"],  # CANONICAL status drives scoring; kept under 'status' for trace continuity
            "local_or_remote": g.local_or_remote,
            "points_awarded": round(points_awarded, 4), "points_possible": round(points_possible_per_gate, 4),
            "canonical_status": r["canonical_status"],
            "canonical_source": r["canonical_source"],
            "local_status": r["local_status"],
            "precedence_reason": r["precedence_reason"],
            "provenance": r["provenance"],
        })
        if r["canonical_status"] in CANONICAL_UNVERIFIED_STATUSES:
            missing_evidence.append({"name": g.name, "kind": "GATE", "reason": g.detail if r["local_status"] == r["canonical_status"] else f"canonical=UNKNOWN ({r['precedence_reason']}); local={g.detail}"})
        local_environment_diagnostics.append({
            "name": g.name, "tool": g.tool, "expected_version": g.expected_version,
            "actual_version": g.actual_version, "local_status": g.status,
            "interpreter": python_path, "notes": g.detail,
        })

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
    local_raw_before_penalty = round(local_gate_component + rubric_component, 2)
    penalty_policy = methodology["debt_penalty_policy"]
    debt_penalty, penalty_trace, debt_breakdown = _debt_penalty(registry, category_name, penalty_policy)
    debt_penalty_raw_total = round(sum(d["penalty_points"] for d in debt_breakdown), 2)
    debt_penalty_cap_applied = debt_penalty_raw_total > penalty_policy["penalty_cap_per_category"]
    rubric_trace.extend(penalty_trace)

    final_score = round(max(0.0, min(100.0, raw_before_penalty - debt_penalty)), 2)
    local_final_score = round(max(0.0, min(100.0, local_raw_before_penalty - debt_penalty)), 2)

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
        local_gate_component=round(local_gate_component, 2),
        local_final_score=local_final_score,
        local_environment_diagnostics=local_environment_diagnostics,
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


def _local_composite(category_scores: dict[str, CategoryScore], weights: dict[str, float]) -> float:
    return sum(category_scores[category].local_final_score * weight for category, weight in weights.items())


DEFAULT_EVIDENCE_INPUT_TRACE: dict[str, Any] = {
    "path": None, "source": "NO_EXTERNAL_EVIDENCE", "loaded": False,
    "schema_version": None, "evidence_set_id": None,
    "commit_sha_or_commit_set": [], "validation_status": "NOT_APPLICABLE",
}


def compute_report(
    methodology: dict[str, Any],
    registry: dict[str, Any],
    cwd: Path,
    evidence: dict[str, Any],
    python_path: str = "",
    python_source: str = "not-resolved",
    canonical_manifest: dict[str, Any] | None = None,
    scored_commit: str = "",
    evidence_input_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not python_path:
        python_path = sys.executable
        python_source = "default-sys.executable"
    if canonical_manifest is None:
        canonical_manifest = {"gates": []}
    if not scored_commit:
        scored_commit = "UNKNOWN_COMMIT"
    if evidence_input_trace is None:
        evidence_input_trace = dict(DEFAULT_EVIDENCE_INPUT_TRACE)

    category_scores: dict[str, CategoryScore] = {}
    for category_name, category_config in methodology["categories"].items():
        category_scores[category_name] = _score_category(
            category_name, category_config, registry, methodology, cwd, evidence, python_path, python_source,
            canonical_manifest, scored_commit,
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

    local_live_readiness_raw = _local_composite(category_scores, live_weights)
    local_transferability_raw = _local_composite(category_scores, transfer_weights)

    canonical_project_evidence = {
        name: [
            {
                "gate": gc["name"], "canonical_status": gc["canonical_status"],
                "canonical_source": gc["canonical_source"], "commit_sha": scored_commit,
                "provenance": gc["provenance"], "precedence_reason": gc["precedence_reason"],
            }
            for gc in cs.gate_contributions
        ]
        for name, cs in category_scores.items()
    }
    local_environment_diagnostics = {
        name: cs.local_environment_diagnostics for name, cs in category_scores.items()
    }

    all_gate_contributions = [gc for cs in category_scores.values() for gc in cs.gate_contributions]
    composition_counts = {
        "remote_verified_gates": sum(1 for gc in all_gate_contributions if gc["canonical_source"] == "REMOTE_CI_VERIFIED"),
        "local_verified_gates": sum(1 for gc in all_gate_contributions if gc["canonical_source"] == "LOCAL_VERIFIED"),
        "registry_derived_gates": sum(1 for gc in all_gate_contributions if gc["canonical_source"] == "REGISTRY_DERIVED"),
        "unknown_gates": sum(1 for gc in all_gate_contributions if gc["canonical_source"] == "NONE"),
        "evidence_conflict_gates": sum(1 for gc in all_gate_contributions if gc["canonical_source"] == "EVIDENCE_CONFLICT"),
    }
    if composition_counts["unknown_gates"] or composition_counts["evidence_conflict_gates"]:
        completeness = "PARTIAL"
    elif composition_counts["local_verified_gates"]:
        completeness = "LOCAL_FALLBACK_USED"
    else:
        completeness = "FULL"
    canonical_evidence_composition = {**composition_counts, "completeness": completeness}

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "methodology_version": methodology["methodology_version"],
        "registry_version": registry.get("registry_version"),
        "interpreter": {"path": python_path, "source": python_source},
        "scored_commit": scored_commit,
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
                "local_gate_component": cs.local_gate_component,
                "local_final_score_NON_CANONICAL": cs.local_final_score,
            }
            for name, cs in category_scores.items()
        },
        "EVIDENCE_INPUT": {
            "description": "Exactly which external evidence file (if any) produced CANONICAL_PROJECT_EVIDENCE below. 'source': NO_EXTERNAL_EVIDENCE means no --evidence-file/BYS360_CANONICAL_EVIDENCE_FILE was supplied -- every gate falls through to local-verified/UNKNOWN, identical to running this calculator with no evidence mechanism at all.",
            **evidence_input_trace,
        },
        "CANONICAL_PROJECT_EVIDENCE": {
            "description": "The verified state of scored_commit, used to compute CANONICAL_PROJECT_SCORE below. Never affected by this machine's own tool versions when valid commit-bound remote evidence exists.",
            "by_category": canonical_project_evidence,
        },
        "CANONICAL_EVIDENCE_COMPOSITION": {
            "description": "Descriptive counts only -- never a new score. completeness=FULL means every scored gate resolved via REMOTE_CI_VERIFIED; LOCAL_FALLBACK_USED means at least one gate fell back to a deterministically-correct local result; PARTIAL means at least one gate is UNKNOWN or in EVIDENCE_CONFLICT. Never present this as 'fully remote verified' unless completeness == FULL.",
            **canonical_evidence_composition,
        },
        "LOCAL_ENVIRONMENT_DIAGNOSTICS": {
            "description": "Whether THIS machine's toolchain can reproduce the canonical quality environment. Informative only -- never used to invalidate valid canonical evidence, and never itself the official project score.",
            "by_category": local_environment_diagnostics,
        },
        "LIVE_READINESS": {
            "label": "CANONICAL_PROJECT_SCORE",
            "weights": live_weights,
            "contributions": live_contributions,
            "raw": round(live_readiness_raw, 4),
            "ceiling_applied_value": round(live_readiness_capped, 4),
            "rounding_rule": "ROUND_HALF_UP",
            "final": _round_half_up(live_readiness_capped),
        },
        "TRANSFERABILITY": {
            "label": "CANONICAL_PROJECT_SCORE",
            "weights": transfer_weights,
            "contributions": transfer_contributions,
            "raw": round(transferability_raw, 4),
            "ceiling_applied_value": round(transferability_capped, 4),
            "rounding_rule": "ROUND_HALF_UP",
            "final": _round_half_up(transferability_capped),
        },
        "LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL": {
            "description": "What LIVE_READINESS/TRANSFERABILITY would be using ONLY this machine's raw local gate results, ignoring the canonical evidence manifest entirely. NOT the official project score -- diagnostic only, to show a developer what fixing their local toolchain would change.",
            "LIVE_READINESS_local": _round_half_up(min(local_live_readiness_raw, ceiling_value)),
            "TRANSFERABILITY_local": _round_half_up(min(local_transferability_raw, ceiling_value)),
        },
        "legacy_snapshot": LEGACY_SNAPSHOT,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BYS360 Methodology V1 Score Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Scored commit: {report.get('scored_commit', 'UNKNOWN_COMMIT')} (source={report.get('scored_commit_source', 'n/a')})",
        f"Methodology version: {report['methodology_version']}",
        f"Registry version: {report['registry_version']}",
        f"Interpreter: {report['interpreter']['path']} (source={report['interpreter']['source']})",
        f"Fully verified (CANONICAL): {report['fully_verified']} (unverified_evidence_count={report['unverified_evidence_count']})",
        f"Evidence-completeness ceiling applied: {report['evidence_completeness_ceiling_applied']}"
        + (f" (value={report['evidence_completeness_ceiling_value']})" if report["evidence_completeness_ceiling_applied"] else ""),
        "",
        "## Category scores -- CANONICAL_PROJECT_SCORE (Methodology V1)",
        "",
        "| Category | Final (canonical) | Gate component | Rubric component | Debt penalty | Local (NON-CANONICAL) |",
        "|---|---|---|---|---|---|",
    ]
    for name, cs in report["category_scores"].items():
        lines.append(
            f"| {name} | {cs['final_score']} | {cs['gate_component']} | {cs['rubric_component']} | "
            f"-{cs['debt_penalty']} | {cs['local_final_score_NON_CANONICAL']} |"
        )

    lines += [
        "",
        "## Local environment diagnostics (NON-CANONICAL -- this machine only)",
        "",
        "| Category | Gate | Tool | Expected version | Actual version | Local status |",
        "|---|---|---|---|---|---|",
    ]
    for name, gates in report["LOCAL_ENVIRONMENT_DIAGNOSTICS"]["by_category"].items():
        for g in gates:
            lines.append(f"| {name} | {g['name']} | {g['tool'] or '-'} | {g['expected_version'] or '-'} | {g['actual_version'] or '-'} | {g['local_status']} |")

    lines += [
        "",
        f"## LIVE_READINESS (CANONICAL_PROJECT_SCORE) = {report['LIVE_READINESS']['final']}",
        f"(raw {report['LIVE_READINESS']['raw']}, post-ceiling {report['LIVE_READINESS']['ceiling_applied_value']})",
        "",
        f"## TRANSFERABILITY (CANONICAL_PROJECT_SCORE) = {report['TRANSFERABILITY']['final']}",
        f"(raw {report['TRANSFERABILITY']['raw']}, post-ceiling {report['TRANSFERABILITY']['ceiling_applied_value']})",
        "",
        "## Local environment score (NON-CANONICAL, diagnostic only)",
        f"LIVE_READINESS_local = {report['LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL']['LIVE_READINESS_local']}, "
        f"TRANSFERABILITY_local = {report['LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL']['TRANSFERABILITY_local']}",
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
    parser.add_argument("--evidence-file", default=None, help="External commit-bound canonical evidence file (default: BYS360_CANONICAL_EVIDENCE_FILE env var, else NO_EXTERNAL_EVIDENCE / local-fallback-only scoring). Never defaults to a committed file -- see docs/governance/BYS360_SCORING_METHODOLOGY_V1.md 'Self-attestation and the bootstrap problem'.")
    parser.add_argument("--scored-commit", default=None, help="Commit SHA being scored (default: git rev-parse HEAD in --root)")
    parser.add_argument("--python", default=None, help="Interpreter to use for gate commands (default: BYS360_QUALITY_PYTHON env var, else sys.executable)")
    parser.add_argument("--report-json", default=None)
    parser.add_argument("--report-md", default=None)
    parser.add_argument("--skip-gates", action="store_true", help="Score using only registry/debt data, treat all subprocess gates as UNKNOWN (fast, for tests)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    methodology = json.loads(Path(args.methodology).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8")) if args.evidence else {}

    canonical_manifest, evidence_input_trace = resolve_evidence_file(args.evidence_file)

    scored_commit, scored_commit_source = resolve_scored_commit(args.scored_commit, root)

    python_path, python_source = resolve_python(args.python)

    if args.skip_gates:
        for category_config in methodology["categories"].values():
            for gate in category_config.get("gates", []):
                gate["pass_rule"] = "exit_code_0_or_supplied_evidence"
                gate.setdefault("evidence_note", "skipped via --skip-gates")

    report = compute_report(
        methodology, registry, root, evidence, python_path, python_source,
        canonical_manifest, scored_commit, evidence_input_trace,
    )
    report["scored_commit_source"] = scored_commit_source

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
