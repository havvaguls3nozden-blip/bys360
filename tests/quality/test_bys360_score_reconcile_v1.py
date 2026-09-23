"""Tests for scripts/quality/bys360_score_reconcile_v1.py.

These tests avoid invoking real subprocess gates (ruff/mypy/etc.) so they
stay fast and deterministic: every gate in the fixture methodology uses
pass_rule="exit_code_0_or_supplied_evidence" with results supplied via the
`evidence` dict, exactly like the real script's --evidence mechanism.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.quality.bys360_score_reconcile_v1 import (
    LEGACY_SNAPSHOT,
    SCORE100_WORKFLOW_GATE_ID,
    _build_argv,
    _registry_matches_scored_commit_tree,
    _round_half_up,
    compute_report,
    resolve_python,
)
from scripts.quality.bys360_technical_debt_registry_gate import (
    GOV_CEILING_WAIVER_001_DECISION_ID,
    GOV_LEGACY_001_DECISION_ID,
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


# ---------------------------------------------------------------------------
# BYS360-GOV-LEGACY-001: HISTORICAL_UNRECONSTRUCTABLE reconciliation state.
# ---------------------------------------------------------------------------


def test_ceiling_still_applies_for_historical_unreconstructable(tmp_path):
    """Anti-gaming: the new state must not be treated as reconciled for ceiling purposes,
    even when every gate is fully verified."""
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[], reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE")
    evidence = _all_gates_pass_evidence()
    report = compute_report(methodology, registry, tmp_path, evidence)
    assert report["fully_verified"] is True
    assert report["evidence_completeness_ceiling_applied"] is True
    assert report["LIVE_READINESS"]["ceiling_applied_value"] <= 89
    assert report["TRANSFERABILITY"]["ceiling_applied_value"] <= 89


def test_historical_unreconstructable_is_not_treated_as_fully_reconciled(tmp_path):
    """HISTORICAL_UNRECONSTRUCTABLE must produce a strictly lower ceiling outcome than
    FULLY_RECONCILED -- it is not a backdoor synonym for full reconciliation."""
    methodology = _fixture_methodology()
    evidence = _all_gates_pass_evidence()
    historical_report = compute_report(
        methodology, _fixture_registry(items=[], reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE"),
        tmp_path, evidence,
    )
    fully_report = compute_report(
        methodology, _fixture_registry(items=[], reconciliation_status="FULLY_RECONCILED"),
        tmp_path, evidence,
    )
    assert historical_report["evidence_completeness_ceiling_applied"] is True
    assert fully_report["evidence_completeness_ceiling_applied"] is False
    assert historical_report["LIVE_READINESS"]["final"] <= fully_report["LIVE_READINESS"]["final"]


def test_historical_unreconstructable_documentation_handover_matches_partial_not_full(tmp_path):
    """The Documentation-Handover reconciliation-transparency rubric must give
    HISTORICAL_UNRECONSTRUCTABLE-with-note the same credit as PARTIALLY_RECONCILED-with-note
    (0.5x), and strictly less than FULLY_RECONCILED (1.0x). Must not silently become 100."""
    methodology = _fixture_methodology()
    evidence = _all_gates_pass_evidence()

    partial_report = compute_report(
        methodology, _fixture_registry(items=[], reconciliation_status="PARTIALLY_RECONCILED"),
        tmp_path, evidence,
    )
    historical_report = compute_report(
        methodology, _fixture_registry(items=[], reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE"),
        tmp_path, evidence,
    )
    full_report = compute_report(
        methodology, _fixture_registry(items=[], reconciliation_status="FULLY_RECONCILED"),
        tmp_path, evidence,
    )

    partial_doc = partial_report["category_scores"]["Documentation-Handover"]["final_score"]
    historical_doc = historical_report["category_scores"]["Documentation-Handover"]["final_score"]
    full_doc = full_report["category_scores"]["Documentation-Handover"]["final_score"]

    assert historical_doc == partial_doc
    assert historical_doc < full_doc
    assert full_doc == pytest.approx(100.0)


def test_historical_unreconstructable_without_note_gets_zero_reconciliation_credit(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[], reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE")
    registry["reconciliation_note"] = ""  # no documented note
    evidence = _all_gates_pass_evidence()
    report = compute_report(methodology, registry, tmp_path, evidence)
    doc_rubric = next(
        r for r in report["category_scores"]["Documentation-Handover"]["rubric_contributions"]
        if r["name"] == "registry_reconciliation_transparency"
    )
    assert doc_rubric["points_awarded"] == 0.0


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


# ---------------------------------------------------------------------------
# Full score-trace completeness tests
# ---------------------------------------------------------------------------

EXPECTED_CATEGORIES = {
    "Code Quality", "Test Assurance", "Security", "CI-Release",
    "Operations", "Documentation-Handover", "Maintainability",
}


def test_all_seven_categories_present(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    assert set(report["category_scores"].keys()) == EXPECTED_CATEGORIES


def test_all_category_trace_fields_present(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[
        {"id": "TD-CAND-001", "status": "OPEN", "severity": "P2", "category": "Code Quality"},
    ])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    required_fields = {
        "final_score", "gate_component", "rubric_component", "raw_before_penalty",
        "debt_penalty", "unverified_count", "gate_contributions", "rubric_contributions",
        "missing_evidence", "debt_penalty_breakdown", "debt_penalty_raw_total",
        "debt_penalty_cap_applied", "ceiling", "gates", "rubric_trace",
    }
    for name, cs in report["category_scores"].items():
        missing = required_fields - set(cs.keys())
        assert not missing, f"{name} is missing trace fields: {missing}"
        assert cs["ceiling"] == {"applies": False}, "no per-category ceiling exists in methodology v1 -- must report honestly"


def test_debt_penalty_breakdown_sums_to_category_penalty(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[
        {"id": "TD-CAND-001", "status": "OPEN", "severity": "P2", "category": "Code Quality"},
        {"id": "TD-CAND-002", "status": "OPEN", "severity": "P1", "category": "Code Quality"},
    ])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    cq = report["category_scores"]["Code Quality"]
    breakdown_sum = sum(item["penalty_points"] for item in cq["debt_penalty_breakdown"])
    assert breakdown_sum == cq["debt_penalty_raw_total"]
    assert min(breakdown_sum, methodology["debt_penalty_policy"]["penalty_cap_per_category"]) == cq["debt_penalty"]
    assert len(cq["debt_penalty_breakdown"]) == 2
    ids = {item["debt_id"] for item in cq["debt_penalty_breakdown"]}
    assert ids == {"TD-CAND-001", "TD-CAND-002"}


def test_debt_penalty_breakdown_reports_severity_and_mapping_status(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[
        {"id": "TD-CAND-001", "status": "OPEN", "severity": "P2", "category": "Code Quality"},
        {"id": "TD-CAND-002", "status": "OPEN", "severity": "TOTALLY_MADE_UP", "category": "Code Quality"},
    ])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    breakdown = {item["debt_id"]: item for item in report["category_scores"]["Code Quality"]["debt_penalty_breakdown"]}
    assert breakdown["TD-CAND-001"]["mapping_status"] == "DIRECT_MATCH"
    assert breakdown["TD-CAND-002"]["mapping_status"] == "FALLBACK_UNCLASSIFIED_DEFAULT"
    assert breakdown["TD-CAND-002"]["penalty_points"] == methodology["debt_penalty_policy"]["severity_weights"]["UNCLASSIFIED"]


def test_debt_penalty_cap_applied_flag(tmp_path):
    methodology = _fixture_methodology()
    # 6 P0 items at weight 40 each = 240 raw, capped at 30.
    registry = _fixture_registry(items=[
        {"id": f"TD-CAND-{i}", "status": "OPEN", "severity": "P0", "category": "Code Quality"}
        for i in range(6)
    ])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    cq = report["category_scores"]["Code Quality"]
    assert cq["debt_penalty_raw_total"] == 240
    assert cq["debt_penalty_cap_applied"] is True
    assert cq["debt_penalty"] == 30


def test_gate_contributions_sum_to_gate_component(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    evidence = {"gate_a": True, "gate_b": True, "gate_c": True, "gate_d": True, "gate_e": True, "gate_f": True}
    report = compute_report(methodology, registry, tmp_path, evidence)
    cq = report["category_scores"]["Code Quality"]
    contributions_sum = sum(g["points_awarded"] for g in cq["gate_contributions"])
    assert round(contributions_sum, 2) == cq["gate_component"]


def test_missing_evidence_trace_lists_unverified_gates(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, evidence={})
    cq = report["category_scores"]["Code Quality"]
    assert len(cq["missing_evidence"]) == 1
    assert cq["missing_evidence"][0]["name"] == "gate_a"
    assert cq["missing_evidence"][0]["kind"] == "GATE"


def test_live_and_transfer_contributions_reproduce_raw_sum(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    live_sum = sum(c["contribution"] for c in report["LIVE_READINESS"]["contributions"])
    assert round(live_sum, 2) == round(report["LIVE_READINESS"]["raw"], 2)
    transfer_sum = sum(c["contribution"] for c in report["TRANSFERABILITY"]["contributions"])
    assert round(transfer_sum, 2) == round(report["TRANSFERABILITY"]["raw"], 2)
    # Every contribution must show its own weight and the category score it was derived from.
    for contribution in report["LIVE_READINESS"]["contributions"]:
        expected = report["category_scores"][contribution["category"]]["final_score"] * contribution["weight"]
        assert round(contribution["contribution"], 4) == round(expected, 4)


def test_composite_weight_sums_equal_one():
    methodology = json.loads(CANONICAL_METHODOLOGY_PATH.read_text(encoding="utf-8"))
    live_sum = sum(methodology["composites"]["LIVE_READINESS"]["weights"].values())
    transfer_sum = sum(methodology["composites"]["TRANSFERABILITY"]["weights"].values())
    assert abs(live_sum - 1.0) < 1e-6
    assert abs(transfer_sum - 1.0) < 1e-6


def test_rounding_deterministic_across_repeated_calls():
    for value in (67.5, 67.4999, 67.50001, 88.5, 89.5, 100.0, 0.0):
        first = _round_half_up(value)
        second = _round_half_up(value)
        assert first == second


def test_round_half_up_diverges_from_bankers_rounding_at_known_boundary():
    """Proves the implementation is NOT Python's built-in round() (banker's rounding)."""
    assert round(88.5) == 88  # Python's default: rounds to even
    assert _round_half_up(88.5) == 89  # methodology's rule: always rounds the tie up


# ---------------------------------------------------------------------------
# Portability tests
# ---------------------------------------------------------------------------


def test_no_hardcoded_machine_specific_executable_path_in_methodology_config():
    """Anti-regression: no GATE DEFINITION (the executable part of the config)
    may hardcode an absolute, machine-specific interpreter path again. Prose
    fields (design_note, interpreter_resolution.note, etc.) are allowed to
    reference the historical hardcoded path when explaining why the fix was
    made -- only gates[] entries are checked, since those are what actually
    get executed."""
    methodology = json.loads(CANONICAL_METHODOLOGY_PATH.read_text(encoding="utf-8"))
    for category_name, category_config in methodology["categories"].items():
        for gate in category_config.get("gates", []):
            gate_json = json.dumps(gate)
            assert "C:\\" not in gate_json and "c:\\\\" not in gate_json.lower(), (
                f"{category_name}.{gate['name']} embeds a hardcoded absolute path in its gate definition: {gate_json}"
            )
            command = gate.get("command", "")
            assert "C:\\" not in command, (
                f"{category_name}.{gate['name']} has a hardcoded absolute path in a legacy command string"
            )


def test_no_hardcoded_machine_specific_path_in_calculator_source():
    source = Path("scripts/quality/bys360_score_reconcile_v1.py").read_text(encoding="utf-8")
    assert "C:\\bys360" not in source and "C:\\\\bys360" not in source


def test_resolve_python_default_uses_sys_executable(monkeypatch):
    monkeypatch.delenv("BYS360_QUALITY_PYTHON", raising=False)
    path, source = resolve_python(None)
    assert path == sys.executable
    assert source == "default-sys.executable"


def test_resolve_python_explicit_override_honored(tmp_path):
    fake_python = tmp_path / "fake_python.exe"
    fake_python.write_text("", encoding="utf-8")
    path, source = resolve_python(str(fake_python))
    assert path == str(fake_python)
    assert source == "explicit"


def test_resolve_python_env_var_honored(monkeypatch, tmp_path):
    fake_python = tmp_path / "env_python.exe"
    fake_python.write_text("", encoding="utf-8")
    monkeypatch.setenv("BYS360_QUALITY_PYTHON", str(fake_python))
    path, source = resolve_python(None)
    assert path == str(fake_python)
    assert source == "env"


def test_resolve_python_explicit_takes_priority_over_env(monkeypatch, tmp_path):
    env_python = tmp_path / "env_python.exe"
    env_python.write_text("", encoding="utf-8")
    explicit_python = tmp_path / "explicit_python.exe"
    explicit_python.write_text("", encoding="utf-8")
    monkeypatch.setenv("BYS360_QUALITY_PYTHON", str(env_python))
    path, source = resolve_python(str(explicit_python))
    assert path == str(explicit_python)
    assert source == "explicit"


def test_resolve_python_rejects_nonexistent_explicit_path():
    with pytest.raises(SystemExit):
        resolve_python(r"C:\definitely\does\not\exist\python.exe")


def test_build_argv_produces_argument_list_not_shell_string():
    gate = {"kind": "python_module", "module": "ruff", "args": ["check", "app"]}
    argv = _build_argv(gate, "/some/python")
    assert isinstance(argv, list)
    assert argv == ["/some/python", "-m", "ruff", "check", "app"]

    gate_script = {"kind": "python_script", "script": "scripts/quality/x.py", "args": ["--root", "."]}
    argv_script = _build_argv(gate_script, "/some/python")
    assert argv_script == ["/some/python", "scripts/quality/x.py", "--root", "."]


def test_wrong_tool_version_produces_version_mismatch_not_silent_pass(tmp_path, monkeypatch):
    """Simulates a gate whose declared expected_version does not match the
    tool actually installed -- must never be silently scored as PASS."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    def fake_check_version(python_path, module, expected, cwd):
        return False, "0.15.21", None  # simulates the real off-pin shared-venv ruff

    monkeypatch.setattr(calc, "_check_tool_version", fake_check_version)

    methodology = _fixture_methodology()
    methodology["categories"]["Code Quality"]["gates"] = [
        {"name": "ruff_full_select", "kind": "python_module", "module": "ruff", "expected_version": "0.16.0",
         "args": ["check"], "pass_rule": "exit_code_0"},
    ]
    registry = _fixture_registry(items=[])
    report = calc.compute_report(methodology, registry, tmp_path, evidence={}, python_path=sys.executable, python_source="explicit")
    cq = report["category_scores"]["Code Quality"]
    assert cq["gates"][0]["status"] == "VERSION_MISMATCH"
    assert cq["gates"][0]["status"] != "PASS"
    assert cq["gate_component"] == 0.0  # must not receive PASS credit
    assert report["fully_verified"] is False
    assert any(item["name"] == "ruff_full_select" for item in cq["missing_evidence"])


def test_version_matched_tool_scores_as_pass(tmp_path, monkeypatch):
    import scripts.quality.bys360_score_reconcile_v1 as calc

    def fake_check_version(python_path, module, expected, cwd):
        return True, expected, None

    def fake_run_argv(argv, cwd):
        return 0, "All checks passed!", None

    monkeypatch.setattr(calc, "_check_tool_version", fake_check_version)
    monkeypatch.setattr(calc, "_run_argv", fake_run_argv)

    methodology = _fixture_methodology()
    methodology["categories"]["Code Quality"]["gates"] = [
        {"name": "ruff_full_select", "kind": "python_module", "module": "ruff", "expected_version": "0.16.0",
         "args": ["check"], "pass_rule": "exit_code_0"},
    ]
    registry = _fixture_registry(items=[])
    report = calc.compute_report(methodology, registry, tmp_path, evidence={}, python_path=sys.executable, python_source="explicit")
    cq = report["category_scores"]["Code Quality"]
    assert cq["gates"][0]["status"] == "PASS"


def test_report_exposes_which_interpreter_was_used(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, evidence={}, python_path="/explicit/python", python_source="explicit")
    assert report["interpreter"]["path"] == "/explicit/python"
    assert report["interpreter"]["source"] == "explicit"


def test_pinned_tool_versions_declared_for_ruff_and_mypy_gates():
    methodology = json.loads(CANONICAL_METHODOLOGY_PATH.read_text(encoding="utf-8"))
    for category_config in methodology["categories"].values():
        for gate in category_config.get("gates", []):
            if gate.get("kind") == "python_module" and gate.get("module") in ("ruff", "mypy"):
                assert "expected_version" in gate, f"{gate['name']} must declare expected_version to avoid silently trusting a wrong-version tool"


def test_no_shell_true_string_commands_remain_in_calculator_run_path():
    """The old shell=True string-command path (_run_command) must no longer be
    the primary execution mechanism -- structured gates use _run_argv with
    shell=False and an argument list."""
    source = Path("scripts/quality/bys360_score_reconcile_v1.py").read_text(encoding="utf-8")
    assert re.search(r"_run_argv\(.*shell\s*=\s*False", source, re.DOTALL) or "shell=False" in source


# ---------------------------------------------------------------------------
# Canonical evidence integration (report-level, using this file's full
# 7-category fixture rather than the smaller fixture in
# test_bys360_canonical_evidence_resolution.py's own unit tests).
# ---------------------------------------------------------------------------

def test_report_backward_compatible_without_manifest_or_scored_commit(tmp_path):
    """Calling compute_report() the old way (no canonical_manifest/scored_commit
    args) must still work and must still be internally consistent -- canonical
    and local scores must be identical, since there is no manifest to diverge
    from local execution."""
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    assert report["scored_commit"] == "UNKNOWN_COMMIT"
    for cs in report["category_scores"].values():
        assert cs["final_score"] == cs["local_final_score_NON_CANONICAL"]
    assert report["LIVE_READINESS"]["final"] == report["LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL"]["LIVE_READINESS_local"]


def test_matching_manifest_evidence_changes_canonical_but_not_local_score(tmp_path):
    from scripts.quality.bys360_score_reconcile_v1 import compute_report as _compute_report

    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    scored_commit = "c" * 40
    # Locally, gate_a fails (not supplied -> UNKNOWN); remotely, it is verified PASS for this exact commit.
    evidence = {"gate_b": True, "gate_c": True, "gate_d": True, "gate_e": True, "gate_f": True}
    manifest = {"gates": [{
        "id": "gate_a", "commit_sha": scored_commit, "status": "PASS",
        "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF", "source": "test",
    }]}
    report_no_manifest = _compute_report(methodology, registry, tmp_path, evidence, scored_commit=scored_commit)
    report_with_manifest = _compute_report(methodology, registry, tmp_path, evidence, canonical_manifest=manifest, scored_commit=scored_commit)

    assert report_no_manifest["category_scores"]["Code Quality"]["final_score"] < report_with_manifest["category_scores"]["Code Quality"]["final_score"]
    # Local (NON-CANONICAL) score must be unaffected by the manifest either way.
    assert report_no_manifest["category_scores"]["Code Quality"]["local_final_score_NON_CANONICAL"] == report_with_manifest["category_scores"]["Code Quality"]["local_final_score_NON_CANONICAL"]


def test_no_double_credit_points_awarded_never_exceeds_points_possible(tmp_path):
    from scripts.quality.bys360_score_reconcile_v1 import compute_report as _compute_report

    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[])
    scored_commit = "d" * 40
    evidence = _all_gates_pass_evidence()  # locally PASS
    manifest = {"gates": [{
        "id": "gate_a", "commit_sha": scored_commit, "status": "PASS",
        "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF", "source": "test",
    }]}  # ALSO remotely PASS -- must not double-award
    report = _compute_report(methodology, registry, tmp_path, evidence, canonical_manifest=manifest, scored_commit=scored_commit)
    for gc in report["category_scores"]["Code Quality"]["gate_contributions"]:
        assert gc["points_awarded"] <= gc["points_possible"]


def test_resolve_scored_commit_explicit_override_honored(tmp_path):
    from scripts.quality.bys360_score_reconcile_v1 import resolve_scored_commit
    sha, source = resolve_scored_commit("e" * 40, tmp_path)
    assert sha == "e" * 40
    assert source == "explicit"


def test_resolve_scored_commit_auto_detects_real_git_head():
    from scripts.quality.bys360_score_reconcile_v1 import resolve_scored_commit
    sha, source = resolve_scored_commit(None, REPO_ROOT)
    assert re.fullmatch(r"[0-9a-f]{40}", sha)
    assert source == "git-rev-parse-HEAD"


def test_resolve_scored_commit_falls_back_when_not_a_git_repo(tmp_path):
    from scripts.quality.bys360_score_reconcile_v1 import resolve_scored_commit
    sha, source = resolve_scored_commit(None, tmp_path)
    assert sha == "UNKNOWN_COMMIT"
    assert source == "git-unavailable"


def test_no_weight_ceiling_penalty_rounding_diff_from_pre_wave_values():
    """Freeze check: this wave must not have altered any scoring-math value in
    the real methodology config -- only added the evidence_precedence_policy
    metadata block and structural gate declarations from the prior wave."""
    methodology = json.loads(CANONICAL_METHODOLOGY_PATH.read_text(encoding="utf-8"))
    assert methodology["composites"]["LIVE_READINESS"]["weights"] == {
        "Security": 0.22, "Test Assurance": 0.21, "CI-Release": 0.21, "Operations": 0.20,
        "Code Quality": 0.10, "Maintainability": 0.03, "Documentation-Handover": 0.03,
    }
    assert methodology["composites"]["TRANSFERABILITY"]["weights"] == {
        "Documentation-Handover": 0.22, "Maintainability": 0.22, "Test Assurance": 0.18,
        "Code Quality": 0.15, "CI-Release": 0.10, "Operations": 0.06, "Security": 0.07,
    }
    assert methodology["debt_penalty_policy"]["severity_weights"] == {"P0": 40, "P1": 20, "P2": 8, "P3": 3, "UNCLASSIFIED": 5}
    assert methodology["debt_penalty_policy"]["penalty_cap_per_category"] == 30
    assert methodology["evidence_completeness_ceiling"]["value"] == 89
    assert methodology["rounding"] == {"category_precision": 2, "composite_rule": "round_half_up", "composite_precision": 0}


# ---------------------------------------------------------------------------
# FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1 (approved 2026-08-22), binding
# hardened 2026-08-23: reconciliation_ceiling_waiver_decision. Orthogonal to
# reconciliation_status (stays HISTORICAL_UNRECONSTRUCTABLE, never rewritten)
# and to the registry_reconciliation_transparency rubric (Documentation-
# Handover credit must be provably unaffected). approval_baseline_commit is
# documentary/anchoring only -- it is never compared to scored_commit (that
# conflation caused a self-SHA circularity and a real evidence-substitution
# gap in the pre-hardening design). registry_commit_verified is the actual
# fix: an independently-resolved boolean (real git verification lives in
# _registry_matches_scored_commit_tree(), tested directly below; here it is
# always explicitly injected, exactly like scored_commit/canonical_manifest
# already are, keeping compute_report() itself git-free and fast to test).
# Every scenario must fail closed unless ALL eligibility terms hold
# simultaneously.
# ---------------------------------------------------------------------------

WAIVER_TARGET_COMMIT = "f" * 40


def _historical_unreconstructable_registry(**overrides):
    registry = _fixture_registry(items=[], reconciliation_status="HISTORICAL_UNRECONSTRUCTABLE")
    registry["legacy_ledger"] = {"P0": 0, "P1": 0, "P2": 17, "P3": 21, "TOTAL": 38}
    registry["reconciliation_governance_decision"] = {
        "decision_id": GOV_LEGACY_001_DECISION_ID,
        "decision_status": "APPROVED",
        "preserved_legacy_total": 38,
        "preserved_legacy_priority_split": {"P0": 0, "P1": 0, "P2": 17, "P3": 21},
    }
    registry.update(overrides)
    return registry


def _valid_waiver(**overrides):
    decision = {
        "decision_id": GOV_CEILING_WAIVER_001_DECISION_ID,
        "decision_status": "APPROVED",
        "approval_baseline_commit": WAIVER_TARGET_COMMIT,
        "preserved_legacy_total": 38,
        "preserved_legacy_priority_split": {"P0": 0, "P1": 0, "P2": 17, "P3": 21},
    }
    decision.update(overrides)
    return decision


def _score100_pass_manifest(commit_sha=WAIVER_TARGET_COMMIT):
    return {"gates": [{
        "id": SCORE100_WORKFLOW_GATE_ID, "commit_sha": commit_sha, "status": "PASS",
        "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF",
    }]}


def _fully_eligible_report(tmp_path, **registry_overrides):
    methodology = _fixture_methodology()
    overrides = {"reconciliation_ceiling_waiver_decision": _valid_waiver()}
    overrides.update(registry_overrides)
    registry = _historical_unreconstructable_registry(**overrides)
    return compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )


def test_ceiling_waiver_active_when_fully_eligible(tmp_path):
    """POSITIVE: every eligibility term satisfied -- ceiling is waived."""
    report = _fully_eligible_report(tmp_path)
    assert report["fully_verified"] is True
    assert report["registry_structurally_valid"] is True
    assert report["registry_commit_verified"] is True
    assert report["reconciliation_ceiling_waiver_active"] is True
    assert report["evidence_completeness_ceiling_applied"] is False


def test_ceiling_waiver_does_not_mutate_registry_or_legacy_ledger(tmp_path):
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry(reconciliation_ceiling_waiver_decision=_valid_waiver())
    registry_before = json.loads(json.dumps(registry))  # deep copy
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    assert report["reconciliation_ceiling_waiver_active"] is True
    assert registry == registry_before
    assert registry["reconciliation_status"] == "HISTORICAL_UNRECONSTRUCTABLE"
    assert registry["legacy_ledger"]["TOTAL"] == 38


def test_ceiling_waiver_active_does_not_change_documentation_handover(tmp_path):
    """Anti-gaming (Section 8 of the ratification report): an active waiver must NOT
    raise Documentation-Handover -- the underlying historical gap is still real."""
    methodology = _fixture_methodology()
    registry_no_waiver = _historical_unreconstructable_registry()
    registry_with_waiver = _historical_unreconstructable_registry(
        reconciliation_ceiling_waiver_decision=_valid_waiver(),
    )
    evidence = _all_gates_pass_evidence()
    report_no_waiver = compute_report(
        methodology, registry_no_waiver, tmp_path, evidence,
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    report_with_waiver = compute_report(
        methodology, registry_with_waiver, tmp_path, evidence,
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    assert report_no_waiver["reconciliation_ceiling_waiver_active"] is False
    assert report_with_waiver["reconciliation_ceiling_waiver_active"] is True
    doc_no_waiver = report_no_waiver["category_scores"]["Documentation-Handover"]["final_score"]
    doc_with_waiver = report_with_waiver["category_scores"]["Documentation-Handover"]["final_score"]
    assert doc_with_waiver == doc_no_waiver


def test_ceiling_waiver_blocked_when_decision_missing(tmp_path):
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry()  # no reconciliation_ceiling_waiver_decision at all
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_decision_status_not_approved(tmp_path):
    report = _fully_eligible_report(tmp_path, reconciliation_ceiling_waiver_decision=_valid_waiver(decision_status="REVOKED"))
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_registry_content_not_verified_against_scored_commit(tmp_path):
    """CRITICAL, THE central hardening property: a well-formed, approved, otherwise
    fully-eligible waiver decision must NOT activate when registry_commit_verified is
    False -- i.e. when nothing has cryptographically confirmed that the registry
    content being scored genuinely came from scored_commit's own git tree. This is
    exactly the case a real (non-injected) run would produce if someone tried the
    parent-scored-child-registry substitution: genuine Score100/Quality evidence for
    a real, already-attested commit, combined with a DIFFERENT commit's registry
    content, both merely claimed under the same scored_commit label."""
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry(reconciliation_ceiling_waiver_decision=_valid_waiver())
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=False,
    )
    assert report["fully_verified"] is True
    assert report["registry_structurally_valid"] is True
    assert report["registry_commit_verified"] is False
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_registry_commit_verified_defaults_to_false():
    """No truthy default anywhere: a caller that forgets to pass
    registry_commit_verified must fail closed, never silently activate a waiver."""
    import inspect
    sig = inspect.signature(compute_report)
    assert sig.parameters["registry_commit_verified"].default is False


def test_ceiling_waiver_blocked_when_quality_evidence_incomplete(tmp_path):
    """fully_verified=False (some gate UNKNOWN) must block the waiver, even with an
    otherwise fully valid, approved, verified decision."""
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry(reconciliation_ceiling_waiver_decision=_valid_waiver())
    report = compute_report(
        methodology, registry, tmp_path, evidence={},  # nothing supplied -> UNKNOWN
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    assert report["fully_verified"] is False
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_score100_evidence_missing(tmp_path):
    """Score100 must be an independent, real requirement -- never inferred from
    Quality gates passing."""
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry(reconciliation_ceiling_waiver_decision=_valid_waiver())
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest={"gates": []},  # Quality-style gates all pass, but no Score100 entry at all
        scored_commit=WAIVER_TARGET_COMMIT, registry_commit_verified=True,
    )
    assert report["fully_verified"] is True
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_score100_evidence_is_fail(tmp_path):
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry(reconciliation_ceiling_waiver_decision=_valid_waiver())
    manifest = {"gates": [{
        "id": SCORE100_WORKFLOW_GATE_ID, "commit_sha": WAIVER_TARGET_COMMIT, "status": "FAIL",
        "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF",
    }]}
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=manifest, scored_commit=WAIVER_TARGET_COMMIT, registry_commit_verified=True,
    )
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_active_debt_present(tmp_path):
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry(
        items=[{"id": "TD-CAND-999", "status": "OPEN", "severity": "P2", "category": "Code Quality"}],
        reconciliation_ceiling_waiver_decision=_valid_waiver(),
    )
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_registry_gate_validation_fails(tmp_path):
    """Any unrelated registry-validation failure (e.g. drifted legacy total) must
    also block the waiver -- validate_registry().ok is a blanket requirement."""
    report = _fully_eligible_report(tmp_path, reconciliation_ceiling_waiver_decision=_valid_waiver(preserved_legacy_total=0))
    assert report["registry_structurally_valid"] is False
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_ceiling_waiver_blocked_when_reconciliation_status_not_historical_unreconstructable(tmp_path):
    methodology = _fixture_methodology()
    registry = _fixture_registry(items=[], reconciliation_status="PARTIALLY_RECONCILED")
    registry["reconciliation_ceiling_waiver_decision"] = _valid_waiver()
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
        registry_commit_verified=True,
    )
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_fully_reconciled_path_blocked_when_registry_structurally_invalid(tmp_path):
    """SAFETY FIX: the pre-existing FULLY_RECONCILED path must also be gated by
    registry validation, not just the new waiver path. A registry claiming
    FULLY_RECONCILED but failing validate_registry() must not lift the ceiling."""
    methodology = _fixture_methodology()
    # unmapped_legacy_open_count != 0 while claiming FULLY_RECONCILED -> validate_registry() fails.
    registry = _fixture_registry(items=[], reconciliation_status="FULLY_RECONCILED")
    registry["legacy_ledger"] = {"P0": 0, "P1": 0, "P2": 17, "P3": 21, "TOTAL": 38}
    report = compute_report(
        methodology, registry, tmp_path, _all_gates_pass_evidence(),
        canonical_manifest=_score100_pass_manifest(), scored_commit=WAIVER_TARGET_COMMIT,
    )
    assert report["registry_structurally_valid"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


def test_fully_reconciled_path_unaffected_when_registry_structurally_valid(tmp_path):
    """The pre-existing behavior for a genuinely valid FULLY_RECONCILED registry
    (no legacy_ledger at all, matching the existing test_no_ceiling_when_fully_verified_
    and_fully_reconciled fixture exactly) must be completely unaffected by the safety fix."""
    methodology = _fixture_methodology()
    registry_full = _fixture_registry(items=[], reconciliation_status="FULLY_RECONCILED")
    report = compute_report(methodology, registry_full, tmp_path, _all_gates_pass_evidence())
    assert report["registry_structurally_valid"] is True
    assert report["evidence_completeness_ceiling_applied"] is False


def test_old_registry_without_waiver_field_reproduces_pre_policy_behavior(tmp_path):
    """Backward compatibility: a registry with the waiver field genuinely absent
    (not null, not present) must behave identically to before this policy existed --
    exactly the existing test_ceiling_still_applies_for_historical_unreconstructable
    scenario, re-asserted here alongside the new fields."""
    methodology = _fixture_methodology()
    registry = _historical_unreconstructable_registry()
    assert "reconciliation_ceiling_waiver_decision" not in registry
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    assert report["fully_verified"] is True
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True
    assert report["LIVE_READINESS"]["ceiling_applied_value"] <= 89
    assert report["TRANSFERABILITY"]["ceiling_applied_value"] <= 89


def test_real_registry_ceiling_waiver_decision_present_but_not_canonically_active(tmp_path):
    """WAIVER_ACTIVATION_APPROVED (2026-08-23): the real, committed registry now has a
    human-approved reconciliation_ceiling_waiver_decision (BYS360-GOV-CEILING-WAIVER-001,
    bound to approval_baseline_commit fe984cf). DECISION_RECORD_PRESENT=YES is proven
    here -- but the ceiling still does NOT canonically waive without this specific
    scoring run's own fresh, commit-bound registry_commit_verified/Quality/Score100
    evidence, which this call deliberately supplies none of (registry_commit_verified
    defaults False, no canonical_manifest, no real scored_commit) -- exactly the state
    every commit is in until it earns its own fresh remote attestation."""
    registry = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    decision = registry.get("reconciliation_ceiling_waiver_decision")
    assert decision is not None
    assert decision["decision_status"] == "APPROVED"
    methodology = _fixture_methodology()
    report = compute_report(methodology, registry, tmp_path, _all_gates_pass_evidence())
    assert report["registry_commit_verified"] is False
    assert report["reconciliation_ceiling_waiver_active"] is False
    assert report["evidence_completeness_ceiling_applied"] is True


# ---------------------------------------------------------------------------
# WAIVER_BINDING_HARDENING (2026-08-23): _registry_matches_scored_commit_tree(),
# tested against a REAL, disposable git repository (not mocked) -- this is the
# actual fix for the parent-scored-child-registry substitution gap: genuine,
# unforged Score100/Quality evidence for one real commit could previously be
# combined with a DIFFERENT commit's registry content, both merely asserted to
# share one scored_commit label.
# ---------------------------------------------------------------------------


def _run_git(cwd, *args):
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def test_registry_matches_scored_commit_tree_accepts_own_content(tmp_path):
    """Legitimate case: scoring a commit while reading THAT SAME commit's own
    registry content must verify True."""
    (tmp_path / "config").mkdir()
    registry_relpath = "config/registry.json"
    _run_git(tmp_path, "init", "-q")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test")

    baseline_registry = {"reconciliation_status": "HISTORICAL_UNRECONSTRUCTABLE", "items": []}
    (tmp_path / registry_relpath).write_text(json.dumps(baseline_registry), encoding="utf-8")
    _run_git(tmp_path, "add", registry_relpath)
    _run_git(tmp_path, "commit", "-q", "-m", "baseline")
    baseline_sha = _run_git(tmp_path, "rev-parse", "HEAD")

    assert _registry_matches_scored_commit_tree(tmp_path, registry_relpath, baseline_sha, baseline_registry) is True


def test_registry_matches_scored_commit_tree_rejects_parent_scored_child_registry_substitution(tmp_path):
    """CRITICAL: the exact exploit this hardening closes. A child commit E adds a
    ceiling-waiver decision to the registry -- nothing else. Someone tries to score
    the already-attested PARENT (baseline_sha) while actually reading E's registry
    content (the one that activates the waiver). Must be rejected, even though
    baseline_sha is a completely real, legitimately-existing commit and nothing here
    is forged -- only mismatched."""
    (tmp_path / "config").mkdir()
    registry_relpath = "config/registry.json"
    _run_git(tmp_path, "init", "-q")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test")

    baseline_registry: dict[str, Any] = {"reconciliation_status": "HISTORICAL_UNRECONSTRUCTABLE", "items": []}
    (tmp_path / registry_relpath).write_text(json.dumps(baseline_registry), encoding="utf-8")
    _run_git(tmp_path, "add", registry_relpath)
    _run_git(tmp_path, "commit", "-q", "-m", "baseline")
    baseline_sha = _run_git(tmp_path, "rev-parse", "HEAD")

    child_registry: dict[str, Any] = dict(baseline_registry)
    child_registry["reconciliation_ceiling_waiver_decision"] = {
        "decision_status": "APPROVED", "approval_baseline_commit": baseline_sha,
    }
    (tmp_path / registry_relpath).write_text(json.dumps(child_registry), encoding="utf-8")
    _run_git(tmp_path, "add", registry_relpath)
    _run_git(tmp_path, "commit", "-q", "-m", "add waiver decision")
    child_sha = _run_git(tmp_path, "rev-parse", "HEAD")

    # Each commit verifies True against its own genuine content.
    assert _registry_matches_scored_commit_tree(tmp_path, registry_relpath, baseline_sha, baseline_registry) is True
    assert _registry_matches_scored_commit_tree(tmp_path, registry_relpath, child_sha, child_registry) is True

    # THE ATTACK: claim scored_commit=baseline_sha (real, already-attested) while the
    # registry content actually being scored is the CHILD's (the one with the waiver).
    assert _registry_matches_scored_commit_tree(tmp_path, registry_relpath, baseline_sha, child_registry) is False
    # And the reverse direction also must not silently pass.
    assert _registry_matches_scored_commit_tree(tmp_path, registry_relpath, child_sha, baseline_registry) is False


def test_registry_matches_scored_commit_tree_fails_closed_when_not_a_git_repo(tmp_path):
    result = _registry_matches_scored_commit_tree(tmp_path, "config/registry.json", "a" * 40, {})
    assert result is False


def test_registry_matches_scored_commit_tree_fails_closed_for_malformed_commit_sha():
    result = _registry_matches_scored_commit_tree(REPO_ROOT, "config/quality/bys360_technical_debt_registry.json", "not-a-real-sha", {})
    assert result is False


def test_registry_matches_scored_commit_tree_fails_closed_for_missing_path(tmp_path):
    _run_git(tmp_path, "init", "-q")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    (tmp_path / "placeholder.txt").write_text("x", encoding="utf-8")
    _run_git(tmp_path, "config", "user.name", "Test")
    _run_git(tmp_path, "add", "placeholder.txt")
    _run_git(tmp_path, "commit", "-q", "-m", "no registry file here")
    sha = _run_git(tmp_path, "rev-parse", "HEAD")
    result = _registry_matches_scored_commit_tree(tmp_path, "config/registry.json", sha, {})
    assert result is False


def test_registry_matches_scored_commit_tree_real_repo_17be109(tmp_path):
    """Sanity check against this repository's own real history: 17be109's actual
    committed registry content must verify True when scored as 17be109 itself."""
    sha = "17be109d66dfb5f91554b28e7573f01c1572c73b"
    real_registry_at_sha = json.loads(_run_git(REPO_ROOT, "show", f"{sha}:config/quality/bys360_technical_debt_registry.json"))
    assert _registry_matches_scored_commit_tree(
        REPO_ROOT, "config/quality/bys360_technical_debt_registry.json", sha, real_registry_at_sha,
    ) is True
    # Content-based, not commit-label-based: even the exact SHA that genuinely
    # produced this content must reject a TAMPERED copy of it (proves the check
    # verifies actual content, not just "does this commit exist").
    tampered = dict(real_registry_at_sha)
    tampered["reconciliation_ceiling_waiver_decision"] = {"decision_status": "APPROVED"}
    assert _registry_matches_scored_commit_tree(
        REPO_ROOT, "config/quality/bys360_technical_debt_registry.json", sha, tampered,
    ) is False
