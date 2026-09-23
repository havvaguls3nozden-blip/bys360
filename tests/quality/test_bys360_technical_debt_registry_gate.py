"""Tests for scripts/quality/bys360_technical_debt_registry_gate.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality.bys360_technical_debt_registry_gate import (
    GOV_CEILING_WAIVER_001_DECISION_ID,
    GOV_LEGACY_001_DECISION_ID,
    validate_registry,
)

pytestmark = pytest.mark.ci_safe

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_REGISTRY_PATH = REPO_ROOT / "config" / "quality" / "bys360_technical_debt_registry.json"


def _item(**overrides):
    base = {
        "id": "TD-001",
        "title": "Example item",
        "status": "CLOSED",
        "severity": "P2",
        "category": "Code Quality",
        "component": "app/example.py",
        "description": "An example debt item for testing.",
        "evidence": ["app/example.py:1"],
        "introduced_commit": None,
        "closure_commit": "abc1234",
        "remote_verified": False,
        "created_at": "2026-01-01",
        "updated_at": "2026-01-02",
        "closure_reason": "Fixed in abc1234.",
        "legacy_mapping": {"status": "UNCONFIRMED", "note": "test fixture"},
        "notes": None,
    }
    base.update(overrides)
    return base


def _minimal_valid_registry(**overrides):
    registry = {
        "schema_version": "1.1",
        "registry_version": "1.1.0",
        "reconciliation_status": "PARTIALLY_RECONCILED",
        "legacy_ledger": {"P0": 0, "P1": 0, "P2": 17, "P3": 21, "TOTAL": 38, "status": "LEGACY_UNMAPPED_WORKING_LEDGER"},
        "items": [_item()],
    }
    registry.update(overrides)
    return registry


def test_canonical_registry_file_validates_cleanly():
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.item_id}:{f.detail}" for f in result.findings]


def test_valid_minimal_registry_accepted():
    result = validate_registry(_minimal_valid_registry())
    assert result.ok
    assert result.findings == []


def test_duplicate_id_rejected():
    registry = _minimal_valid_registry()
    registry["items"].append(dict(registry["items"][0]))
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "duplicate_id" for f in result.findings)


def test_invalid_status_rejected():
    registry = _minimal_valid_registry()
    registry["items"][0]["status"] = "SORT_OF_DONE"
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "invalid_status" for f in result.findings)


def test_invalid_severity_rejected():
    registry = _minimal_valid_registry()
    registry["items"][0]["severity"] = "P9"
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "invalid_severity" for f in result.findings)


def test_closed_without_evidence_rejected():
    registry = _minimal_valid_registry()
    registry["items"][0]["closure_commit"] = None
    registry["items"][0]["closure_reason"] = None
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "closed_without_evidence" for f in result.findings)


def test_closed_with_empty_evidence_list_rejected():
    registry = _minimal_valid_registry()
    registry["items"][0]["evidence"] = []
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code in ("closed_without_evidence", "missing_evidence") for f in result.findings)


def test_open_item_falsely_claiming_closure_rejected():
    registry = _minimal_valid_registry()
    registry["items"][0]["status"] = "OPEN"
    # closure_commit/closure_reason still set from the CLOSED fixture -- contradiction.
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "open_falsely_claims_closure" for f in result.findings)


def test_missing_required_field_rejected():
    registry = _minimal_valid_registry()
    del registry["items"][0]["evidence"]
    result = validate_registry(registry)
    assert not result.ok
    codes = {f.code for f in result.findings}
    assert "missing_field" in codes or "missing_evidence" in codes


def test_missing_legacy_mapping_rejected():
    registry = _minimal_valid_registry()
    del registry["items"][0]["legacy_mapping"]
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code in ("missing_field", "invalid_legacy_mapping") for f in result.findings)


def test_invalid_legacy_mapping_status_rejected():
    registry = _minimal_valid_registry()
    registry["items"][0]["legacy_mapping"] = {"status": "PROBABLY", "note": "x"}
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "invalid_legacy_mapping_status" for f in result.findings)


def test_registry_counts_computed_correctly():
    registry = _minimal_valid_registry()
    registry["items"] = [
        _item(id="TD-001", status="CLOSED"),
        _item(id="TD-CAND-001", status="OPEN", severity="P2", closure_commit=None, closure_reason=None),
        _item(id="TD-CAND-002", status="OPEN", severity="P3", category="Maintainability", closure_commit=None, closure_reason=None),
    ]
    result = validate_registry(registry)
    assert result.ok
    assert result.registry_counts["REGISTRY_TOTAL"] == 3
    assert result.registry_counts["REGISTRY_CLOSED_COUNT"] == 1
    assert result.registry_counts["REGISTRY_ACTIVE_COUNT"] == 2
    assert result.registry_counts["REGISTRY_SEVERITY_COUNTS_ACTIVE"]["P2"] == 1
    assert result.registry_counts["REGISTRY_SEVERITY_COUNTS_ACTIVE"]["P3"] == 1


# ---------------------------------------------------------------------------
# Debt reconciliation invariant tests (registry_version >= 1.1.0)
# ---------------------------------------------------------------------------


def test_closed_items_never_reduce_legacy_open_count():
    """9 closed records must not reduce LEGACY_OPEN_TOTAL or inflate MAPPED_LEGACY_OPEN_COUNT."""
    registry = _minimal_valid_registry()
    registry["items"] = [
        _item(id=f"TD-{i:03d}", status="CLOSED", legacy_mapping={"status": "UNCONFIRMED", "note": "x"})
        for i in range(9)
    ]
    result = validate_registry(registry)
    assert result.ok
    assert result.legacy_counts["LEGACY_OPEN_TOTAL"] == 38
    assert result.legacy_counts["MAPPED_LEGACY_OPEN_COUNT"] == 0
    assert result.legacy_counts["UNMAPPED_LEGACY_OPEN_COUNT"] == 38


def test_confirmed_mapped_open_items_reduce_unmapped_count():
    """legacy open 38 + 5 confirmed mapped -> unmapped 33."""
    registry = _minimal_valid_registry()
    registry["items"] = [
        _item(id=f"TD-CAND-{i:03d}", status="OPEN", closure_commit=None, closure_reason=None,
              legacy_mapping={"status": "CONFIRMED", "note": "matched to legacy entry"})
        for i in range(5)
    ]
    result = validate_registry(registry)
    assert result.ok
    assert result.legacy_counts["MAPPED_LEGACY_OPEN_COUNT"] == 5
    assert result.legacy_counts["UNMAPPED_LEGACY_OPEN_COUNT"] == 33


def test_mixed_confirmed_and_unconfirmed_mapping():
    """legacy open 38 + 3 confirmed + 2 unconfirmed -> unmapped 35 (unconfirmed don't count as mapped)."""
    registry = _minimal_valid_registry()
    registry["items"] = [
        *[_item(id=f"TD-CAND-C{i}", status="OPEN", closure_commit=None, closure_reason=None,
                legacy_mapping={"status": "CONFIRMED", "note": "x"}) for i in range(3)],
        *[_item(id=f"TD-CAND-U{i}", status="OPEN", closure_commit=None, closure_reason=None,
                legacy_mapping={"status": "UNCONFIRMED", "note": "x"}) for i in range(2)],
    ]
    result = validate_registry(registry)
    assert result.ok
    assert result.legacy_counts["MAPPED_LEGACY_OPEN_COUNT"] == 3
    assert result.legacy_counts["UNMAPPED_LEGACY_OPEN_COUNT"] == 35


def test_active_status_semantics_include_non_open_unresolved_statuses():
    """BLOCKED/IN_PROGRESS/DEFERRED/ACCEPTED_RISK all count as REGISTRY_ACTIVE_COUNT, not just OPEN."""
    registry = _minimal_valid_registry()
    registry["items"] = [
        _item(id="TD-CAND-A", status="OPEN", closure_commit=None, closure_reason=None),
        _item(id="TD-CAND-B", status="BLOCKED", closure_commit=None, closure_reason=None),
        _item(id="TD-CAND-C", status="IN_PROGRESS", closure_commit=None, closure_reason=None),
        _item(id="TD-CAND-D", status="DEFERRED", closure_commit=None, closure_reason=None),
        _item(id="TD-CAND-E", status="ACCEPTED_RISK", closure_commit=None, closure_reason=None),
        _item(id="TD-001", status="CLOSED"),
    ]
    result = validate_registry(registry)
    assert result.ok
    assert result.registry_counts["REGISTRY_ACTIVE_COUNT"] == 5
    assert result.registry_counts["REGISTRY_CLOSED_COUNT"] == 1
    assert result.registry_counts["REGISTRY_TOTAL"] == 6


def test_closed_item_with_confirmed_legacy_mapping_is_excluded_not_rejected():
    """A CLOSED item may carry legacy_mapping.status=CONFIRMED as valuable audit history,
    but it must not count toward MAPPED_LEGACY_OPEN_COUNT (that count is active-only)."""
    registry = _minimal_valid_registry()
    registry["items"] = [
        _item(id="TD-001", status="CLOSED", legacy_mapping={"status": "CONFIRMED", "note": "later confirmed legacy member"}),
    ]
    result = validate_registry(registry)
    assert result.ok  # not rejected
    assert result.legacy_counts["MAPPED_LEGACY_OPEN_COUNT"] == 0  # but excluded from the active-only count


def test_mapped_exceeding_legacy_total_rejected():
    registry = _minimal_valid_registry(legacy_ledger={"P0": 0, "P1": 0, "P2": 1, "P3": 0, "TOTAL": 1, "status": "x"})
    registry["items"] = [
        _item(id=f"TD-CAND-{i}", status="OPEN", closure_commit=None, closure_reason=None,
              legacy_mapping={"status": "CONFIRMED", "note": "x"})
        for i in range(2)
    ]
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "mapped_exceeds_legacy_total" for f in result.findings)


def test_unmapped_legacy_open_count_never_negative():
    """The invariant LEGACY_OPEN_TOTAL >= MAPPED_LEGACY_OPEN_COUNT prevents a negative unmapped count."""
    registry = _minimal_valid_registry(legacy_ledger={"P0": 0, "P1": 0, "P2": 1, "P3": 0, "TOTAL": 1, "status": "x"})
    registry["items"] = [
        _item(id=f"TD-CAND-{i}", status="OPEN", closure_commit=None, closure_reason=None,
              legacy_mapping={"status": "CONFIRMED", "note": "x"})
        for i in range(3)
    ]
    result = validate_registry(registry)
    assert not result.ok
    # Either the exceeds-total finding or the negative-count finding must fire; both point at the same defect.
    codes = {f.code for f in result.findings}
    assert "mapped_exceeds_legacy_total" in codes or "negative_unmapped_legacy_open_count" in codes


def test_legacy_invariant_equation_holds_on_valid_registry():
    registry = _minimal_valid_registry()
    result = validate_registry(registry)
    lc = result.legacy_counts
    assert lc["LEGACY_OPEN_TOTAL"] == lc["MAPPED_LEGACY_OPEN_COUNT"] + lc["UNMAPPED_LEGACY_OPEN_COUNT"]


def test_registry_open_unlinked_count_is_active_minus_mapped():
    registry = _minimal_valid_registry()
    registry["items"] = [
        _item(id="TD-CAND-1", status="OPEN", closure_commit=None, closure_reason=None,
              legacy_mapping={"status": "CONFIRMED", "note": "x"}),
        _item(id="TD-CAND-2", status="OPEN", closure_commit=None, closure_reason=None,
              legacy_mapping={"status": "UNCONFIRMED", "note": "x"}),
        _item(id="TD-CAND-3", status="OPEN", closure_commit=None, closure_reason=None,
              legacy_mapping={"status": "UNCONFIRMED", "note": "x"}),
    ]
    result = validate_registry(registry)
    assert result.registry_counts["REGISTRY_ACTIVE_COUNT"] == 3
    assert result.registry_counts["MAPPED_LEGACY_OPEN_COUNT"] == 1
    assert result.registry_counts["REGISTRY_OPEN_UNLINKED_COUNT"] == 2


def test_canonical_registry_matches_expected_corrected_values():
    """Pin the exact corrected accounting for the real, current registry -- guards against
    silently reintroducing the old (legacy_total - TOTAL_ITEMS-including-closed) bug."""
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    result = validate_registry(registry)
    assert result.ok
    assert result.registry_counts["REGISTRY_TOTAL"] == 14
    assert result.registry_counts["REGISTRY_CLOSED_COUNT"] == 14
    assert result.registry_counts["REGISTRY_ACTIVE_COUNT"] == 0
    assert result.legacy_counts["LEGACY_OPEN_TOTAL"] == 38
    assert result.legacy_counts["MAPPED_LEGACY_OPEN_COUNT"] == 0
    assert result.legacy_counts["UNMAPPED_LEGACY_OPEN_COUNT"] == 38


def test_legacy_ledger_never_overwritten_by_registry_derived_counts():
    registry = _minimal_valid_registry()
    result = validate_registry(registry)
    assert result.legacy_counts["LEGACY_P2"] == 17
    assert result.legacy_counts["LEGACY_P3"] == 21
    assert result.legacy_counts["LEGACY_OPEN_TOTAL"] == 38
    assert result.legacy_counts["LEGACY_OPEN_TOTAL"] != result.registry_counts["REGISTRY_TOTAL"]


# ---------------------------------------------------------------------------
# BYS360-GOV-LEGACY-001: HISTORICAL_UNRECONSTRUCTABLE reconciliation state.
# ---------------------------------------------------------------------------


def _valid_gov_decision(**overrides):
    decision = {
        "decision_id": GOV_LEGACY_001_DECISION_ID,
        "decision_status": "APPROVED",
        "preserved_legacy_total": 38,
        "preserved_legacy_priority_split": {"P0": 0, "P1": 0, "P2": 17, "P3": 21},
    }
    decision.update(overrides)
    return decision


def test_historical_unreconstructable_accepted_with_valid_decision_metadata():
    registry = _minimal_valid_registry(
        reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE",
        reconciliation_governance_decision=_valid_gov_decision(),
    )
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]
    assert result.findings == []


def test_historical_unreconstructable_rejected_without_decision_metadata():
    """Bare manual status flip with no governance-decision object at all must fail."""
    registry = _minimal_valid_registry(reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "historical_unreconstructable_missing_decision" for f in result.findings)


def test_historical_unreconstructable_rejected_with_wrong_decision_id():
    registry = _minimal_valid_registry(
        reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE",
        reconciliation_governance_decision=_valid_gov_decision(decision_id="SOME-OTHER-DECISION"),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "historical_unreconstructable_wrong_decision_id" for f in result.findings)


def test_historical_unreconstructable_rejected_when_not_approved():
    registry = _minimal_valid_registry(
        reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE",
        reconciliation_governance_decision=_valid_gov_decision(decision_status="PROPOSED_NOT_APPROVED"),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "historical_unreconstructable_not_approved" for f in result.findings)


def test_historical_unreconstructable_rejected_when_preserved_total_drifts():
    """Anti-gaming: the historical 38 cannot be silently changed while riding this decision."""
    registry = _minimal_valid_registry(
        reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE",
        reconciliation_governance_decision=_valid_gov_decision(preserved_legacy_total=0),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "historical_unreconstructable_total_drift" for f in result.findings)


def test_historical_unreconstructable_rejected_when_preserved_split_drifts():
    """Anti-gaming: the historical P2/P3 split cannot be silently changed while riding this decision."""
    registry = _minimal_valid_registry(
        reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE",
        reconciliation_governance_decision=_valid_gov_decision(
            preserved_legacy_priority_split={"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        ),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "historical_unreconstructable_split_drift" for f in result.findings)


def test_unknown_reconciliation_status_still_rejected_after_adding_new_state():
    """Adding HISTORICAL_UNRECONSTRUCTABLE must not accidentally widen the enum to 'anything'."""
    registry = _minimal_valid_registry(reconciliation_status="SOME_MADE_UP_STATUS")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "invalid_reconciliation_status" for f in result.findings)


def test_fully_reconciled_semantics_unweakened_by_new_state():
    """FULLY_RECONCILED still requires UNMAPPED_LEGACY_OPEN_COUNT == 0 -- HISTORICAL_UNRECONSTRUCTABLE
    is not a backdoor to a weaker FULLY_RECONCILED."""
    registry = _minimal_valid_registry(reconciliation_status="FULLY_RECONCILED")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "reconciliation_status_inconsistent" for f in result.findings)


def test_canonical_registry_now_uses_historical_unreconstructable_with_valid_decision():
    """End-to-end: the real, currently-committed registry reflects the approved
    BYS360-GOV-LEGACY-001 decision and validates cleanly."""
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    assert registry["reconciliation_status"] == "HISTORICAL_UNRECONSTRUCTABLE"
    decision = registry["reconciliation_governance_decision"]
    assert decision["decision_id"] == GOV_LEGACY_001_DECISION_ID
    assert decision["decision_status"] == "APPROVED"
    assert decision["preserved_legacy_total"] == 38
    assert decision["preserved_legacy_priority_split"] == {"P0": 0, "P1": 0, "P2": 17, "P3": 21}
    # Historical values themselves remain byte-identical to before this decision.
    assert registry["legacy_ledger"]["TOTAL"] == 38
    assert registry["legacy_ledger"]["P0"] == 0
    assert registry["legacy_ledger"]["P1"] == 0
    assert registry["legacy_ledger"]["P2"] == 17
    assert registry["legacy_ledger"]["P3"] == 21
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]


def test_fully_reconciled_requires_zero_unmapped():
    registry = _minimal_valid_registry(reconciliation_status="FULLY_RECONCILED")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "reconciliation_status_inconsistent" for f in result.findings)


def test_invalid_reconciliation_status_rejected():
    registry = _minimal_valid_registry(reconciliation_status="MOSTLY_FINE_PROBABLY")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "invalid_reconciliation_status" for f in result.findings)


# ---------------------------------------------------------------------------
# FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1 (approved 2026-08-22), binding
# hardened 2026-08-23: reconciliation_ceiling_waiver_decision -- orthogonal to
# reconciliation_status and reconciliation_governance_decision. Never claims
# FULLY_RECONCILED, never rewrites the historical fact; only a separate,
# drift-checked governance decision about whether the ceiling still needs to
# apply. approval_baseline_commit is documentary/anchoring only (mirroring
# reconciliation_governance_decision.target_baseline_commit's own precedent) --
# this validator checks only its shape, never compares it to "the commit
# currently being scored" (that binding conflation was the pre-hardening
# design's flaw). The actual current-commit provenance check now lives in the
# calculator (bys360_score_reconcile_v1.py's
# _registry_matches_scored_commit_tree()), not here.
# ---------------------------------------------------------------------------

APPROVAL_BASELINE_COMMIT = "8529ca57e37a1c8c10a513584e61998f799dd1af"


def _valid_ceiling_waiver_decision(**overrides):
    decision = {
        "decision_id": GOV_CEILING_WAIVER_001_DECISION_ID,
        "decision_status": "APPROVED",
        "approval_baseline_commit": APPROVAL_BASELINE_COMMIT,
        "preserved_legacy_total": 38,
        "preserved_legacy_priority_split": {"P0": 0, "P1": 0, "P2": 17, "P3": 21},
    }
    decision.update(overrides)
    return decision


def _historical_unreconstructable_registry(**overrides):
    return _minimal_valid_registry(
        reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE",
        reconciliation_governance_decision=_valid_gov_decision(),
        **overrides,
    )


def test_ceiling_waiver_absent_is_still_a_valid_registry():
    """Optional field: the registry stays fully valid with no waiver object at all --
    zero blast radius for every registry that predates this policy."""
    registry = _historical_unreconstructable_registry()
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]


def test_ceiling_waiver_accepted_with_valid_metadata():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(),
    )
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]


def test_ceiling_waiver_rejected_with_wrong_decision_id():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(decision_id="SOME-OTHER-ID"),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_wrong_decision_id" for f in result.findings)


def test_ceiling_waiver_rejected_when_reusing_gov_legacy_001_decision_id():
    """Anti-gaming: GOV-LEGACY-001's own text affirmatively preserves the ceiling --
    its decision_id can never be reused to authorize lifting it."""
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(
            decision_id=GOV_LEGACY_001_DECISION_ID,
        ),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_decision_id_reuses_gov_legacy_001" for f in result.findings)


def test_ceiling_waiver_rejected_with_invalid_decision_status():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(decision_status="MADE_UP"),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_invalid_decision_status" for f in result.findings)


def test_ceiling_waiver_revoked_status_is_inert_not_a_failing_finding():
    """A REVOKED decision is preserved verbatim for audit trail, not deleted -- and
    does not itself fail registry validation (it simply confers no waiver)."""
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(decision_status="REVOKED"),
    )
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]


def test_ceiling_waiver_rejected_when_reconciliation_status_not_historical_unreconstructable():
    registry = _minimal_valid_registry(
        reconciliation_status="PARTIALLY_RECONCILED",
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_requires_historical_unreconstructable" for f in result.findings)


def test_ceiling_waiver_rejected_when_preserved_total_drifts():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(preserved_legacy_total=0),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_total_drift" for f in result.findings)


def test_ceiling_waiver_rejected_when_preserved_split_drifts():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(
            preserved_legacy_priority_split={"P0": 0, "P1": 0, "P2": 0, "P3": 0},
        ),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_split_drift" for f in result.findings)


def test_ceiling_waiver_rejected_when_approval_baseline_commit_missing():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(approval_baseline_commit=None),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_invalid_approval_baseline_commit" for f in result.findings)


def test_ceiling_waiver_rejected_when_approval_baseline_commit_malformed():
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(
            approval_baseline_commit="not-a-real-sha",
        ),
    )
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_invalid_approval_baseline_commit" for f in result.findings)


def test_ceiling_waiver_approval_baseline_commit_not_compared_to_any_current_commit():
    """The hardened design's central property: approval_baseline_commit is purely
    documentary and is never checked against any notion of "the current commit" --
    validate_registry() no longer even accepts a current_commit parameter. Any
    well-formed SHA is accepted here; provenance-to-scored-commit binding is the
    calculator's job now, not this validator's."""
    registry = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_ceiling_waiver_decision(
            approval_baseline_commit="0" * 40,
        ),
    )
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]


def test_ceiling_waiver_invalid_object_type_rejected():
    registry = _historical_unreconstructable_registry(reconciliation_ceiling_waiver_decision="not-an-object")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "ceiling_waiver_invalid_object" for f in result.findings)


def test_canonical_registry_ceiling_waiver_decision_present_and_schema_valid():
    """WAIVER_ACTIVATION_APPROVED (2026-08-23): a human-approved
    reconciliation_ceiling_waiver_decision now exists (decision_id
    BYS360-GOV-CEILING-WAIVER-001, bound to approval_baseline_commit fe984cf, itself
    exact-head remotely attested). DECISION_RECORD_PRESENT=YES is a distinct fact from
    canonical waiver eligibility -- registry-gate validation only confirms this
    object's own shape/drift correctness, never that any commit's ceiling is
    canonically waived (that additionally requires registry_commit_verified and fresh,
    commit-bound Quality/Score100 evidence, evaluated only by the calculator)."""
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    decision = registry.get("reconciliation_ceiling_waiver_decision")
    assert decision is not None
    assert decision["decision_id"] == GOV_CEILING_WAIVER_001_DECISION_ID
    assert decision["decision_status"] == "APPROVED"
    assert decision["approval_baseline_commit"] == "fe984cf1542e8769e9d1e40400a9a533f5cac6d0"
    assert decision["preserved_legacy_total"] == 38
    assert decision["preserved_legacy_priority_split"] == {"P0": 0, "P1": 0, "P2": 17, "P3": 21}
    result = validate_registry(registry)
    assert result.ok, [f"{f.code}:{f.detail}" for f in result.findings]
    # Historical truth unaffected by this decision's presence.
    assert registry["reconciliation_status"] == "HISTORICAL_UNRECONSTRUCTABLE"
    assert registry["legacy_ledger"]["TOTAL"] == 38
