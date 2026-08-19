"""Tests for scripts/quality/bys360_score_reconcile_v1.py.

These tests avoid invoking real subprocess gates (ruff/mypy/etc.) so they
stay fast and deterministic: every gate in the fixture methodology uses
pass_rule="exit_code_0_or_supplied_evidence" with results supplied via the
`evidence` dict, exactly like the real script's --evidence mechanism.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from scripts.quality.bys360_score_reconcile_v1 import (
    LEGACY_SNAPSHOT,
    _build_argv,
    _round_half_up,
    compute_report,
    resolve_python,
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
