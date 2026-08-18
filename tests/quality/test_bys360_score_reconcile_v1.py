"""Tests for scripts/quality/bys360_score_reconcile_v1.py.

These tests avoid invoking real subprocess gates (ruff/mypy/etc.) so they
stay fast and deterministic: every gate in the fixture methodology uses
pass_rule="exit_code_0_or_supplied_evidence" with results supplied via the
`evidence` dict, exactly like the real script's --evidence mechanism.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality.bys360_score_reconcile_v1 import (
    LEGACY_SNAPSHOT,
    _round_half_up,
    compute_report,
)

pytestmark = pytest.mark.ci_safe

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_METHODOLOGY_PATH = REPO_ROOT / "config" / "quality" / "bys360_scoring_methodology_v1.json"
CANONICAL_REGISTRY_PATH = REPO_ROOT / "config" / "quality" / "bys360_technical_debt_registry.json"


def _fixture_methodology(**category_overrides):
    categories = {
        "Code Quality": {
            "gate_component_weight": 0.8, "rubric_component_weight": 0.2,
            "gates": [{"name": "gate_a", "pass_rule": "exit_code_0_or_supplied_evidence"}],
            "rubric": [{"name": "open_debt_inverse", "source": "registry_open_count_in_category"}],
        },
        "Test Assurance": {
            "gate_component_weight": 0.8, "rubric_component_weight": 0.2,
            "gates": [{"name": "gate_b", "pass_rule": "exit_code_0_or_supplied_evidence"}],
            "rubric": [{"name": "open_debt_inverse", "source": "registry_open_count_in_category"}],
        },
        "Security": {
            "gate_component_weight": 0.8, "rubric_component_weight": 0.2,
            "gates": [{"name": "gate_c", "pass_rule": "exit_code_0_or_supplied_evidence"}],
            "rubric": [{"name": "open_debt_inverse", "source": "registry_open_count_in_category"}],
        },
        "CI-Release": {
            "gate_component_weight": 0.8, "rubric_component_weight": 0.2,
            "gates": [{"name": "gate_d", "pass_rule": "exit_code_0_or_supplied_evidence"}],
            "rubric": [{"name": "open_debt_inverse", "source": "registry_open_count_in_category"}],
        },
        "Operations": {
            "gate_component_weight": 0.8, "rubric_component_weight": 0.2,
            "gates": [{"name": "gate_e", "pass_rule": "exit_code_0_or_supplied_evidence"}],
            "rubric": [{"name": "open_debt_inverse", "source": "registry_open_count_in_category"}],
        },
        "Documentation-Handover": {
            "gate_component_weight": 0.7, "rubric_component_weight": 0.3,
            "gates": [{"name": "gate_f", "pass_rule": "exit_code_0_or_supplied_evidence"}],
            "rubric": [{"name": "registry_reconciliation_transparency", "source": "registry.reconciliation_status"}],
        },
        "Maintainability": {
            "gate_component_weight": 0.6, "rubric_component_weight": 0.4,
            "gates": [{"name": "no_open_p0_or_p1_anywhere", "pass_rule": "boolean"}],
            "rubric": [{"name": "open_debt_inverse", "source": "registry_open_count_in_category"}],
        },
    }
    for category, override in category_overrides.items():
        categories[category].update(override)
    return {
        "methodology_version": "1.0.0-test",
        "debt_penalty_policy": {
            "severity_weights": {"P0": 40, "P1": 20, "P2": 8, "P3": 3, "UNCLASSIFIED": 5},
            "penalty_cap_per_category": 30,
        },
        "evidence_completeness_ceiling": {"value": 89},
        "composites": {
            "LIVE_READINESS": {"weights": {
                "Security": 0.22, "Test Assurance": 0.21, "CI-Release": 0.21, "Operations": 0.20,
                "Code Quality": 0.10, "Maintainability": 0.03, "Documentation-Handover": 0.03,
            }},
            "TRANSFERABILITY": {"weights": {
                "Documentation-Handover": 0.22, "Maintainability": 0.22, "Test Assurance": 0.18,
                "Code Quality": 0.15, "CI-Release": 0.10, "Operations": 0.06, "Security": 0.07,
            }},
        },
        "categories": categories,
    }


def _fixture_registry(items=None, reconciliation_status="FULLY_RECONCILED"):
    return {
        "registry_version": "1.0.0-test",
        "reconciliation_status": reconciliation_status,
        "reconciliation_note": "test note",
        "items": items or [],
    }


def _all_gates_pass_evidence():
    return {"gate_a": True, "gate_b": True, "gate_c": True, "gate_d": True, "gate_e": True, "gate_f": True}


def test_all_gates_pass_no_debt_yields_full_gate_credit(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    for name, cs in report["category_scores"].items():
        assert cs["gate_component"] == pytest.approx(methodology["categories"][name]["gate_component_weight"] * 100)
        assert cs["debt_penalty"] == 0


def test_score_range_always_0_to_100(tmp_path):
    items = [
        {"id": f"TD-{i}", "status": "OPEN", "severity": "P0", "category": "Code Quality"}
        for i in range(20)
    ]
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=items)
    report = compute_report(methodology, registry, tmp_path, {})
    for cs in report["category_scores"].values():
        assert 0 <= cs["final_score"] <= 100
    assert 0 <= report["LIVE_READINESS"]["final"] <= 100
    assert 0 <= report["TRANSFERABILITY"]["final"] <= 100


def test_deterministic_repeated_calculation(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[
        {"id": "TD-CAND-001", "status": "OPEN", "severity": "P2", "category": "Code Quality"},
    ])
    evidence = _all_gates_pass_evidence()
    report1 = compute_report(methodology, registry, tmp_path, evidence)
    report2 = compute_report(methodology, registry, tmp_path, evidence)
    # generated_at will differ; strip it before comparing.
    r1 = {k: v for k, v in report1.items() if k != "generated_at"}
    r2 = {k: v for k, v in report2.items() if k != "generated_at"}
    assert r1 == r2


def test_missing_evidence_scores_zero_gate_component_not_full_credit(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, evidence={})  # nothing supplied -> all UNKNOWN
    for name, cs in report["category_scores"].items():
        if name == "Maintainability":
            continue  # boolean gate computed from registry directly
        assert cs["gate_component"] == 0, f"{name} gate_component should be 0 when evidence is fully UNKNOWN"
    assert report["fully_verified"] is False
    assert report["unverified_evidence_count"] > 0


def test_missing_evidence_is_not_silently_treated_as_pass(tmp_path):
    """A gate with no supplied evidence must never be scored identically to a genuine PASS."""
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    unknown_report = compute_report(methodology, registry, tmp_path, evidence={})
    pass_report = compute_report(methodology, registry, tmp_path, evidence=_all_gates_pass_evidence())
    assert unknown_report["category_scores"]["Code Quality"]["gate_component"] < pass_report["category_scores"]["Code Quality"]["gate_component"]


def test_p0_debt_materially_degrades_live_readiness(tmp_path):
    """Sensitivity scenario A: introducing a P0 must materially lower LIVE_READINESS."""
    methodology = _fixture_methodology()
    clean_registry = _fixture_registry(items=[])
    p0_registry = _fixture_registry(items=[
        {"id": "TD-CAND-999", "status": "OPEN", "severity": "P0", "category": "Security"},
    ])
    evidence = _all_gates_pass_evidence()
    clean_report = compute_report(methodology, clean_registry, tmp_path, evidence)
    p0_report = compute_report(methodology, p0_registry, tmp_path, evidence)
    assert p0_report["LIVE_READINESS"]["raw"] < clean_report["LIVE_READINESS"]["raw"]
    # A P0 must also make Maintainability's boolean gate fail globally.
    assert p0_report["category_scores"]["Maintainability"]["gates"][0]["status"] == "FAIL"
    assert clean_report["category_scores"]["Maintainability"]["gates"][0]["status"] == "PASS"


def test_documentation_gap_materially_affects_transferability_not_test_assurance(tmp_path):
    """Sensitivity scenario B/C: a Documentation-Handover-only weakness should move
    TRANSFERABILITY but must not move Test Assurance (no cross-category bleed)."""
    methodology = _fixture_methodology()
    good_registry = _fixture_registry(items=[])
    doc_gap_registry = _fixture_registry(items=[
        {"id": "TD-CAND-999", "status": "OPEN", "severity": "P2", "category": "Documentation-Handover"},
    ])
    evidence = _all_gates_pass_evidence()
    good_report = compute_report(methodology, good_registry, tmp_path, evidence)
    gap_report = compute_report(methodology, doc_gap_registry, tmp_path, evidence)

    assert gap_report["category_scores"]["Documentation-Handover"]["final_score"] < good_report["category_scores"]["Documentation-Handover"]["final_score"]
    assert gap_report["TRANSFERABILITY"]["raw"] < good_report["TRANSFERABILITY"]["raw"]
    # No double counting: Test Assurance must be completely unaffected by a Documentation-only debt item.
    assert gap_report["category_scores"]["Test Assurance"]["final_score"] == good_report["category_scores"]["Test Assurance"]["final_score"]


def test_rounding_is_round_half_up():
    assert _round_half_up(67.5) == 68
    assert _round_half_up(67.4) == 67
    assert _round_half_up(67.49999) == 67
    assert _round_half_up(0.5) == 1
    assert _round_half_up(100.0) == 100


def test_unclassified_debt_is_not_a_free_pass(tmp_path):
    """Anti-gaming: leaving a debt item permanently UNCLASSIFIED must still cost points."""
    methodology = _fixture_methodology()
    registry_unclassified = _fixture_registry(items=[
        {"id": "TD-CAND-999", "status": "OPEN", "severity": "UNCLASSIFIED", "category": "Code Quality"},
    ])
    registry_clean = _fixture_registry(items=[])
    evidence = _all_gates_pass_evidence()
    report_unclassified = compute_report(methodology, registry_unclassified, tmp_path, evidence)
    report_clean = compute_report(methodology, registry_clean, tmp_path, evidence)
    assert report_unclassified["category_scores"]["Code Quality"]["final_score"] < report_clean["category_scores"]["Code Quality"]["final_score"]
    assert report_unclassified["category_scores"]["Code Quality"]["debt_penalty"] > 0


def test_evidence_completeness_ceiling_applies_when_registry_not_fully_reconciled(tmp_path):
    methodology = _fixture_methodology()
    registry_partial = _fixture_registry(items=[], reconciliation_status="PARTIALLY_RECONCILED")
    evidence = _all_gates_pass_evidence()
    report = compute_report(methodology, registry_partial, tmp_path, evidence)
    assert report["evidence_completeness_ceiling_applied"] is True
    assert report["LIVE_READINESS"]["ceiling_applied_value"] <= 89
    assert report["TRANSFERABILITY"]["ceiling_applied_value"] <= 89


def test_no_ceiling_when_fully_verified_and_fully_reconciled(tmp_path):
    methodology = _fixture_methodology()
    registry_full = _fixture_registry(items=[], reconciliation_status="FULLY_RECONCILED")
    evidence = _all_gates_pass_evidence()
    report = compute_report(methodology, registry_full, tmp_path, evidence)
    assert report["evidence_completeness_ceiling_applied"] is False


def test_legacy_snapshot_never_mutated_by_calculation(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[
        {"id": "TD-CAND-999", "status": "OPEN", "severity": "P0", "category": "Security"},
    ])
    report = compute_report(methodology, registry, tmp_path, {})
    assert report["legacy_snapshot"] == LEGACY_SNAPSHOT
    assert report["legacy_snapshot"]["LIVE_READINESS"] == 68
    assert report["legacy_snapshot"]["TRANSFERABILITY"] == 61


def test_double_counting_prevented_between_categories(tmp_path):
    """A debt item filed under one category must not penalize any other category."""
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[
        {"id": "TD-CAND-999", "status": "OPEN", "severity": "P1", "category": "Operations"},
    ])
    evidence = _all_gates_pass_evidence()
    report = compute_report(methodology, registry, tmp_path, evidence)
    assert report["category_scores"]["Operations"]["debt_penalty"] > 0
    for name, cs in report["category_scores"].items():
        if name == "Operations":
            continue
        assert cs["debt_penalty"] == 0, f"{name} should not be penalized by an Operations-category debt item"


def test_canonical_methodology_and_registry_files_produce_a_valid_report(tmp_path):
    """End-to-end smoke test against the real canonical config files, with all
    subprocess gates skipped (supplied as UNKNOWN) to keep this test fast and
    independent of the ambient environment's tool availability."""
    methodology = json.loads(CANONICAL_METHODOLOGY_PATH.read_text(encoding="utf-8"))
    for category_config in methodology["categories"].values():
        for gate in category_config.get("gates", []):
            if gate.get("pass_rule") != "boolean":
                gate["pass_rule"] = "exit_code_0_or_supplied_evidence"
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    report = compute_report(methodology, registry, tmp_path, evidence={})
    assert set(report["category_scores"].keys()) == set(methodology["categories"].keys())
    assert isinstance(report["LIVE_READINESS"]["final"], int)
    assert isinstance(report["TRANSFERABILITY"]["final"], int)
    assert report["legacy_snapshot"]["LIVE_READINESS"] == 68
