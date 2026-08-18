"""Tests for scripts/quality/bys360_technical_debt_registry_gate.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality.bys360_technical_debt_registry_gate import validate_registry

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
    assert result.registry_counts["REGISTRY_CLOSED_COUNT"] == 9
    assert result.registry_counts["REGISTRY_ACTIVE_COUNT"] == 5
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
