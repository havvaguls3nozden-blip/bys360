"""Tests for the commit-bound canonical evidence resolver added to
scripts/quality/bys360_score_reconcile_v1.py.

Covers: resolve_evidence() precedence tiers, validate_evidence_manifest()
schema/conflict checks, and cross-environment reproducibility of
CANONICAL_PROJECT_SCORE through compute_report() -- the key acceptance
property this wave exists to prove: the same scored commit with the same
canonical manifest must produce an identical canonical score regardless of
this machine's own local tool versions, while LOCAL_ENVIRONMENT_DIAGNOSTICS
are allowed (expected) to differ.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.quality.bys360_score_reconcile_v1 import (
    compute_report,
    resolve_evidence,
    resolve_evidence_file,
    validate_evidence_manifest,
)

pytestmark = pytest.mark.ci_safe

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_EVIDENCE_EXAMPLE_PATH = REPO_ROOT / "config" / "quality" / "bys360_canonical_evidence.example.json"
OLD_LIVE_EVIDENCE_PATH = REPO_ROOT / "config" / "quality" / "bys360_canonical_evidence.json"

COMMIT_AAA = "a" * 40
COMMIT_BBB = "b" * 40


def _manifest(*entries):
    return {"gates": list(entries)}


def _entry(gate_id, commit_sha, status, evidence_type="REMOTE_CI_VERIFIED", provenance="USER_SUPPLIED_REMOTE_PROOF"):
    return {
        "id": gate_id, "commit_sha": commit_sha, "status": status,
        "evidence_type": evidence_type, "provenance": provenance, "source": "test_source",
    }


# ---------------------------------------------------------------------------
# resolve_evidence(): precedence tiers
# ---------------------------------------------------------------------------

def test_exact_commit_match_remote_pass_wins_over_local_version_mismatch():
    manifest = _manifest(_entry("ruff_full_select", COMMIT_AAA, "PASS"))
    r = resolve_evidence("ruff_full_select", COMMIT_AAA, manifest, "VERSION_MISMATCH", "wrong ruff version")
    assert r["canonical_status"] == "PASS"
    assert r["canonical_source"] == "REMOTE_CI_VERIFIED"
    assert r["local_status"] == "VERSION_MISMATCH"
    assert r["precedence_reason"] == "COMMIT_BOUND_REMOTE_VERIFIED"


def test_remote_fail_not_overridden_by_local_pass():
    """Critical: a matching canonical remote FAIL must never be overridden by local PASS."""
    manifest = _manifest(_entry("ops_audit", COMMIT_AAA, "FAIL"))
    r = resolve_evidence("ops_audit", COMMIT_AAA, manifest, "PASS", "local run exit_code=0")
    assert r["canonical_status"] == "FAIL"
    assert r["local_status"] == "PASS"
    assert r["precedence_reason"] == "COMMIT_BOUND_REMOTE_VERIFIED"


def test_remote_pass_and_local_pass_no_double_credit_single_source():
    manifest = _manifest(_entry("ops_audit", COMMIT_AAA, "PASS"))
    r = resolve_evidence("ops_audit", COMMIT_AAA, manifest, "PASS", "exit_code=0")
    assert r["canonical_status"] == "PASS"
    assert r["canonical_source"] == "REMOTE_CI_VERIFIED"  # remote is the credited source, not "both"


def test_wrong_sha_remote_evidence_rejected_as_stale_local_fallback_used():
    manifest = _manifest(_entry("mypy_full_scope", COMMIT_BBB, "PASS"))
    r = resolve_evidence("mypy_full_scope", COMMIT_AAA, manifest, "PASS", "exit_code=0")
    assert r["canonical_status"] == "PASS"  # local fallback still allowed
    assert r["canonical_source"] == "LOCAL_VERIFIED"
    assert r["precedence_reason"] == "STALE_COMMIT_EVIDENCE_REJECTED_LOCAL_FALLBACK"


def test_wrong_sha_remote_evidence_rejected_no_local_fallback_when_local_unverified():
    manifest = _manifest(_entry("mypy_full_scope", COMMIT_BBB, "PASS"))
    r = resolve_evidence("mypy_full_scope", COMMIT_AAA, manifest, "VERSION_MISMATCH", "wrong version")
    assert r["canonical_status"] == "UNKNOWN"
    assert r["precedence_reason"] == "STALE_COMMIT_EVIDENCE_REJECTED_NO_LOCAL_FALLBACK"


def test_no_remote_local_verified_may_be_canonical():
    manifest = _manifest()
    r = resolve_evidence("secret_repo_gate", COMMIT_AAA, manifest, "PASS", "ok=True")
    assert r["canonical_status"] == "PASS"
    assert r["canonical_source"] == "LOCAL_VERIFIED"
    assert r["precedence_reason"] == "LOCAL_VERIFIED_NO_MATCHING_REMOTE_EVIDENCE"


def test_no_remote_local_wrong_version_yields_unknown_not_pass():
    manifest = _manifest()
    r = resolve_evidence("ruff_full_select", COMMIT_AAA, manifest, "VERSION_MISMATCH", "expected 0.16.0 found 0.15.21")
    assert r["canonical_status"] == "UNKNOWN"
    assert r["local_status"] == "VERSION_MISMATCH"
    assert r["precedence_reason"] == "NO_VALID_EVIDENCE"


def test_no_remote_no_local_evidence_yields_unknown():
    manifest = _manifest()
    r = resolve_evidence("postgres_migration_integrity_gate", COMMIT_AAA, manifest, "UNKNOWN", "not measurable locally")
    assert r["canonical_status"] == "UNKNOWN"
    assert r["canonical_source"] == "NONE"


def test_evidence_conflict_same_gate_same_commit_disagreeing_status():
    manifest = _manifest(
        _entry("ops_audit", COMMIT_AAA, "PASS"),
        _entry("ops_audit", COMMIT_AAA, "FAIL"),
    )
    r = resolve_evidence("ops_audit", COMMIT_AAA, manifest, "PASS", "exit_code=0")
    assert r["canonical_status"] == "UNKNOWN"
    assert r["canonical_source"] == "EVIDENCE_CONFLICT"
    assert r["precedence_reason"] == "EVIDENCE_CONFLICT"


def test_evidence_conflict_not_triggered_by_duplicate_agreeing_entries():
    """Two entries for the same gate+commit that AGREE is not a conflict."""
    manifest = _manifest(
        _entry("ops_audit", COMMIT_AAA, "PASS"),
        _entry("ops_audit", COMMIT_AAA, "PASS"),
    )
    r = resolve_evidence("ops_audit", COMMIT_AAA, manifest, "PASS", "exit_code=0")
    assert r["canonical_status"] == "PASS"
    assert r["canonical_source"] == "REMOTE_CI_VERIFIED"


def test_local_fail_correctly_verified_may_be_canonical_fail():
    """A deterministically-correct local FAIL (not a diagnostic) is legitimate tier-2 evidence."""
    manifest = _manifest()
    r = resolve_evidence("ops_audit", COMMIT_AAA, manifest, "FAIL", "exit_code=1")
    assert r["canonical_status"] == "FAIL"
    assert r["canonical_source"] == "LOCAL_VERIFIED"


@pytest.mark.parametrize("local_status", ["LOCAL_TOOL_MISSING", "LOCAL_EXECUTION_FAILURE", "UNKNOWN", "VERSION_MISMATCH"])
def test_local_diagnostic_statuses_never_eligible_for_tier2_canonical(local_status):
    manifest = _manifest()
    r = resolve_evidence("some_gate", COMMIT_AAA, manifest, local_status, "diagnostic detail")
    assert r["canonical_status"] == "UNKNOWN"
    assert r["canonical_source"] == "NONE"


def test_local_diagnostic_always_reported_even_when_canonical_comes_from_remote():
    manifest = _manifest(_entry("ruff_syntax_import_sanity", COMMIT_AAA, "PASS"))
    r = resolve_evidence("ruff_syntax_import_sanity", COMMIT_AAA, manifest, "VERSION_MISMATCH", "expected 0.16.0 found 0.15.21")
    assert r["local_status"] == "VERSION_MISMATCH"  # never suppressed just because canonical succeeded
    assert r["local_detail"] == "expected 0.16.0 found 0.15.21"


# ---------------------------------------------------------------------------
# validate_evidence_manifest(): schema and conflict checks
# ---------------------------------------------------------------------------

def test_valid_manifest_has_no_problems():
    manifest = _manifest(_entry("ops_audit", COMMIT_AAA, "PASS"))
    assert validate_evidence_manifest(manifest) == []


def test_missing_id_flagged():
    manifest = {"gates": [{"commit_sha": COMMIT_AAA, "status": "PASS", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF"}]}
    problems = validate_evidence_manifest(manifest)
    assert any("missing 'id'" in p for p in problems)


def test_malformed_commit_sha_flagged():
    manifest = _manifest({"id": "ops_audit", "commit_sha": "not-a-sha", "status": "PASS", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF"})
    problems = validate_evidence_manifest(manifest)
    assert any("malformed commit_sha" in p for p in problems)


def test_missing_commit_sha_flagged():
    manifest = _manifest({"id": "ops_audit", "status": "PASS", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF"})
    problems = validate_evidence_manifest(manifest)
    assert any("malformed commit_sha" in p for p in problems)


def test_invalid_status_flagged():
    manifest = _manifest({"id": "ops_audit", "commit_sha": COMMIT_AAA, "status": "MAYBE", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF"})
    problems = validate_evidence_manifest(manifest)
    assert any("invalid status" in p for p in problems)


def test_invalid_evidence_type_flagged():
    manifest = _manifest({"id": "ops_audit", "commit_sha": COMMIT_AAA, "status": "PASS", "evidence_type": "TOTALLY_MADE_UP", "provenance": "USER_SUPPLIED_REMOTE_PROOF"})
    problems = validate_evidence_manifest(manifest)
    assert any("invalid evidence_type" in p for p in problems)


def test_remote_ci_verified_missing_provenance_flagged():
    manifest = _manifest({"id": "ops_audit", "commit_sha": COMMIT_AAA, "status": "PASS", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": None})
    problems = validate_evidence_manifest(manifest)
    assert any("missing required 'provenance'" in p for p in problems)


def test_invalid_provenance_value_flagged():
    manifest = _manifest(_entry("ops_audit", COMMIT_AAA, "PASS", provenance="I_JUST_KNOW_IT_PASSED"))
    problems = validate_evidence_manifest(manifest)
    assert any("invalid provenance" in p for p in problems)


def test_duplicate_conflicting_entries_flagged_as_evidence_conflict():
    manifest = _manifest(
        _entry("ops_audit", COMMIT_AAA, "PASS"),
        _entry("ops_audit", COMMIT_AAA, "FAIL"),
    )
    problems = validate_evidence_manifest(manifest)
    assert any("EVIDENCE_CONFLICT" in p for p in problems)


def test_duplicate_agreeing_entries_not_flagged():
    manifest = _manifest(
        _entry("ops_audit", COMMIT_AAA, "PASS"),
        _entry("ops_audit", COMMIT_AAA, "PASS"),
    )
    assert validate_evidence_manifest(manifest) == []


def test_different_commits_same_gate_disagreeing_status_not_a_conflict():
    """Different commits are independent history, not a conflict, even if statuses differ."""
    manifest = _manifest(
        _entry("ops_audit", COMMIT_AAA, "PASS"),
        _entry("ops_audit", COMMIT_BBB, "FAIL"),
    )
    assert validate_evidence_manifest(manifest) == []


# ---------------------------------------------------------------------------
# Example/historical-sample evidence file: honesty and structural checks.
# This file is NEVER auto-loaded by the calculator -- see the
# self-attestation/bootstrap tests further below for that guarantee.
# ---------------------------------------------------------------------------

def test_old_live_attestation_path_no_longer_exists():
    """Locks in the self-attestation fix: the old config/quality/
    bys360_canonical_evidence.json (committed as though it were live runtime
    truth) must no longer exist at that path -- it has been superseded by
    the explicitly-labeled .example.json, which is never auto-loaded."""
    assert not OLD_LIVE_EVIDENCE_PATH.exists()


def test_example_manifest_file_is_valid():
    manifest = json.loads(CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    assert validate_evidence_manifest(manifest) == []


def test_example_manifest_marked_as_non_runtime_historical_sample():
    manifest = json.loads(CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    assert manifest["sample_type"] == "HISTORICAL_SAMPLE_NON_RUNTIME"


def test_example_manifest_has_no_fabricated_urls():
    raw_text = CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "http://" not in raw_text
    assert "https://" not in raw_text


def test_example_manifest_every_gate_entry_has_disclosed_provenance():
    manifest = json.loads(CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    for gate in manifest["gates"]:
        assert gate["provenance"] == "USER_SUPPLIED_REMOTE_PROOF", (
            f"{gate['id']} must honestly disclose it was manually supplied, not silently upgraded to look machine-verified"
        )


def test_example_manifest_ruff_full_select_has_no_evidence_entry():
    """The user's reported remote evidence covers only the syntax/import-sanity
    subset, not a full-select Ruff run -- these must never be conflated."""
    manifest = json.loads(CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    gate_ids = {g["id"] for g in manifest["gates"]}
    assert "ruff_full_select" not in gate_ids
    assert "ruff_syntax_import_sanity" in gate_ids


def test_example_manifest_handover_docs_contract_mapping_removed():
    """Strict provenance re-audit: 'BYS360 Score 100 Quality Gate V1' was only
    an inferred filename correlation to handover_docs_contract, not a direct
    name/identity match -- the mapping must be removed, not preserved to keep
    a historical score unchanged."""
    manifest = json.loads(CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    gate_ids = {g["id"] for g in manifest["gates"]}
    assert "handover_docs_contract" not in gate_ids
    unmapped_ids = {g["id"] for g in manifest["deliberately_unmapped_gates"]}
    assert "handover_docs_contract" in unmapped_ids


def test_example_manifest_only_six_gates_have_direct_provenance():
    """Provenance audit result: quality9_gate, coverage_ratchet,
    ruff_syntax_import_sanity, postgres_migration_integrity_gate,
    dependency_audit, ops_audit -- exactly these 6, no more, no fewer."""
    manifest = json.loads(CANONICAL_EVIDENCE_EXAMPLE_PATH.read_text(encoding="utf-8"))
    gate_ids = {g["id"] for g in manifest["gates"]}
    assert gate_ids == {
        "quality9_gate", "coverage_ratchet", "ruff_syntax_import_sanity",
        "postgres_migration_integrity_gate", "dependency_audit", "ops_audit",
    }


# ---------------------------------------------------------------------------
# compute_report() integration: cross-environment reproducibility
# ---------------------------------------------------------------------------

def _cross_env_methodology():
    categories = {
        "Code Quality": {
            "gate_component_weight": 0.8, "rubric_component_weight": 0.2,
            "gates": [{"name": "ruff_full_select", "kind": "python_module", "module": "ruff", "expected_version": "0.16.0", "args": ["check"], "pass_rule": "exit_code_0"}],
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
    return {
        "methodology_version": "1.0.0-test",
        "debt_penalty_policy": {"severity_weights": {"P0": 40, "P1": 20, "P2": 8, "P3": 3, "UNCLASSIFIED": 5}, "penalty_cap_per_category": 30},
        "evidence_completeness_ceiling": {"value": 89},
        "composites": {
            "LIVE_READINESS": {"weights": {"Security": 0.22, "Test Assurance": 0.21, "CI-Release": 0.21, "Operations": 0.20, "Code Quality": 0.10, "Maintainability": 0.03, "Documentation-Handover": 0.03}},
            "TRANSFERABILITY": {"weights": {"Documentation-Handover": 0.22, "Maintainability": 0.22, "Test Assurance": 0.18, "Code Quality": 0.15, "CI-Release": 0.10, "Operations": 0.06, "Security": 0.07}},
        },
        "categories": categories,
    }


def _cross_env_registry():
    return {"registry_version": "1.0.0-test", "reconciliation_status": "FULLY_RECONCILED", "reconciliation_note": "test", "items": []}


def _cross_env_manifest():
    return {"gates": [_entry("ruff_full_select", COMMIT_AAA, "PASS")]}


def _cross_env_evidence():
    return {"gate_b": True, "gate_c": True, "gate_d": True, "gate_e": True, "gate_f": True}


def test_cross_environment_A_correct_local_version_matches_remote(tmp_path, monkeypatch):
    """Environment A: local Ruff is correctly pinned -- local and canonical agree."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    monkeypatch.setattr(calc, "_check_tool_version", lambda *a, **k: (True, "0.16.0", None))
    monkeypatch.setattr(calc, "_run_argv", lambda *a, **k: (0, "All checks passed!", None))

    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=_cross_env_manifest(), scored_commit=COMMIT_AAA,
    )
    assert report["LIVE_READINESS"]["final"] == report["LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL"]["LIVE_READINESS_local"]
    gate = report["category_scores"]["Code Quality"]["gate_contributions"][0]
    assert gate["canonical_status"] == "PASS"
    assert gate["local_status"] == "PASS"


def test_cross_environment_B_wrong_local_version_canonical_still_matches_A(tmp_path, monkeypatch):
    """Environment B: local Ruff is off-pin (VERSION_MISMATCH) -- canonical score
    must still equal Environment A's, because commit-bound remote evidence covers
    this gate. Only the local diagnostic differs."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    monkeypatch.setattr(calc, "_check_tool_version", lambda *a, **k: (False, "0.15.21", None))

    report_b = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=_cross_env_manifest(), scored_commit=COMMIT_AAA,
    )
    gate = report_b["category_scores"]["Code Quality"]["gate_contributions"][0]
    assert gate["canonical_status"] == "PASS"  # unaffected by wrong local version
    assert gate["local_status"] == "VERSION_MISMATCH"  # local diagnostic correctly differs
    assert gate["precedence_reason"] == "COMMIT_BOUND_REMOTE_VERIFIED"


def test_cross_environment_C_tool_missing_canonical_still_matches(tmp_path, monkeypatch):
    """Environment C: Ruff is not installed at all (OSError on launch) -- canonical
    score must still equal Environments A/B's for this gate."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    def fake_check_version(python_path, module, expected, cwd):
        return False, "OSError: [Errno 2] No such file or directory: 'ruff'", "LOCAL_TOOL_MISSING"

    monkeypatch.setattr(calc, "_check_tool_version", fake_check_version)

    report_c = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=_cross_env_manifest(), scored_commit=COMMIT_AAA,
    )
    gate = report_c["category_scores"]["Code Quality"]["gate_contributions"][0]
    assert gate["canonical_status"] == "PASS"
    assert gate["local_status"] == "LOCAL_TOOL_MISSING"
    assert gate["precedence_reason"] == "COMMIT_BOUND_REMOTE_VERIFIED"


def test_cross_environment_A_B_C_canonical_composites_are_identical(tmp_path, monkeypatch):
    """The key acceptance test: run all three environments in the same test and
    directly compare CANONICAL_PROJECT_SCORE -- must be byte-identical -- while
    local diagnostics differ."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    def run(check_version_fn):
        monkeypatch.setattr(calc, "_check_tool_version", check_version_fn)
        return compute_report(
            _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
            canonical_manifest=_cross_env_manifest(), scored_commit=COMMIT_AAA,
        )

    report_a = run(lambda *a, **k: (True, "0.16.0", None))
    report_b = run(lambda *a, **k: (False, "0.15.21", None))
    report_c = run(lambda *a, **k: (False, "n/a", "LOCAL_TOOL_MISSING"))

    assert report_a["LIVE_READINESS"]["final"] == report_b["LIVE_READINESS"]["final"] == report_c["LIVE_READINESS"]["final"]
    assert report_a["TRANSFERABILITY"]["final"] == report_b["TRANSFERABILITY"]["final"] == report_c["TRANSFERABILITY"]["final"]
    assert report_a["LIVE_READINESS"]["raw"] == report_b["LIVE_READINESS"]["raw"] == report_c["LIVE_READINESS"]["raw"]

    # Local diagnostics genuinely differ across environments.
    local_statuses = {
        report_a["category_scores"]["Code Quality"]["gate_contributions"][0]["local_status"],
        report_b["category_scores"]["Code Quality"]["gate_contributions"][0]["local_status"],
        report_c["category_scores"]["Code Quality"]["gate_contributions"][0]["local_status"],
    }
    assert local_statuses == {"PASS", "VERSION_MISMATCH", "LOCAL_TOOL_MISSING"}


def test_no_remote_evidence_canonical_score_falls_back_to_local_and_can_differ(tmp_path, monkeypatch):
    """Contrast case: WITHOUT matching remote evidence, a wrong local version DOES
    lower the canonical score -- proving the manifest, not blind optimism, is what
    stabilizes the score across environments."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    monkeypatch.setattr(calc, "_check_tool_version", lambda *a, **k: (False, "0.15.21", None))
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest={"gates": []}, scored_commit=COMMIT_AAA,  # empty manifest this time
    )
    gate = report["category_scores"]["Code Quality"]["gate_contributions"][0]
    assert gate["canonical_status"] == "UNKNOWN"
    assert report["category_scores"]["Code Quality"]["gate_component"] == 0.0


# ---------------------------------------------------------------------------
# compute_report() integration: PostgreSQL / dependency-audit remote evidence
# ---------------------------------------------------------------------------

def test_postgres_gate_remote_evidence_used_when_locally_unmeasurable(tmp_path):
    methodology = _cross_env_methodology()
    methodology["categories"]["CI-Release"]["gates"] = [
        {"name": "postgres_migration_integrity_gate", "pass_rule": "exit_code_0_or_supplied_evidence", "evidence_note": "needs live postgres"},
    ]
    manifest = {"gates": [_entry("postgres_migration_integrity_gate", COMMIT_AAA, "PASS")]}
    report = compute_report(
        methodology, _cross_env_registry(), tmp_path, evidence={},  # nothing supplied locally
        canonical_manifest=manifest, scored_commit=COMMIT_AAA,
    )
    gate = report["category_scores"]["CI-Release"]["gate_contributions"][0]
    assert gate["canonical_status"] == "PASS"
    assert gate["canonical_source"] == "REMOTE_CI_VERIFIED"
    assert report["category_scores"]["CI-Release"]["gate_component"] > 0


def test_dependency_audit_remote_evidence_used_when_locally_unmeasurable(tmp_path):
    methodology = _cross_env_methodology()
    methodology["categories"]["Security"]["gates"] = [
        {"name": "dependency_audit", "pass_rule": "exit_code_0_or_supplied_evidence", "evidence_note": "slow/network"},
    ]
    manifest = {"gates": [_entry("dependency_audit", COMMIT_AAA, "PASS")]}
    report = compute_report(
        methodology, _cross_env_registry(), tmp_path, evidence={},
        canonical_manifest=manifest, scored_commit=COMMIT_AAA,
    )
    gate = report["category_scores"]["Security"]["gate_contributions"][0]
    assert gate["canonical_status"] == "PASS"
    assert gate["canonical_source"] == "REMOTE_CI_VERIFIED"


# ---------------------------------------------------------------------------
# Report shape: new sections present, methodology semantics unchanged
# ---------------------------------------------------------------------------

def test_report_exposes_canonical_and_local_sections(tmp_path):
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest={"gates": []}, scored_commit=COMMIT_AAA,
    )
    assert "CANONICAL_PROJECT_EVIDENCE" in report
    assert "LOCAL_ENVIRONMENT_DIAGNOSTICS" in report
    assert "LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL" in report
    assert report["scored_commit"] == COMMIT_AAA


def test_registry_derived_gate_bypasses_manifest_and_is_always_canonical(tmp_path):
    """no_open_p0_or_p1_anywhere is computed from the checked-out registry file
    itself -- inherently commit-bound, must never depend on the manifest."""
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest={"gates": []}, scored_commit=COMMIT_AAA,
    )
    gate = report["category_scores"]["Maintainability"]["gate_contributions"][0]
    assert gate["canonical_source"] == "REGISTRY_DERIVED"
    assert gate["canonical_status"] == "PASS"


# ---------------------------------------------------------------------------
# resolve_evidence_file(): CLI/env resolution, fail-fast on bad input,
# and -- critically -- NO default auto-load of any committed file.
# ---------------------------------------------------------------------------

def _write_valid_evidence_file(tmp_path, commit_sha=COMMIT_AAA):
    p = tmp_path / "evidence_external.json"
    p.write_text(json.dumps({
        "schema_version": "1.0",
        "evidence_set_id": "TEST_SET_1",
        "gates": [_entry("ops_audit", commit_sha, "PASS")],
    }), encoding="utf-8")
    return p


def test_no_evidence_file_or_env_yields_no_external_evidence(monkeypatch):
    monkeypatch.delenv("BYS360_CANONICAL_EVIDENCE_FILE", raising=False)
    manifest, trace = resolve_evidence_file(None)
    assert manifest == {"gates": []}
    assert trace["source"] == "NO_EXTERNAL_EVIDENCE"
    assert trace["loaded"] is False
    assert trace["validation_status"] == "NOT_APPLICABLE"


def test_explicit_evidence_file_loaded_and_validated(tmp_path):
    p = _write_valid_evidence_file(tmp_path)
    manifest, trace = resolve_evidence_file(str(p))
    assert trace["loaded"] is True
    assert trace["source"] == "explicit"
    assert trace["validation_status"] == "VALID"
    assert trace["evidence_set_id"] == "TEST_SET_1"
    assert trace["commit_sha_or_commit_set"] == [COMMIT_AAA]
    assert manifest["gates"][0]["id"] == "ops_audit"


def test_env_var_evidence_file_honored_when_no_cli_flag(tmp_path, monkeypatch):
    p = _write_valid_evidence_file(tmp_path)
    monkeypatch.setenv("BYS360_CANONICAL_EVIDENCE_FILE", str(p))
    manifest, trace = resolve_evidence_file(None)
    assert trace["source"] == "env"
    assert trace["loaded"] is True
    assert manifest["gates"][0]["id"] == "ops_audit"


def test_explicit_evidence_file_takes_priority_over_env_var(tmp_path, monkeypatch):
    cli_path = _write_valid_evidence_file(tmp_path, commit_sha=COMMIT_AAA)
    env_path = tmp_path / "other.json"
    env_path.write_text(json.dumps({"gates": [_entry("ops_audit", COMMIT_BBB, "PASS")]}), encoding="utf-8")
    monkeypatch.setenv("BYS360_CANONICAL_EVIDENCE_FILE", str(env_path))
    manifest, trace = resolve_evidence_file(str(cli_path))
    assert trace["source"] == "explicit"
    assert manifest["gates"][0]["commit_sha"] == COMMIT_AAA


def test_missing_explicit_evidence_file_fails_fast_not_silent_fallback():
    with pytest.raises(SystemExit, match="EVIDENCE_FILE_NOT_FOUND"):
        resolve_evidence_file("C:/definitely/does/not/exist/evidence.json")


def test_missing_env_evidence_file_fails_fast(monkeypatch, tmp_path):
    monkeypatch.setenv("BYS360_CANONICAL_EVIDENCE_FILE", str(tmp_path / "missing.json"))
    with pytest.raises(SystemExit, match="EVIDENCE_FILE_NOT_FOUND"):
        resolve_evidence_file(None)


def test_malformed_json_evidence_file_fails_fast(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SystemExit, match="EVIDENCE_FILE_INVALID"):
        resolve_evidence_file(str(p))


def test_schema_invalid_evidence_file_fails_fast_not_ignored(tmp_path):
    """A typo/tampered file (e.g. a bad SHA) must BLOCK, never be silently
    treated as though nothing had been supplied."""
    p = tmp_path / "bad_schema.json"
    p.write_text(json.dumps({"gates": [{"id": "ops_audit", "commit_sha": "not-a-sha", "status": "PASS", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF"}]}), encoding="utf-8")
    with pytest.raises(SystemExit, match="EVIDENCE_FILE_INVALID"):
        resolve_evidence_file(str(p))


def test_unknown_status_evidence_file_rejected(tmp_path):
    p = tmp_path / "unknown_status.json"
    p.write_text(json.dumps({"gates": [{"id": "ops_audit", "commit_sha": COMMIT_AAA, "status": "MAYBE", "evidence_type": "REMOTE_CI_VERIFIED", "provenance": "USER_SUPPLIED_REMOTE_PROOF"}]}), encoding="utf-8")
    with pytest.raises(SystemExit, match="EVIDENCE_FILE_INVALID"):
        resolve_evidence_file(str(p))


def test_example_file_is_never_auto_loaded_by_default(monkeypatch):
    """The committed .example.json exists on disk in this very repo, yet
    calling resolve_evidence_file with no CLI flag and no env var must still
    yield NO_EXTERNAL_EVIDENCE -- proving there is no hidden default path
    pointing at it."""
    monkeypatch.delenv("BYS360_CANONICAL_EVIDENCE_FILE", raising=False)
    assert CANONICAL_EVIDENCE_EXAMPLE_PATH.exists()  # sanity: the file really is there
    manifest, trace = resolve_evidence_file(None)
    assert trace["source"] == "NO_EXTERNAL_EVIDENCE"
    assert manifest == {"gates": []}


# ---------------------------------------------------------------------------
# Self-attestation / bootstrap acceptance tests (the core point of this
# wave): current HEAD can be scored using freshly-captured remote evidence
# without any repository mutation, and the mechanism generalizes to
# historical commits too.
# ---------------------------------------------------------------------------

def test_current_head_bootstrap_no_repository_mutation(tmp_path):
    """Formal proof of SELF_ATTESTATION_BOOTSTRAP_DEFECT = CLOSED:
    1. A commit ABC is 'pushed' (simulated -- any valid-looking 40-hex SHA).
    2. Remote CI produces evidence for ABC, captured in an EXTERNAL file
       (never inside the repository tree).
    3. The checkout/scored commit remains ABC the whole time.
    4. Scoring ABC with --evidence-file <external path> succeeds and grants
       real canonical credit -- with zero writes to any repository-tracked
       path, and therefore no new commit was ever required to record it."""
    commit_abc = "ab" * 20
    external_evidence_path = tmp_path / "evidence_ABC_from_ci_artifact.json"  # deliberately outside the repo tree
    external_evidence_path.write_text(json.dumps({
        "schema_version": "1.0",
        "evidence_set_id": "CI_RUN_FOR_ABC",
        "gates": [_entry("ops_audit", commit_abc, "PASS"), _entry("quality9_gate", commit_abc, "PASS")],
    }), encoding="utf-8")

    tracked_files_before = sorted(REPO_ROOT.rglob("*.json"))  # coarse repo-state snapshot (config dir only matters)
    config_before = json.loads((REPO_ROOT / "config" / "quality" / "bys360_canonical_evidence.example.json").read_text(encoding="utf-8"))

    manifest, trace = resolve_evidence_file(str(external_evidence_path))
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=manifest, scored_commit=commit_abc, evidence_input_trace=trace,
    )

    # Canonical evidence was accepted for the exact commit being scored.
    assert report["scored_commit"] == commit_abc
    assert report["EVIDENCE_INPUT"]["loaded"] is True
    assert report["EVIDENCE_INPUT"]["commit_sha_or_commit_set"] == [commit_abc]

    # No repository file was touched to make this happen.
    tracked_files_after = sorted(REPO_ROOT.rglob("*.json"))
    assert tracked_files_before == tracked_files_after
    config_after = json.loads((REPO_ROOT / "config" / "quality" / "bys360_canonical_evidence.example.json").read_text(encoding="utf-8"))
    assert config_before == config_after


def test_historical_scoring_flow_no_special_git_hack(tmp_path):
    """An OLD scored commit with its own external evidence file scores
    correctly too -- no special-casing needed for 'the current' vs. 'a past'
    commit; the mechanism is identical either way."""
    old_sha = "cd" * 20
    p = tmp_path / "evidence_old.json"
    p.write_text(json.dumps({"gates": [_entry("gate_e", old_sha, "PASS")]}), encoding="utf-8")
    manifest, trace = resolve_evidence_file(str(p))
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=manifest, scored_commit=old_sha, evidence_input_trace=trace,
    )
    assert report["scored_commit"] == old_sha
    gate = report["category_scores"]["Operations"]["gate_contributions"][0]
    assert gate["canonical_status"] == "PASS"
    assert gate["canonical_source"] == "REMOTE_CI_VERIFIED"


def test_external_evidence_file_cross_environment_reproducibility(tmp_path, monkeypatch):
    """Section 33's required test: an ACTUAL temporary external file (not an
    in-memory dict) drives identical canonical scores across 3 simulated
    environments."""
    import scripts.quality.bys360_score_reconcile_v1 as calc

    evidence_path = tmp_path / "evidence_cross_env.json"
    evidence_path.write_text(json.dumps({"gates": [_entry("ruff_full_select", COMMIT_AAA, "PASS")]}), encoding="utf-8")

    def run(check_version_fn):
        monkeypatch.setattr(calc, "_check_tool_version", check_version_fn)
        manifest, trace = resolve_evidence_file(str(evidence_path))
        return compute_report(
            _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
            canonical_manifest=manifest, scored_commit=COMMIT_AAA, evidence_input_trace=trace,
        )

    report_a = run(lambda *a, **k: (True, "0.16.0", None))
    report_b = run(lambda *a, **k: (False, "0.15.21", None))
    report_c = run(lambda *a, **k: (False, "n/a", "LOCAL_TOOL_MISSING"))

    assert report_a["LIVE_READINESS"]["final"] == report_b["LIVE_READINESS"]["final"] == report_c["LIVE_READINESS"]["final"]
    assert report_a["TRANSFERABILITY"]["final"] == report_b["TRANSFERABILITY"]["final"] == report_c["TRANSFERABILITY"]["final"]
    local_statuses = {
        r["category_scores"]["Code Quality"]["gate_contributions"][0]["local_status"]
        for r in (report_a, report_b, report_c)
    }
    assert local_statuses == {"PASS", "VERSION_MISMATCH", "LOCAL_TOOL_MISSING"}


def test_stale_external_file_rejected_for_wrong_scored_commit(tmp_path):
    p = tmp_path / "evidence_aaa.json"
    p.write_text(json.dumps({"gates": [_entry("gate_e", COMMIT_AAA, "PASS")]}), encoding="utf-8")
    manifest, trace = resolve_evidence_file(str(p))
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=manifest, scored_commit=COMMIT_BBB, evidence_input_trace=trace,
    )
    gate = report["category_scores"]["Operations"]["gate_contributions"][0]
    assert gate["precedence_reason"] in (
        "STALE_COMMIT_EVIDENCE_REJECTED_LOCAL_FALLBACK", "STALE_COMMIT_EVIDENCE_REJECTED_NO_LOCAL_FALLBACK",
    )


def test_remote_fail_external_file_precedence(tmp_path):
    p = tmp_path / "evidence_fail.json"
    p.write_text(json.dumps({"gates": [_entry("gate_e", COMMIT_AAA, "FAIL")]}), encoding="utf-8")
    manifest, trace = resolve_evidence_file(str(p))
    evidence = dict(_cross_env_evidence())
    evidence["gate_e"] = True  # locally PASS
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, evidence,
        canonical_manifest=manifest, scored_commit=COMMIT_AAA, evidence_input_trace=trace,
    )
    gate = report["category_scores"]["Operations"]["gate_contributions"][0]
    assert gate["canonical_status"] == "FAIL"
    assert gate["local_status"] == "PASS"


def test_canonical_evidence_composition_reports_completeness(tmp_path):
    p = tmp_path / "evidence_partial.json"
    p.write_text(json.dumps({"gates": [_entry("gate_e", COMMIT_AAA, "PASS")]}), encoding="utf-8")
    manifest, trace = resolve_evidence_file(str(p))
    report = compute_report(
        _cross_env_methodology(), _cross_env_registry(), tmp_path, _cross_env_evidence(),
        canonical_manifest=manifest, scored_commit=COMMIT_AAA, evidence_input_trace=trace,
    )
    comp = report["CANONICAL_EVIDENCE_COMPOSITION"]
    assert comp["remote_verified_gates"] >= 1
    assert comp["completeness"] in ("FULL", "LOCAL_FALLBACK_USED", "PARTIAL")


def test_no_hardcoded_9def579_in_runtime_calculator_source():
    """9def579... may appear in historical docs/test fixtures/example
    evidence, never as a hardcoded assumption inside the calculator's own
    runtime logic."""
    source = Path("scripts/quality/bys360_score_reconcile_v1.py").read_text(encoding="utf-8")
    assert "9def579247637390b7635c02f606449a2692ef99" not in source
