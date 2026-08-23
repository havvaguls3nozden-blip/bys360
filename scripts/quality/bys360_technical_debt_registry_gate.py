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
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VALID_STATUSES = {"OPEN", "BLOCKED", "IN_PROGRESS", "CLOSED", "ACCEPTED_RISK", "DEFERRED"}
VALID_SEVERITIES = {"P0", "P1", "P2", "P3", "UNCLASSIFIED"}
VALID_LEGACY_MAPPING_STATUSES = {"CONFIRMED", "UNCONFIRMED", "NOT_LEGACY_MEMBER"}
VALID_RECONCILIATION_STATUSES = {"FULLY_RECONCILED", "PARTIALLY_RECONCILED", "HISTORICAL_UNRECONSTRUCTABLE"}
# BYS360-GOV-LEGACY-001: the only governance decision currently authorized to set
# reconciliation_status=HISTORICAL_UNRECONSTRUCTABLE. See
# docs/governance/BYS360_GOV_LEGACY_001_DECISION_RECORD.md. A bare manual status
# flip without matching reconciliation_governance_decision metadata is rejected below.
GOV_LEGACY_001_DECISION_ID = "BYS360-GOV-LEGACY-001"
# FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1 (approved 2026-08-22): the only decision_id
# currently authorized inside reconciliation_ceiling_waiver_decision. Distinct from
# GOV_LEGACY_001_DECISION_ID by design -- that decision's own text affirmatively
# preserves the ceiling and cannot be reused to lift it. See
# docs/governance/BYS360_GOV_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1.md. No commit's ceiling
# is waived merely by this constant existing -- a waiver only activates for a real
# reconciliation_ceiling_waiver_decision object bound to a specific, eligible commit.
GOV_CEILING_WAIVER_001_DECISION_ID = "BYS360-GOV-CEILING-WAIVER-001"
VALID_CEILING_WAIVER_DECISION_STATUSES = {"APPROVED", "REVOKED", "SUPERSEDED", "PROPOSED_NOT_APPROVED"}
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


def validate_registry(registry: dict[str, Any], *, current_commit: str | None = None) -> RegistryValidationResult:
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
    if reconciliation_status not in VALID_RECONCILIATION_STATUSES:
        findings.append(RegistryFinding(
            "invalid_reconciliation_status", None,
            f"reconciliation_status '{reconciliation_status}' must be one of "
            f"{sorted(VALID_RECONCILIATION_STATUSES)}",
        ))
    if reconciliation_status == "FULLY_RECONCILED" and unmapped_legacy_open_count not in (0, None):
        findings.append(RegistryFinding(
            "reconciliation_status_inconsistent", None,
            "reconciliation_status=FULLY_RECONCILED requires UNMAPPED_LEGACY_OPEN_COUNT == 0 "
            "(every legacy-38 slot confirmed-mapped to an active registry item)",
        ))
    if reconciliation_status == "HISTORICAL_UNRECONSTRUCTABLE":
        decision = registry.get("reconciliation_governance_decision")
        if not isinstance(decision, dict):
            findings.append(RegistryFinding(
                "historical_unreconstructable_missing_decision", None,
                "reconciliation_status=HISTORICAL_UNRECONSTRUCTABLE requires a "
                "reconciliation_governance_decision object recording the approved governance decision",
            ))
        else:
            if decision.get("decision_id") != GOV_LEGACY_001_DECISION_ID:
                findings.append(RegistryFinding(
                    "historical_unreconstructable_wrong_decision_id", None,
                    f"reconciliation_governance_decision.decision_id must be "
                    f"'{GOV_LEGACY_001_DECISION_ID}', got {decision.get('decision_id')!r}",
                ))
            if decision.get("decision_status") != "APPROVED":
                findings.append(RegistryFinding(
                    "historical_unreconstructable_not_approved", None,
                    f"reconciliation_governance_decision.decision_status must be 'APPROVED', "
                    f"got {decision.get('decision_status')!r}",
                ))
            preserved_total = decision.get("preserved_legacy_total")
            if preserved_total != legacy_total:
                findings.append(RegistryFinding(
                    "historical_unreconstructable_total_drift", None,
                    f"reconciliation_governance_decision.preserved_legacy_total ({preserved_total}) "
                    f"does not match current legacy_ledger.TOTAL ({legacy_total}) -- the historical "
                    f"reference must not drift",
                ))
            preserved_split = decision.get("preserved_legacy_priority_split") or {}
            current_split = {
                "P0": legacy_ledger.get("P0"), "P1": legacy_ledger.get("P1"),
                "P2": legacy_ledger.get("P2"), "P3": legacy_ledger.get("P3"),
            }
            if preserved_split != current_split:
                findings.append(RegistryFinding(
                    "historical_unreconstructable_split_drift", None,
                    f"reconciliation_governance_decision.preserved_legacy_priority_split "
                    f"{preserved_split} does not match current legacy_ledger P0/P1/P2/P3 "
                    f"{current_split} -- the historical split must not drift",
                ))

    # ------------------------------------------------------------------
    # FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1 (approved 2026-08-22):
    # OPTIONAL, orthogonal ceiling-waiver decision. Sibling to
    # reconciliation_governance_decision -- never reads for write, sets, or
    # aliases reconciliation_status/legacy_ledger. Registry remains fully
    # valid without this key. Enforcement below applies only while
    # decision_status == "APPROVED"; a REVOKED/SUPERSEDED/PROPOSED_NOT_APPROVED
    # object is preserved verbatim for audit trail but is inert.
    ceiling_waiver = registry.get("reconciliation_ceiling_waiver_decision")
    if ceiling_waiver is not None:
        if not isinstance(ceiling_waiver, dict):
            findings.append(RegistryFinding(
                "ceiling_waiver_invalid_object", None,
                "reconciliation_ceiling_waiver_decision must be an object when present",
            ))
        else:
            decision_status = ceiling_waiver.get("decision_status")
            if decision_status not in VALID_CEILING_WAIVER_DECISION_STATUSES:
                findings.append(RegistryFinding(
                    "ceiling_waiver_invalid_decision_status", None,
                    f"reconciliation_ceiling_waiver_decision.decision_status "
                    f"'{decision_status}' not in {sorted(VALID_CEILING_WAIVER_DECISION_STATUSES)}",
                ))

            waiver_decision_id = ceiling_waiver.get("decision_id")
            if waiver_decision_id == GOV_LEGACY_001_DECISION_ID:
                findings.append(RegistryFinding(
                    "ceiling_waiver_decision_id_reuses_gov_legacy_001", None,
                    f"reconciliation_ceiling_waiver_decision.decision_id must not reuse "
                    f"'{GOV_LEGACY_001_DECISION_ID}' -- that decision's own text affirmatively "
                    "preserves the ceiling and cannot authorize lifting it; mint a distinct decision_id",
                ))
            elif waiver_decision_id != GOV_CEILING_WAIVER_001_DECISION_ID:
                findings.append(RegistryFinding(
                    "ceiling_waiver_wrong_decision_id", None,
                    f"reconciliation_ceiling_waiver_decision.decision_id must be "
                    f"'{GOV_CEILING_WAIVER_001_DECISION_ID}', got {waiver_decision_id!r}",
                ))

            if decision_status == "APPROVED":
                if registry.get("reconciliation_status") != "HISTORICAL_UNRECONSTRUCTABLE":
                    findings.append(RegistryFinding(
                        "ceiling_waiver_requires_historical_unreconstructable", None,
                        "reconciliation_ceiling_waiver_decision is APPROVED but the registry's own "
                        f"reconciliation_status is {registry.get('reconciliation_status')!r}, not "
                        "'HISTORICAL_UNRECONSTRUCTABLE' -- re-checked live here, never trusted from "
                        "reconciliation_governance_decision or cached anywhere",
                    ))

                preserved_total = ceiling_waiver.get("preserved_legacy_total")
                if preserved_total != legacy_total:
                    findings.append(RegistryFinding(
                        "ceiling_waiver_total_drift", None,
                        f"reconciliation_ceiling_waiver_decision.preserved_legacy_total "
                        f"({preserved_total}) does not match current legacy_ledger.TOTAL "
                        f"({legacy_total}) -- the historical reference must not drift",
                    ))

                preserved_split = ceiling_waiver.get("preserved_legacy_priority_split") or {}
                current_waiver_split = {
                    "P0": legacy_ledger.get("P0"), "P1": legacy_ledger.get("P1"),
                    "P2": legacy_ledger.get("P2"), "P3": legacy_ledger.get("P3"),
                }
                if preserved_split != current_waiver_split:
                    findings.append(RegistryFinding(
                        "ceiling_waiver_split_drift", None,
                        f"reconciliation_ceiling_waiver_decision.preserved_legacy_priority_split "
                        f"{preserved_split} does not match current legacy_ledger P0/P1/P2/P3 "
                        f"{current_waiver_split} -- the historical split must not drift",
                    ))

                target_scored_commit = ceiling_waiver.get("target_scored_commit")
                if current_commit is None:
                    findings.append(RegistryFinding(
                        "ceiling_waiver_commit_unverified", None,
                        "reconciliation_ceiling_waiver_decision is APPROVED but no current_commit was "
                        "supplied to validate_registry() to check target_scored_commit against -- the "
                        "real scored commit must be verified, never assumed",
                    ))
                elif target_scored_commit != current_commit:
                    findings.append(RegistryFinding(
                        "ceiling_waiver_commit_mismatch", None,
                        f"reconciliation_ceiling_waiver_decision.target_scored_commit "
                        f"({target_scored_commit!r}) does not match the actual current commit "
                        f"({current_commit!r}) -- this waiver only authorizes the exact commit it "
                        "was approved against",
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

    current_commit: str | None = None
    try:
        git_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=registry_path.resolve().parent,
            capture_output=True,
            text=True,
            check=False,
        )
        if git_result.returncode == 0:
            current_commit = git_result.stdout.strip()
    except OSError:
        current_commit = None

    result = validate_registry(registry, current_commit=current_commit)

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "ok": result.ok,
        "registry_version": registry.get("registry_version"),
        "reconciliation_status": registry.get("reconciliation_status"),
        "current_commit": current_commit,
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
