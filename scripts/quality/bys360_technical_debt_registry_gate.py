"""BYS360 canonical technical debt registry validator.

Parses config/quality/bys360_technical_debt_registry.json, validates its
schema, and computes registry-derived debt counts. Never invents, infers,
or silently reconciles the separate historical legacy_ledger counts --
those are surfaced unmodified, clearly labeled as unmapped, alongside the
registry-derived counts.

Read-only: this script never edits the registry file.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VALID_STATUSES = {"OPEN", "BLOCKED", "IN_PROGRESS", "CLOSED", "ACCEPTED_RISK", "DEFERRED"}
VALID_SEVERITIES = {"P0", "P1", "P2", "P3", "UNCLASSIFIED"}
REQUIRED_ITEM_FIELDS = (
    "id", "title", "status", "severity", "category", "component", "description",
    "evidence", "introduced_commit", "closure_commit", "remote_verified",
    "created_at", "updated_at", "closure_reason", "notes",
)
CLOSED_LIKE_STATUSES = {"CLOSED"}


@dataclass
class RegistryFinding:
    code: str
    item_id: str | None
    detail: str


@dataclass
class RegistryValidationResult:
    ok: bool
    findings: list[RegistryFinding] = field(default_factory=list)
    registry_derived_counts: dict[str, Any] = field(default_factory=dict)
    legacy_unmapped_ledger_counts: dict[str, Any] = field(default_factory=dict)


def _load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_item(item: dict[str, Any], seen_ids: set[str]) -> list[RegistryFinding]:
    findings: list[RegistryFinding] = []
    item_id = item.get("id")

    for required_field in REQUIRED_ITEM_FIELDS:
        if required_field not in item:
            findings.append(RegistryFinding("missing_field", item_id, f"missing required field '{required_field}'"))

    if not item_id or not isinstance(item_id, str):
        findings.append(RegistryFinding("invalid_id", item_id, "id must be a non-empty string"))
    elif item_id in seen_ids:
        findings.append(RegistryFinding("duplicate_id", item_id, f"duplicate id '{item_id}'"))
    else:
        seen_ids.add(item_id)

    status = item.get("status")
    if status not in VALID_STATUSES:
        findings.append(RegistryFinding("invalid_status", item_id, f"status '{status}' not in {sorted(VALID_STATUSES)}"))

    severity = item.get("severity")
    if severity not in VALID_SEVERITIES:
        findings.append(RegistryFinding("invalid_severity", item_id, f"severity '{severity}' not in {sorted(VALID_SEVERITIES)}"))

    if status in CLOSED_LIKE_STATUSES:
        has_evidence = bool(item.get("closure_commit")) or bool(item.get("closure_reason"))
        has_evidence_list = bool(item.get("evidence"))
        if not has_evidence or not has_evidence_list:
            findings.append(RegistryFinding(
                "closed_without_evidence", item_id,
                "status=CLOSED requires a non-empty closure_commit or closure_reason, AND a non-empty evidence list",
            ))

    if status == "OPEN" and (item.get("closure_commit") or item.get("closure_reason")):
        findings.append(RegistryFinding(
            "open_falsely_claims_closure", item_id,
            "status=OPEN but closure_commit/closure_reason is set -- an item cannot be both open and closed",
        ))

    if not item.get("evidence"):
        findings.append(RegistryFinding("missing_evidence", item_id, "evidence list must be non-empty for every item"))

    return findings


def validate_registry(registry: dict[str, Any]) -> RegistryValidationResult:
    findings: list[RegistryFinding] = []
    items = registry.get("items", [])

    if not isinstance(items, list):
        findings.append(RegistryFinding("invalid_items", None, "items must be a list"))
        items = []

    seen_ids: set[str] = set()
    for item in items:
        findings.extend(_validate_item(item, seen_ids))

    open_by_severity = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "UNCLASSIFIED": 0}
    closed_count = 0
    blocked_count = 0
    for item in items:
        status = item.get("status")
        severity = item.get("severity")
        if status == "OPEN" and severity in open_by_severity:
            open_by_severity[severity] += 1
        elif status == "CLOSED":
            closed_count += 1
        elif status == "BLOCKED":
            blocked_count += 1

    total_open = sum(v for k, v in open_by_severity.items() if k != "UNCLASSIFIED") + open_by_severity["UNCLASSIFIED"]

    registry_derived_counts = {
        "P0": open_by_severity["P0"],
        "P1": open_by_severity["P1"],
        "P2": open_by_severity["P2"],
        "P3": open_by_severity["P3"],
        "UNCLASSIFIED": open_by_severity["UNCLASSIFIED"],
        "TOTAL_OPEN": total_open,
        "CLOSED_COUNT": closed_count,
        "BLOCKED_COUNT": blocked_count,
        "TOTAL_ITEMS": len(items),
    }

    legacy_ledger = registry.get("legacy_ledger", {})
    legacy_unmapped_ledger_counts = {
        "P0": legacy_ledger.get("P0"),
        "P1": legacy_ledger.get("P1"),
        "P2": legacy_ledger.get("P2"),
        "P3": legacy_ledger.get("P3"),
        "TOTAL": legacy_ledger.get("TOTAL"),
        "status": legacy_ledger.get("status"),
        "reconciliation_gap": None,
    }
    if isinstance(legacy_ledger.get("TOTAL"), int):
        legacy_unmapped_ledger_counts["reconciliation_gap"] = legacy_ledger["TOTAL"] - registry_derived_counts["TOTAL_ITEMS"]

    reconciliation_status = registry.get("reconciliation_status")
    if reconciliation_status not in {"FULLY_RECONCILED", "PARTIALLY_RECONCILED"}:
        findings.append(RegistryFinding(
            "invalid_reconciliation_status", None,
            f"reconciliation_status '{reconciliation_status}' must be FULLY_RECONCILED or PARTIALLY_RECONCILED",
        ))
    if reconciliation_status == "FULLY_RECONCILED" and legacy_unmapped_ledger_counts["reconciliation_gap"] not in (0, None):
        findings.append(RegistryFinding(
            "reconciliation_status_inconsistent", None,
            "reconciliation_status=FULLY_RECONCILED but legacy_ledger.TOTAL does not match registry item count",
        ))

    ok = not findings
    return RegistryValidationResult(
        ok=ok,
        findings=findings,
        registry_derived_counts=registry_derived_counts,
        legacy_unmapped_ledger_counts=legacy_unmapped_ledger_counts,
    )


def render_markdown(registry: dict[str, Any], result: RegistryValidationResult) -> str:
    lines = [
        "# BYS360 Technical Debt Registry Summary",
        "",
        f"Registry version: {registry.get('registry_version', 'unknown')}",
        f"Reconciliation status: {registry.get('reconciliation_status', 'unknown')}",
        "",
        "## Registry-derived counts (computed from items[], authoritative for CURRENT state)",
        "",
        f"- P0 = {result.registry_derived_counts['P0']}",
        f"- P1 = {result.registry_derived_counts['P1']}",
        f"- P2 = {result.registry_derived_counts['P2']}",
        f"- P3 = {result.registry_derived_counts['P3']}",
        f"- UNCLASSIFIED = {result.registry_derived_counts['UNCLASSIFIED']}",
        f"- TOTAL_OPEN = {result.registry_derived_counts['TOTAL_OPEN']}",
        f"- CLOSED_COUNT = {result.registry_derived_counts['CLOSED_COUNT']}",
        f"- BLOCKED_COUNT = {result.registry_derived_counts['BLOCKED_COUNT']}",
        "",
        "## Legacy unmapped ledger (preserved historical reference, NOT registry-derived)",
        "",
        f"- P0 = {result.legacy_unmapped_ledger_counts['P0']}",
        f"- P1 = {result.legacy_unmapped_ledger_counts['P1']}",
        f"- P2 = {result.legacy_unmapped_ledger_counts['P2']}",
        f"- P3 = {result.legacy_unmapped_ledger_counts['P3']}",
        f"- TOTAL = {result.legacy_unmapped_ledger_counts['TOTAL']}",
        f"- reconciliation_gap (legacy TOTAL minus registry item count) = {result.legacy_unmapped_ledger_counts['reconciliation_gap']}",
        "",
        "## Validation",
        "",
        f"Status: {'PASS' if result.ok else 'FAIL'}",
    ]
    if result.findings:
        lines.append("")
        lines.append("### Findings")
        for finding in result.findings:
            lines.append(f"- `{finding.code}` ({finding.item_id or 'registry'}): {finding.detail}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 canonical technical debt registry validator")
    parser.add_argument("--registry", default="config/quality/bys360_technical_debt_registry.json")
    parser.add_argument("--report-json", default=None)
    parser.add_argument("--report-md", default=None)
    args = parser.parse_args()

    registry_path = Path(args.registry)
    if not registry_path.exists():
        print(json.dumps({"ok": False, "error": f"registry file not found: {registry_path}"}))
        return 2

    registry = _load_registry(registry_path)
    result = validate_registry(registry)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": result.ok,
        "registry_version": registry.get("registry_version"),
        "reconciliation_status": registry.get("reconciliation_status"),
        "registry_derived_counts": result.registry_derived_counts,
        "legacy_unmapped_ledger_counts": result.legacy_unmapped_ledger_counts,
        "findings": [
            {"code": f.code, "item_id": f.item_id, "detail": f.detail}
            for f in result.findings
        ],
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.report_json:
        Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_json).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.report_md:
        Path(args.report_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report_md).write_text(render_markdown(registry, result), encoding="utf-8")

    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
