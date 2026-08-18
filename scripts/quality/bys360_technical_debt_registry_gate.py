"""BYS360 canonical technical debt registry validator.

Parses config/quality/bys360_technical_debt_registry.json, validates its
schema, and computes registry-derived debt counts. Never invents, infers,
or silently reconciles the separate historical legacy_ledger counts --
those are surfaced unmodified, clearly labeled as unmapped, alongside the
registry-derived counts.

Accounting invariant (registry_version >= 1.1.0): the legacy ledger
represents CURRENT OPEN debt only. It must never be reconciled against a
registry count that includes CLOSED items -- closing an item (or
discovering and immediately closing a brand-new, unrelated item) must
never be able to mechanically shrink an "unexplained legacy debt" number,
because that would let unrelated hygiene work silently masquerade as
progress on a specific historical backlog it was never shown to be part
of. See MAPPED_LEGACY_OPEN_COUNT / UNMAPPED_LEGACY_OPEN_COUNT below.

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
VALID_LEGACY_MAPPING_STATUSES = {"CONFIRMED", "UNCONFIRMED", "NOT_LEGACY_MEMBER"}
ACTIVE_STATUSES = {"OPEN", "BLOCKED", "IN_PROGRESS", "DEFERRED", "ACCEPTED_RISK"}
CLOSED_LIKE_STATUSES = {"CLOSED"}
REQUIRED_ITEM_FIELDS = (
    "id", "title", "status", "severity", "category", "component", "description",
    "evidence", "introduced_commit", "closure_commit", "remote_verified",
    "created_at", "updated_at", "closure_reason", "legacy_mapping", "notes",
)


@dataclass
class RegistryFinding:
    code: str
    item_id: str | None
    detail: str


@dataclass
class RegistryValidationResult:
    ok: bool
    findings: list[RegistryFinding] = field(default_factory=list)
    registry_counts: dict[str, Any] = field(default_factory=dict)
    legacy_counts: dict[str, Any] = field(default_factory=dict)


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

    legacy_mapping = item.get("legacy_mapping")
    if not isinstance(legacy_mapping, dict) or "status" not in legacy_mapping:
        findings.append(RegistryFinding(
            "invalid_legacy_mapping", item_id,
            "legacy_mapping must be an object with a 'status' field",
        ))
    elif legacy_mapping.get("status") not in VALID_LEGACY_MAPPING_STATUSES:
        findings.append(RegistryFinding(
            "invalid_legacy_mapping_status", item_id,
            f"legacy_mapping.status '{legacy_mapping.get('status')}' not in {sorted(VALID_LEGACY_MAPPING_STATUSES)}",
        ))

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

    registry_total = len(items)
    registry_closed_count = sum(1 for item in items if item.get("status") == "CLOSED")
    active_items = [item for item in items if item.get("status") in ACTIVE_STATUSES]
    registry_active_count = len(active_items)

    active_severity_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "UNCLASSIFIED": 0}
    for item in active_items:
        severity = item.get("severity")
        if severity in active_severity_counts:
            active_severity_counts[severity] += 1

    mapped_legacy_open_count = sum(
        1 for item in active_items
        if isinstance(item.get("legacy_mapping"), dict) and item["legacy_mapping"].get("status") == "CONFIRMED"
    )

    legacy_ledger = registry.get("legacy_ledger", {})
    legacy_total = legacy_ledger.get("TOTAL")

    unmapped_legacy_open_count = None
    if isinstance(legacy_total, int):
        unmapped_legacy_open_count = legacy_total - mapped_legacy_open_count
        if mapped_legacy_open_count > legacy_total:
            findings.append(RegistryFinding(
                "mapped_exceeds_legacy_total", None,
                f"MAPPED_LEGACY_OPEN_COUNT ({mapped_legacy_open_count}) exceeds legacy_ledger.TOTAL ({legacy_total}) -- "
                "more items claim confirmed legacy membership than the legacy ledger admits exist",
            ))

    registry_open_unlinked_count = registry_active_count - mapped_legacy_open_count

    registry_counts = {
        "REGISTRY_TOTAL": registry_total,
        "REGISTRY_CLOSED_COUNT": registry_closed_count,
        "REGISTRY_ACTIVE_COUNT": registry_active_count,
        "REGISTRY_SEVERITY_COUNTS_ACTIVE": active_severity_counts,
        "MAPPED_LEGACY_OPEN_COUNT": mapped_legacy_open_count,
        "REGISTRY_OPEN_UNLINKED_COUNT": registry_open_unlinked_count,
    }

    legacy_counts = {
        "LEGACY_OPEN_TOTAL": legacy_total,
        "LEGACY_P0": legacy_ledger.get("P0"),
        "LEGACY_P1": legacy_ledger.get("P1"),
        "LEGACY_P2": legacy_ledger.get("P2"),
        "LEGACY_P3": legacy_ledger.get("P3"),
        "MAPPED_LEGACY_OPEN_COUNT": mapped_legacy_open_count,
        "UNMAPPED_LEGACY_OPEN_COUNT": unmapped_legacy_open_count,
        "status": legacy_ledger.get("status"),
    }

    if isinstance(legacy_total, int) and unmapped_legacy_open_count is not None:
        invariant_holds = legacy_total == mapped_legacy_open_count + unmapped_legacy_open_count
        if not invariant_holds:
            findings.append(RegistryFinding(
                "legacy_invariant_violated", None,
                "LEGACY_OPEN_TOTAL must equal MAPPED_LEGACY_OPEN_COUNT + UNMAPPED_LEGACY_OPEN_COUNT",
            ))
        if unmapped_legacy_open_count < 0:
            findings.append(RegistryFinding(
                "negative_unmapped_legacy_open_count", None,
                f"UNMAPPED_LEGACY_OPEN_COUNT computed as {unmapped_legacy_open_count}, which is impossible",
            ))

    reconciliation_status = registry.get("reconciliation_status")
    if reconciliation_status not in {"FULLY_RECONCILED", "PARTIALLY_RECONCILED"}:
        findings.append(RegistryFinding(
            "invalid_reconciliation_status", None,
            f"reconciliation_status '{reconciliation_status}' must be FULLY_RECONCILED or PARTIALLY_RECONCILED",
        ))
    if reconciliation_status == "FULLY_RECONCILED" and unmapped_legacy_open_count not in (0, None):
        findings.append(RegistryFinding(
            "reconciliation_status_inconsistent", None,
            "reconciliation_status=FULLY_RECONCILED requires UNMAPPED_LEGACY_OPEN_COUNT == 0 "
            "(every legacy-38 slot confirmed-mapped to an active registry item)",
        ))

    ok = not findings
    return RegistryValidationResult(
        ok=ok,
        findings=findings,
        registry_counts=registry_counts,
        legacy_counts=legacy_counts,
    )


def render_markdown(registry: dict[str, Any], result: RegistryValidationResult) -> str:
    rc = result.registry_counts
    lc = result.legacy_counts
    lines = [
        "# BYS360 Technical Debt Registry Summary",
        "",
        f"Registry version: {registry.get('registry_version', 'unknown')}",
        f"Reconciliation status: {registry.get('reconciliation_status', 'unknown')}",
        "",
        "## Canonical registry (computed from items[], authoritative for CURRENT state)",
        "",
        f"- REGISTRY_TOTAL = {rc['REGISTRY_TOTAL']}",
        f"- REGISTRY_CLOSED_COUNT = {rc['REGISTRY_CLOSED_COUNT']}",
        f"- REGISTRY_ACTIVE_COUNT = {rc['REGISTRY_ACTIVE_COUNT']}",
        f"- REGISTRY_SEVERITY_COUNTS_ACTIVE (P0/P1/P2/P3/UNCLASSIFIED) = "
        f"{rc['REGISTRY_SEVERITY_COUNTS_ACTIVE']['P0']}/{rc['REGISTRY_SEVERITY_COUNTS_ACTIVE']['P1']}/"
        f"{rc['REGISTRY_SEVERITY_COUNTS_ACTIVE']['P2']}/{rc['REGISTRY_SEVERITY_COUNTS_ACTIVE']['P3']}/"
        f"{rc['REGISTRY_SEVERITY_COUNTS_ACTIVE']['UNCLASSIFIED']}",
        f"- MAPPED_LEGACY_OPEN_COUNT = {rc['MAPPED_LEGACY_OPEN_COUNT']} (active items with legacy_mapping.status=CONFIRMED)",
        f"- REGISTRY_OPEN_UNLINKED_COUNT = {rc['REGISTRY_OPEN_UNLINKED_COUNT']} (active items NOT confirmed as legacy members -- newly-discovered debt)",
        "",
        "## Legacy working ledger (preserved historical reference, NOT registry-derived)",
        "",
        f"- LEGACY_OPEN_TOTAL = {lc['LEGACY_OPEN_TOTAL']}",
        f"- LEGACY P0/P1/P2/P3 = {lc['LEGACY_P0']}/{lc['LEGACY_P1']}/{lc['LEGACY_P2']}/{lc['LEGACY_P3']}",
        f"- MAPPED_LEGACY_OPEN_COUNT = {lc['MAPPED_LEGACY_OPEN_COUNT']}",
        f"- UNMAPPED_LEGACY_OPEN_COUNT = {lc['UNMAPPED_LEGACY_OPEN_COUNT']} (LEGACY_OPEN_TOTAL minus MAPPED; CLOSED registry items never participate in this figure)",
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
        "registry_counts": result.registry_counts,
        "legacy_counts": result.legacy_counts,
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
