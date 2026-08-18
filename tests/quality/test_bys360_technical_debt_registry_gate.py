"""Tests for scripts/quality/bys360_technical_debt_registry_gate.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality.bys360_technical_debt_registry_gate import validate_registry

pytestmark = pytest.mark.ci_safe

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_REGISTRY_PATH = REPO_ROOT / "config" / "quality" / "bys360_technical_debt_registry.json"


def _minimal_valid_registry(**overrides):
    registry = {
        "schema_version": "1.0",
        "registry_version": "1.0.0",
        "reconciliation_status": "PARTIALLY_RECONCILED",
        "legacy_ledger": {"P0": 0, "P1": 0, "P2": 17, "P3": 21, "TOTAL": 38, "status": "LEGACY_UNMAPPED_WORKING_LEDGER"},
        "items": [
            {
                "id": "TD-001",
                "title": "Example closed item",
                "status": "CLOSED",
                "severity": "P2",
                "category": "Code Quality",
                "component": "app/example.py",
                "description": "An example closed debt item for testing.",
                "evidence": ["app/example.py:1"],
                "introduced_commit": None,
                "closure_commit": "abc1234",
                "remote_verified": False,
                "created_at": "2026-01-01",
                "updated_at": "2026-01-02",
                "closure_reason": "Fixed in abc1234.",
                "notes": None,
            },
        ],
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


def test_registry_derived_counts_computed_correctly():
    registry = _minimal_valid_registry()
    registry["items"] = [
        {**_minimal_valid_registry()["items"][0], "id": "TD-001", "status": "CLOSED"},
        {
            "id": "TD-CAND-001", "title": "open p2", "status": "OPEN", "severity": "P2",
            "category": "Code Quality", "component": "x", "description": "d",
            "evidence": ["x:1"], "introduced_commit": None, "closure_commit": None,
            "remote_verified": False, "created_at": None, "updated_at": "2026-01-01",
            "closure_reason": None, "notes": None,
        },
        {
            "id": "TD-CAND-002", "title": "open p3", "status": "OPEN", "severity": "P3",
            "category": "Maintainability", "component": "x", "description": "d",
            "evidence": ["x:1"], "introduced_commit": None, "closure_commit": None,
            "remote_verified": False, "created_at": None, "updated_at": "2026-01-01",
            "closure_reason": None, "notes": None,
        },
    ]
    result = validate_registry(registry)
    assert result.ok
    assert result.registry_derived_counts["P2"] == 1
    assert result.registry_derived_counts["P3"] == 1
    assert result.registry_derived_counts["TOTAL_OPEN"] == 2
    assert result.registry_derived_counts["CLOSED_COUNT"] == 1


def test_legacy_ledger_never_overwritten_by_registry_derived_counts():
    registry = _minimal_valid_registry()
    result = validate_registry(registry)
    # Legacy ledger figures must pass through completely unmodified.
    assert result.legacy_unmapped_ledger_counts["P2"] == 17
    assert result.legacy_unmapped_ledger_counts["P3"] == 21
    assert result.legacy_unmapped_ledger_counts["TOTAL"] == 38
    # And must be distinct from (not silently equal to) the registry-derived total.
    assert result.legacy_unmapped_ledger_counts["TOTAL"] != result.registry_derived_counts["TOTAL_ITEMS"]


def test_fully_reconciled_requires_matching_totals():
    registry = _minimal_valid_registry(reconciliation_status="FULLY_RECONCILED")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "reconciliation_status_inconsistent" for f in result.findings)


def test_invalid_reconciliation_status_rejected():
    registry = _minimal_valid_registry(reconciliation_status="MOSTLY_FINE_PROBABLY")
    result = validate_registry(registry)
    assert not result.ok
    assert any(f.code == "invalid_reconciliation_status" for f in result.findings)
