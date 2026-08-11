"""BYS360 Phase 6 -- CI Coverage Scope Policy Closure contract tests.

Locks in the decision that ``tests/services`` (422 tests, verified stable
and low-cost) is included in the real CI-enforced coverage measurement in
``.github/workflows/bys360-ci.yml``, via the same single unified pytest
invocation as the rest of the CI-exact scope (Policy A -- no separate
coverage-combine step). Also locks in that the coverage source scope and
ratchet floor were not weakened while doing so.

Also locks in the follow-up Critical Operational CI Coverage Expansion
(2026-07-27): ``tests/migrations``, ``tests/workflow`` and ``tests/release``
(46 tests total, 0 cross-scope duplicate node IDs, 0 skip/xfail, each stable
across 2 isolated runs + 1 combined run) were added via the same Policy A
single-invocation approach.

``tests/workflow`` was later deleted in commit 5401195 ("remove orphan
presentation subsystem", ORPHAN_CONFIRMED -- see that commit's message) along
with the dead ``app/workflow/`` package it tested. The CI workflow's pytest
command kept the now-nonexistent ``tests/workflow`` path for 5 days/12
commits afterward, which made pytest exit 4 ("file or directory not found")
on that step's ENTIRE positional-argument list -- zeroing out ~3400 tests and
this step's coverage.xml output, and making every step after it (coverage
ratchet, mypy, ops audit, Quality9, pip-audit) unreachable in real CI. The
"BYS360 CI Coverage Gate Drift Closure" section below removes the stale path,
wires in its replacement contract test file explicitly, and adds a
filesystem-existence check over every CI-referenced test path so this class
of drift cannot recur silently again.

Also locks in the follow-up Communication/Behavior/Mobile CI Coverage
Expansion (2026-07-27): ``tests/communication``, ``tests/behavior`` and
``tests/mobile`` (29 tests total, 0 cross-scope duplicate node IDs, 0
skip/xfail, stable across 2 isolated runs + 1 combined run) were added via
the same Policy A single-invocation approach. tests/communication and
tests/mobile are 0-import AST/source-contract checks (~0% measurable app/
coverage, kept as required structural gates); tests/behavior imports real
app.services/app.models and does contribute measurable app/ coverage.

These are pure contract/parsing tests -- they read real repo files, they do
not run the workflow or any subprocess, with one deliberate exception: the
BYS360 CI Coverage Gate Drift Closure section's
``test_workflow_orphan_cleanup_contract_collects_exactly_82_tests`` runs a
real ``pytest --collect-only`` subprocess against the replacement contract
file, because only a real pytest collection pass -- not static AST parsing --
can prove that file actually collects, given it mixes plain and
``@pytest.mark.parametrize`` tests.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts.quality import bys360_quality9_ci_gate as quality9

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "bys360-ci.yml"
COVERAGE_BASELINE = ROOT / "reports" / "quality" / "coverage_baseline.json"
PYPROJECT = ROOT / "pyproject.toml"

# The baseline in effect before this policy closure (Campaign 1B, 2026-07-24)
# -- locked here as a historical floor so the ratchet can never be silently
# lowered back toward it by a future edit.
PRE_CLOSURE_BASELINE_COMBINED_PCT = 18.85

# The baseline in effect before the Critical Operational CI Coverage
# Expansion (services-only scope, 2026-07-27) -- locked here so the ratchet
# can never be silently lowered back toward it by a future edit.
PRE_CRITICAL_EXPANSION_BASELINE_COMBINED_PCT = 23.27

CRITICAL_OPERATIONAL_TEST_PATHS = ("tests/migrations", "tests/release")

# The baseline in effect before the Communication/Behavior/Mobile CI Coverage
# Expansion (2026-07-27) -- locked here so the ratchet can never be silently
# lowered back toward it by a future edit.
PRE_REMAINING_MODULE_EXPANSION_BASELINE_COMBINED_PCT = 23.39

REMAINING_MODULE_TEST_PATHS = ("tests/communication", "tests/behavior", "tests/mobile")


def _ci_workflow_commands() -> list[str]:
    return quality9.workflow_run_commands(CI_WORKFLOW.read_text(encoding="utf-8"))


def _coverage_instrumented_broad_step_command() -> str:
    commands = _ci_workflow_commands()
    matches = [c for c in commands if "tests/integration" in c and "tests/critical" in c]
    assert len(matches) == 1, (
        "expected exactly one CI run command combining tests/integration and "
        f"tests/critical, found {len(matches)}"
    )
    return matches[0]


def _ci_safe_step_command() -> str:
    commands = _ci_workflow_commands()
    matches = [c for c in commands if 'tests/quality' in c and '"ci_safe"' in c]
    assert len(matches) == 1, f"expected exactly one ci_safe pytest command, found {len(matches)}"
    return matches[0]


# --- Test A: services is in the real coverage-measured CI scope ---


def test_services_is_included_in_coverage_instrumented_ci_step() -> None:
    command = _coverage_instrumented_broad_step_command()
    assert "tests/services" in command
    assert "--cov=app" in command
    assert "--cov-append" in command


# --- Test E: no duplicate execution across CI steps ---


def test_services_is_not_also_run_in_the_ci_safe_step() -> None:
    """tests/services must be measured exactly once in the coverage run --
    appearing in both CI pytest invocations would double-count its lines in
    the combined coverage.xml (harmless for statement coverage, since
    coverage.py dedupes by executed line, but it would silently run all 422
    tests twice per CI run for no reason)."""
    ci_safe_command = _ci_safe_step_command()
    assert "tests/services" not in ci_safe_command


def test_services_appears_in_exactly_one_ci_workflow_run_command() -> None:
    commands = _ci_workflow_commands()
    hits = [c for c in commands if "tests/services" in c]
    assert len(hits) == 1, f"expected tests/services in exactly one CI run command, found {len(hits)}: {hits}"


# --- Test B: a services failure actually blocks the coverage job ---


def test_coverage_step_has_no_failure_suppression() -> None:
    """No ``continue-on-error``, ``|| true``, or exit-code swallowing on the
    step that now includes tests/services -- a real test failure there must
    fail the CI job, not be silently absorbed."""
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "continue-on-error" not in workflow_text
    command = _coverage_instrumented_broad_step_command()
    assert "|| true" not in command
    assert "--exitfirst" not in command
    assert "-x " not in command and not command.rstrip().endswith(" -x")


# --- Test C: the ratchet floor was raised, never lowered ---


def test_coverage_ratchet_baseline_was_raised_not_lowered() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    new_combined_pct = float(data["combined_pct"])
    assert new_combined_pct > PRE_CLOSURE_BASELINE_COMBINED_PCT, (
        f"new coverage_baseline.json combined_pct ({new_combined_pct}) must be strictly "
        f"greater than the pre-closure baseline ({PRE_CLOSURE_BASELINE_COMBINED_PCT}); "
        "the ratchet must never be silently lowered"
    )


def test_coverage_baseline_commands_include_services() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    commands = data.get("commands", [])
    assert any("tests/services" in c for c in commands), (
        "coverage_baseline.json's recorded 'commands' must reflect the real "
        "measured scope, including tests/services"
    )


def test_coverage_baseline_tolerance_still_present() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    assert "tolerance_pct" in data
    assert float(data["tolerance_pct"]) > 0


# --- Test D: production coverage source scope was not weakened ---


def test_coverage_source_scope_is_unchanged() -> None:
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    coverage_run = data.get("tool", {}).get("coverage", {}).get("run", {})
    assert coverage_run.get("source") == ["app"]
    assert coverage_run.get("branch") is True


def test_coverage_omit_list_was_not_expanded_to_hide_services_or_app_code() -> None:
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    coverage_report = data.get("tool", {}).get("coverage", {}).get("report", {})
    omit = coverage_report.get("omit", [])
    # The pre-existing, narrow omit list (static/templates/inspect helpers)
    # must not have grown to quietly exclude real application code.
    assert len(omit) <= 4
    for pattern in omit:
        assert "services" not in pattern.lower() or "static" in pattern.lower()


def test_coverage_fail_under_floor_not_lowered() -> None:
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    coverage_report = data.get("tool", {}).get("coverage", {}).get("report", {})
    fail_under = coverage_report.get("fail_under")
    assert fail_under is not None
    assert fail_under >= 18


# --- Test F: no stale "excluded from CI" claim remains ---


def test_no_stale_services_excluded_from_ci_claim_in_workflow() -> None:
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow_text.lower()
    stale_patterns = [
        "services excluded",
        "services is not included",
        "services kapsam dışı",
        "services scope dışında",
    ]
    for pattern in stale_patterns:
        assert pattern not in lowered, f"stale exclusion claim found in workflow: {pattern!r}"


def test_pytest_ini_does_not_exclude_services_from_collection() -> None:
    """Guards against a future accidental addition of ``services`` to
    ``norecursedirs`` (or similar), which would silently stop pytest from
    ever collecting tests/services regardless of what the CI workflow asks
    for."""
    ini_text = re.sub(r"#.*", "", (ROOT / "pytest.ini").read_text(encoding="utf-8"))
    norecursedirs_match = re.search(r"norecursedirs\s*=\s*((?:\n[ \t]+\S+)*)", ini_text)
    assert norecursedirs_match is not None
    excluded_dirs = norecursedirs_match.group(1).split()
    assert "services" not in excluded_dirs
    assert "tests/services" not in excluded_dirs


# =====================================================================
# BYS360 Phase 6 -- Critical Operational CI Coverage Expansion
# (tests/migrations, tests/workflow, tests/release)
# =====================================================================

# --- Tests A/B/C: migrations/workflow/release are in the real coverage-measured CI scope ---


@pytest.mark.parametrize("target_path", CRITICAL_OPERATIONAL_TEST_PATHS)
def test_critical_operational_path_is_included_in_coverage_instrumented_ci_step(target_path: str) -> None:
    command = _coverage_instrumented_broad_step_command()
    assert target_path in command, f"{target_path} must be part of the real coverage-instrumented CI step"


# --- Test D: no duplicate execution, neither against the ci_safe step nor across each other ---


@pytest.mark.parametrize("target_path", CRITICAL_OPERATIONAL_TEST_PATHS)
def test_critical_operational_path_is_not_also_run_in_the_ci_safe_step(target_path: str) -> None:
    ci_safe_command = _ci_safe_step_command()
    assert target_path not in ci_safe_command


@pytest.mark.parametrize("target_path", CRITICAL_OPERATIONAL_TEST_PATHS)
def test_critical_operational_path_appears_in_exactly_one_ci_workflow_run_command(target_path: str) -> None:
    commands = _ci_workflow_commands()
    hits = [c for c in commands if target_path in c]
    assert len(hits) == 1, f"expected {target_path} in exactly one CI run command, found {len(hits)}: {hits}"


def test_no_critical_operational_path_appears_more_than_once_in_the_same_command() -> None:
    """Each of tests/migrations, tests/workflow, tests/release must appear
    exactly once as a distinct pytest rootdir argument in the broad step --
    guards against an accidental copy-paste duplicate within the same run
    line (which pytest would silently collect twice)."""
    command = _coverage_instrumented_broad_step_command()
    tokens = command.split()
    for target_path in CRITICAL_OPERATIONAL_TEST_PATHS:
        assert tokens.count(target_path) == 1, f"{target_path} must appear exactly once as a pytest argument"


# --- Test E: a migration/workflow/release failure actually blocks the coverage job ---
# (covered generically by test_coverage_step_has_no_failure_suppression above --
# that check already applies to the whole broad step command, which now
# includes these three paths too; no continue-on-error/|| true was added.)


# --- Test F: production coverage source scope was not weakened ---
# (covered generically by test_coverage_source_scope_is_unchanged and
# test_coverage_omit_list_was_not_expanded_to_hide_services_or_app_code
# above -- those assertions are not services-specific, they hold for the
# whole [tool.coverage] contract regardless of which test paths feed it.)


# --- Test G: the ratchet floor was raised again, never lowered back toward the pre-expansion value ---


def test_coverage_ratchet_baseline_was_raised_past_pre_critical_expansion_value() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    new_combined_pct = float(data["combined_pct"])
    assert new_combined_pct >= PRE_CRITICAL_EXPANSION_BASELINE_COMBINED_PCT, (
        f"new coverage_baseline.json combined_pct ({new_combined_pct}) must not regress below "
        f"the pre-critical-expansion baseline ({PRE_CRITICAL_EXPANSION_BASELINE_COMBINED_PCT})"
    )


def test_coverage_baseline_commands_include_all_critical_operational_paths() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    commands = data.get("commands", [])
    for target_path in CRITICAL_OPERATIONAL_TEST_PATHS:
        assert any(target_path in c for c in commands), (
            f"coverage_baseline.json's recorded 'commands' must reflect the real "
            f"measured scope, including {target_path}"
        )


# --- Test H: baseline test-count metadata arithmetic is internally consistent ---


def test_baseline_metadata_step_counts_sum_to_total_passed() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    counts = data["test_counts"]
    step1_passed = counts["step1_ci_safe_passed"]
    step2_passed = counts["step2_broader_scope_passed"]
    assert step1_passed + step2_passed == counts["total_passed"], (
        f"step1_ci_safe_passed ({step1_passed}) + step2_broader_scope_passed "
        f"({step2_passed}) must equal total_passed ({counts['total_passed']})"
    )


# =====================================================================
# BYS360 Phase 6 -- Communication/Behavior/Mobile CI Coverage Expansion
# (tests/communication, tests/behavior, tests/mobile)
# =====================================================================

# --- Tests: communication/behavior/mobile are in the real coverage-measured CI scope ---


@pytest.mark.parametrize("target_path", REMAINING_MODULE_TEST_PATHS)
def test_remaining_module_path_is_included_in_coverage_instrumented_ci_step(target_path: str) -> None:
    command = _coverage_instrumented_broad_step_command()
    assert target_path in command, f"{target_path} must be part of the real coverage-instrumented CI step"


# --- No duplicate execution, neither against the ci_safe step nor across each other ---


@pytest.mark.parametrize("target_path", REMAINING_MODULE_TEST_PATHS)
def test_remaining_module_path_is_not_also_run_in_the_ci_safe_step(target_path: str) -> None:
    ci_safe_command = _ci_safe_step_command()
    assert target_path not in ci_safe_command


@pytest.mark.parametrize("target_path", REMAINING_MODULE_TEST_PATHS)
def test_remaining_module_path_appears_in_exactly_one_ci_workflow_run_command(target_path: str) -> None:
    commands = _ci_workflow_commands()
    hits = [c for c in commands if target_path in c]
    assert len(hits) == 1, f"expected {target_path} in exactly one CI run command, found {len(hits)}: {hits}"


def test_no_remaining_module_path_appears_more_than_once_in_the_same_command() -> None:
    """Each of tests/communication, tests/behavior, tests/mobile must appear
    exactly once as a distinct pytest rootdir argument in the broad step."""
    command = _coverage_instrumented_broad_step_command()
    tokens = command.split()
    for target_path in REMAINING_MODULE_TEST_PATHS:
        assert tokens.count(target_path) == 1, f"{target_path} must appear exactly once as a pytest argument"


# --- A communication/behavior/mobile failure actually blocks the coverage job ---
# (covered generically by test_coverage_step_has_no_failure_suppression above --
# that check already applies to the whole broad step command, which now
# includes these three paths too; no continue-on-error/|| true was added.)


# --- Production coverage source scope was not weakened ---
# (covered generically by test_coverage_source_scope_is_unchanged and
# test_coverage_omit_list_was_not_expanded_to_hide_services_or_app_code
# above -- those assertions hold for the whole [tool.coverage] contract
# regardless of which test paths feed it.)


# --- The ratchet floor was raised again, never lowered back toward the pre-expansion value ---


def test_coverage_ratchet_baseline_was_raised_past_pre_remaining_module_expansion_value() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    new_combined_pct = float(data["combined_pct"])
    assert new_combined_pct >= PRE_REMAINING_MODULE_EXPANSION_BASELINE_COMBINED_PCT, (
        f"new coverage_baseline.json combined_pct ({new_combined_pct}) must not regress below "
        f"the pre-remaining-module-expansion baseline ({PRE_REMAINING_MODULE_EXPANSION_BASELINE_COMBINED_PCT})"
    )


def test_coverage_baseline_commands_include_all_remaining_module_paths() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    commands = data.get("commands", [])
    for target_path in REMAINING_MODULE_TEST_PATHS:
        assert any(target_path in c for c in commands), (
            f"coverage_baseline.json's recorded 'commands' must reflect the real "
            f"measured scope, including {target_path}"
        )


def test_no_stale_communication_behavior_mobile_excluded_claim_in_workflow() -> None:
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow_text.lower()
    stale_patterns = [
        "communication excluded",
        "behavior excluded",
        "mobile excluded",
        "communication kapsam dışı",
        "behavior kapsam dışı",
        "mobile kapsam dışı",
    ]
    for pattern in stale_patterns:
        assert pattern not in lowered, f"stale exclusion claim found in workflow: {pattern!r}"


# =====================================================================
# BYS360 Phase 7 -- Quality/Top-Level CI Coverage Expansion
# (40 previously-deselected tests/quality tests + 32 of 33 loose
# tests/test_*.py files, 573 tests total; tests/load and
# tests/test_live_scope_and_security_static.py deliberately excluded)
#
# NOTE on approach: the ci_safe step's marker expression was NOT widened.
# scripts/quality/bys360_quality9_ci_gate.py::check_workflow hard-requires
# the tests/quality pytest command's "-m" value to be the exact literal
# string "ci_safe" (GateFinding "pytest_not_enforced" otherwise) -- that
# script is outside this expansion's allowed change scope. Instead,
# @pytest.mark.ci_safe (module-level pytestmark) was added directly to the
# 14 tests/quality files containing the 40 verified-safe candidates, so the
# existing, unchanged `-m "ci_safe"` command now naturally selects them.
# =====================================================================

# The baseline in effect before the Phase 7 expansion -- locked here so the
# ratchet can never be silently lowered back toward it by a future edit.
PRE_PHASE7_EXPANSION_BASELINE_COMBINED_PCT = 23.45

QUALITY_CANDIDATE_FILES_NOW_MARKED_CI_SAFE = (
    "tests/quality/test_ai_screen_guide_working_v2_contract.py",
    "tests/quality/test_app_factory_registers_routes_without_duplicate_endpoints.py",
    "tests/quality/test_assistant_js_split_contract_v1.py",
    "tests/quality/test_code_quality_architecture_score_contract_v1.py",
    "tests/quality/test_coverage_campaign.py",
    "tests/quality/test_coverage_regression_gate_phase4n.py",
    "tests/quality/test_effective_menu_facade_v1_contract.py",
    "tests/quality/test_phase2_pytest_invocation_contract_v1.py",
    "tests/quality/test_phase2_test_coverage_evidence_gate_v1.py",
    "tests/quality/test_tckn_crypto_storage_contract_v1.py",
    "tests/quality/test_tckn_crypto_v1a.py",
    "tests/quality/test_ux1_simple_screen_guide_contract.py",
    "tests/quality/test_ux1_simple_screen_guide_v1b_contract.py",
    "tests/quality/test_ux1_top_banner_remove_v1_contract.py",
)

TOP_LEVEL_SAFE_TEST_FILES = (
    "tests/test_10_10_core_static_gate.py",
    "tests/test_ai_analysis_excel_preview_static.py",
    "tests/test_ai_executive_report_static.py",
    "tests/test_ai_recommendation_priority_static.py",
    "tests/test_ai_routes.py",
    "tests/test_claude_phase5_function_signatures.py",
    "tests/test_claude_phase5_template_compilation.py",
    "tests/test_compat_redirects.py",
    "tests/test_datetime_utils.py",
    "tests/test_error_support.py",
    "tests/test_feedback_admin_endpoint_static.py",
    "tests/test_feedback_privacy_static.py",
    "tests/test_feedback_pulse_admin_tab_static.py",
    "tests/test_feedback_pulse_menu_visibility_static.py",
    "tests/test_feedback_pulse_privacy_behavior.py",
    "tests/test_hr_reports_template_no_unpack_static.py",
    "tests/test_live_scope_and_security_static.py",
    "tests/test_module_maturity_scoring.py",
    "tests/test_no_admin_org_units_duplicate_static.py",
    "tests/test_no_duplicate_admin_org_units_static.py",
    "tests/test_performance_archive_visibility_contract.py",
    "tests/test_performance_chain_constitution.py",
    "tests/test_performance_form_guard.py",
    "tests/test_performance_ops_center.py",
    "tests/test_performance_preflight.py",
    "tests/test_performance_publish_guard.py",
    "tests/test_performance_publish_preflight_static.py",
    "tests/test_personel_analizi_dalga7_static.py",
    "tests/test_score100_handover_docs_contract_v1.py",
    "tests/test_shared_cache_store_behavior.py",
    "tests/test_sp_routes_smoke.py",
    "tests/test_team_compare_publish_visibility.py",
    "tests/test_team_compare_service.py",
)

# --- The ci_safe step's command is untouched (still the exact literal
# "ci_safe" the Quality9 gate requires); the 40 previously-deselected tests
# are now selected via a module-level pytestmark on their 14 source files
# instead ---


def test_ci_safe_step_command_is_unchanged_literal_ci_safe_marker() -> None:
    """scripts/quality/bys360_quality9_ci_gate.py::check_workflow requires
    the exact literal marker value "ci_safe" -- Phase 7 must not touch this."""
    command = _ci_safe_step_command()
    assert '-m "ci_safe"' in command


@pytest.mark.parametrize("rel_path", QUALITY_CANDIDATE_FILES_NOW_MARKED_CI_SAFE)
def test_quality_candidate_file_declares_ci_safe_pytestmark(rel_path: str) -> None:
    tree = ast.parse((ROOT / rel_path).read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets
        ):
            found = True
            break
    assert found, f"{rel_path} must declare a module-level pytestmark (pytest.mark.ci_safe)"


@pytest.mark.parametrize("rel_path", QUALITY_CANDIDATE_FILES_NOW_MARKED_CI_SAFE)
def test_quality_candidate_file_is_selected_by_the_unchanged_ci_safe_command(rel_path: str) -> None:
    module_node = rel_path.replace("tests/quality/", "")
    commands = quality9.workflow_run_commands(CI_WORKFLOW.read_text(encoding="utf-8"))
    matches = [c for c in commands if "tests/quality" in c and '"ci_safe"' in c]
    assert len(matches) == 1
    # The file itself is never named in the command (whole-directory
    # collection) -- this asserts the file still lives under the exact
    # tests/quality tree that command scopes to.
    assert rel_path.startswith("tests/quality/")
    assert module_node.endswith(".py")


def test_exactly_14_quality_candidate_files_are_tracked_by_this_contract() -> None:
    assert len(QUALITY_CANDIDATE_FILES_NOW_MARKED_CI_SAFE) == 14
    assert len(set(QUALITY_CANDIDATE_FILES_NOW_MARKED_CI_SAFE)) == 14


# --- The 33 verified-safe top-level files are in the real coverage-measured
# CI scope (Phase 8 resolved the 1 file previously blocked pending marker
# review -- see below) ---


@pytest.mark.parametrize("target_path", TOP_LEVEL_SAFE_TEST_FILES)
def test_top_level_safe_file_is_included_in_coverage_instrumented_ci_step(target_path: str) -> None:
    command = _coverage_instrumented_broad_step_command()
    assert target_path in command, f"{target_path} must be part of the real coverage-instrumented CI step"


# --- BYS360 Phase 8: tests/test_live_scope_and_security_static.py's
# pytest.mark.live/realdb/slow markers were confirmed stale (plain static
# Path.read_text() checks, no app.*/DB/network/subprocess use, no recorded
# rationale in git history) and removed; the file is now included above like
# any other verified-safe top-level file ---


def test_live_scope_file_no_longer_declares_live_realdb_slow_markers() -> None:
    tree = ast.parse((ROOT / "tests" / "test_live_scope_and_security_static.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets
        ):
            raise AssertionError("tests/test_live_scope_and_security_static.py must not declare a pytestmark")


# --- BYS360 Phase 9: tests/architecture/test_survey_live_contract.py's
# pytest.mark.live/realdb/slow markers were confirmed stale by the exact
# same criteria as the Phase 8 file above (plain static Path.read_text()
# check against app/communication/surveys_routes.py, no app.*/DB/network/
# subprocess use, no recorded rationale in git history, same origin commit
# as the Phase 8 file) and removed. Unlike the Phase 8 file, no workflow
# change was needed: this file already lives in tests/architecture, which
# the broad coverage-instrumented step already collects as a whole directory
# with no -m marker filter, so it was already executing in CI regardless of
# its (inert, for that step) markers ---


def test_survey_live_contract_file_no_longer_declares_live_realdb_slow_markers() -> None:
    tree = ast.parse((ROOT / "tests" / "architecture" / "test_survey_live_contract.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets
        ):
            raise AssertionError("tests/architecture/test_survey_live_contract.py must not declare a pytestmark")


def test_survey_live_contract_is_not_explicitly_named_in_any_ci_command() -> None:
    """It must be collected exactly once, implicitly, via the tests/architecture
    directory argument -- never named explicitly (which would risk double
    collection if the directory argument is ever also kept)."""
    commands = _ci_workflow_commands()
    for command in commands:
        assert "test_survey_live_contract.py" not in command


def test_tests_load_is_not_accidentally_included_in_any_ci_step() -> None:
    commands = _ci_workflow_commands()
    for command in commands:
        assert "tests/load" not in command


# --- No duplicate execution, neither against the ci_safe step nor across each other ---


@pytest.mark.parametrize("target_path", TOP_LEVEL_SAFE_TEST_FILES)
def test_top_level_safe_file_is_not_also_run_in_the_ci_safe_step(target_path: str) -> None:
    ci_safe_command = _ci_safe_step_command()
    assert target_path not in ci_safe_command


@pytest.mark.parametrize("target_path", TOP_LEVEL_SAFE_TEST_FILES)
def test_top_level_safe_file_appears_in_exactly_one_ci_workflow_run_command(target_path: str) -> None:
    commands = _ci_workflow_commands()
    hits = [c for c in commands if target_path in c]
    assert len(hits) == 1, f"expected {target_path} in exactly one CI run command, found {len(hits)}: {hits}"


def test_no_top_level_safe_file_appears_more_than_once_in_the_same_command() -> None:
    command = _coverage_instrumented_broad_step_command()
    tokens = command.split()
    for target_path in TOP_LEVEL_SAFE_TEST_FILES:
        assert tokens.count(target_path) == 1, f"{target_path} must appear exactly once as a pytest argument"


def test_exactly_33_top_level_safe_files_are_tracked_by_this_contract() -> None:
    """Guards against silently growing or shrinking the reviewed set without
    updating this contract -- a new tests/test_*.py file must be explicitly
    triaged (Policy A/B/C/D) before being added here or to the workflow."""
    assert len(TOP_LEVEL_SAFE_TEST_FILES) == 33
    assert len(set(TOP_LEVEL_SAFE_TEST_FILES)) == 33


# --- A quality-candidate or top-level-candidate failure actually blocks the
# coverage job (covered generically by test_coverage_step_has_no_failure_
# suppression above -- applies to the whole broad step command regardless of
# which paths feed it; no continue-on-error/|| true was added for Phase 7) ---


# --- Production coverage source scope was not weakened (covered generically
# by test_coverage_source_scope_is_unchanged and
# test_coverage_omit_list_was_not_expanded_to_hide_services_or_app_code above) ---


# --- The ratchet floor was raised again, never lowered back toward the
# pre-Phase-7 value ---


def test_coverage_ratchet_baseline_was_raised_past_pre_phase7_expansion_value() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    new_combined_pct = float(data["combined_pct"])
    assert new_combined_pct > PRE_PHASE7_EXPANSION_BASELINE_COMBINED_PCT, (
        f"new coverage_baseline.json combined_pct ({new_combined_pct}) must be strictly greater "
        f"than the pre-Phase-7 baseline ({PRE_PHASE7_EXPANSION_BASELINE_COMBINED_PCT})"
    )


def test_coverage_baseline_commands_include_unchanged_marker_and_top_level_paths() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    commands = data.get("commands", [])
    assert any('-m "ci_safe"' in c for c in commands), (
        "coverage_baseline.json's recorded 'commands' must reflect the unchanged, literal ci_safe marker"
    )
    for target_path in TOP_LEVEL_SAFE_TEST_FILES:
        assert any(target_path in c for c in commands), (
            f"coverage_baseline.json's recorded 'commands' must reflect the real measured scope, "
            f"including {target_path}"
        )


def test_phase7_baseline_metadata_step_counts_sum_to_total_passed() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    counts = data["test_counts"]
    step1_passed = counts["step1_ci_safe_passed"]
    step2_passed = counts["step2_broader_scope_passed"]
    assert step1_passed + step2_passed == counts["total_passed"], (
        f"step1_ci_safe_passed ({step1_passed}) + step2_broader_scope_passed "
        f"({step2_passed}) must equal total_passed ({counts['total_passed']})"
    )


def test_phase7_baseline_records_the_two_identical_reproducibility_runs() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    repeatability = data["repeatability"]
    assert repeatability["run_1_combined_pct_precise"] == repeatability["run_2_combined_pct_precise"]


def test_no_stale_quality_or_top_level_excluded_claim_in_workflow() -> None:
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow_text.lower()
    stale_patterns = [
        "quality tests excluded",
        "top-level tests excluded",
        "top level tests excluded",
        "kalite testleri kapsam dışı",
        "top-level testler kapsam dışı",
    ]
    for pattern in stale_patterns:
        assert pattern not in lowered, f"stale exclusion claim found in workflow: {pattern!r}"


# =====================================================================
# BYS360 CI Coverage Gate Drift Closure
#
# tests/workflow was deleted in commit 5401195 (dead app/workflow/ package,
# ORPHAN_CONFIRMED) but the CI workflow kept referencing it as a pytest
# positional path for 5 days/12 commits, which made pytest exit 4 ("file or
# directory not found") on that step's ENTIRE argument list -- not just
# skipping 7 tests, but silently zeroing out the whole ~3400-test coverage
# step and every step after it (ratchet, mypy, ops audit, Quality9,
# pip-audit). The pre-existing lock above (CRITICAL_OPERATIONAL_TEST_PATHS)
# did not catch this because it only asserts the *string* "tests/workflow"
# is present in the command -- true even after the directory no longer
# existed on disk. This section closes both gaps: it removes the stale
# path + wires in its replacement contract file, and it adds a
# filesystem-existence check over every CI-referenced test path so this
# class of drift (a real, once-valid path silently going stale) cannot
# recur undetected for ANY path in this command, not just this one.
# =====================================================================

WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH = (
    "tests/quality/test_workflow_orphan_presentation_subsystem_cleanup_contract.py"
)

# Reviewed, human-verified collection count as of the drift-closure commit
# (2026-08-11) -- an exact lock, not a >= floor, because this file's test
# count is a known, reviewed contract value (consistent with this file's
# existing test_exactly_33_.../test_exactly_14_... convention above): if a
# future edit silently adds or removes parametrized cases, this test must
# fail loudly and force a deliberate review of this constant, not pass
# quietly on "at least as many as before".
EXPECTED_WORKFLOW_ORPHAN_CLEANUP_CONTRACT_TEST_COUNT = 82

# This wave (CI Coverage Gate Drift Closure) intentionally does not change
# the coverage ratchet baseline -- see reports/quality/coverage_baseline.json
# and its KEEP_24_16_BASELINE decision (a separate, human-reviewed action).
#
# The BYS360 Coverage Baseline Ratchet Elevation wave (2026-08-11) later DID
# raise this baseline, deliberately and human-reviewed, after 3 independent
# zero-variance fresh measurements (see coverage_baseline.json's own
# _history entry for the full evidence trail) -- so this constant is kept
# as the durable historical floor this baseline must never silently drop
# back to, matching the PRE_*_EXPANSION_BASELINE_COMBINED_PCT convention
# used elsewhere in this file, rather than an exact-equality lock.
PRE_BASELINE_ELEVATION_COMBINED_PCT = 24.16


def _coverage_instrumented_broad_step_tokens() -> list[str]:
    return _coverage_instrumented_broad_step_command().split()


def _ci_safe_step_tokens() -> list[str]:
    return _ci_safe_step_command().split()


def _referenced_test_paths(tokens: list[str]) -> list[str]:
    """Positional pytest path arguments in a CI command -- tokens that look
    like a tests/ path and are not an option flag or an option's value
    (heuristic: preceded by another tests/-looking or bare token, not a
    ``--flag``). Good enough for this workflow's simple space-separated,
    no-shell-quoting command lines."""
    paths = []
    for index, token in enumerate(tokens):
        if not token.startswith("tests/"):
            continue
        previous = tokens[index - 1] if index > 0 else ""
        if previous.startswith("--") and "=" not in previous:
            continue
        paths.append(token)
    return paths


# --- Test: the stale tests/workflow path is gone from every CI-run command ---


def test_tests_workflow_path_is_not_referenced_as_a_pytest_argument_anywhere() -> None:
    for command in _ci_workflow_commands():
        assert "tests/workflow" not in command.split(), (
            f"tests/workflow no longer exists on disk (deleted in commit 5401195) and must not "
            f"be a pytest positional argument in any CI command: {command!r}"
        )


# --- Test: every CI-referenced test path actually exists on disk (the check ---
# --- that would have caught this exact class of drift) ---


def test_every_referenced_test_path_in_the_coverage_instrumented_ci_step_exists_on_disk() -> None:
    for path in _referenced_test_paths(_coverage_instrumented_broad_step_tokens()):
        assert (ROOT / path).exists(), (
            f"CI references {path!r} as a pytest path but it does not exist in the repo -- "
            "this is exactly the drift class that broke this step for tests/workflow"
        )


def test_every_referenced_test_path_in_the_ci_safe_step_exists_on_disk() -> None:
    for path in _referenced_test_paths(_ci_safe_step_tokens()):
        assert (ROOT / path).exists(), f"CI references {path!r} as a pytest path but it does not exist in the repo"


# --- Test: the replacement contract file is wired in explicitly ---


def test_workflow_orphan_cleanup_contract_is_explicitly_named_in_the_coverage_instrumented_ci_step() -> None:
    command = _coverage_instrumented_broad_step_command()
    assert WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH in command.split(), (
        "tests/quality/ is not swept as a whole directory by this step (it is scoped separately, "
        "with a ci_safe marker filter, by the 'Run quality tests' step) -- the replacement contract "
        "file must be named explicitly here to actually execute"
    )


def test_workflow_orphan_cleanup_contract_file_exists_on_disk() -> None:
    assert (ROOT / WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH).is_file()


def test_workflow_orphan_cleanup_contract_is_not_also_selected_by_the_ci_safe_step() -> None:
    """Guards against double execution: if this file ever gains a module-level
    ci_safe pytestmark, the 'Run quality tests' step (tests/quality -m
    "ci_safe") would start collecting it too, on top of the explicit mention
    in the broad step added here."""
    tree = ast.parse((ROOT / WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets
        ):
            raise AssertionError(
                f"{WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH} must not declare a module-level "
                "pytestmark -- it is already explicitly named in the broad coverage step; a "
                "ci_safe marker would make the 'Run quality tests' step collect it a second time"
            )


def test_workflow_orphan_cleanup_contract_appears_in_exactly_one_ci_workflow_run_command() -> None:
    commands = _ci_workflow_commands()
    hits = [c for c in commands if WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH in c.split()]
    assert len(hits) == 1, (
        f"expected {WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH} in exactly one CI run command, "
        f"found {len(hits)}: {hits}"
    )


def test_workflow_orphan_cleanup_contract_collects_exactly_82_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match is not None, f"could not parse a collected-test count from pytest output: {result.stdout!r}"
    collected = int(match.group(1))
    assert collected == EXPECTED_WORKFLOW_ORPHAN_CLEANUP_CONTRACT_TEST_COUNT, (
        f"{WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH} now collects {collected} tests, expected "
        f"{EXPECTED_WORKFLOW_ORPHAN_CLEANUP_CONTRACT_TEST_COUNT} -- if this is a deliberate change, "
        "update EXPECTED_WORKFLOW_ORPHAN_CLEANUP_CONTRACT_TEST_COUNT with a documented reason"
    )


# --- Test: coverage command semantics and downstream gate reachability preserved ---


def test_coverage_command_semantics_unchanged_by_drift_closure() -> None:
    command = _coverage_instrumented_broad_step_command()
    assert "--cov=app" in command
    assert "--cov-append" in command
    assert "--cov-report=xml:reports/quality/coverage.xml" in command
    assert "--cov-fail-under=0" in command


def test_coverage_ratchet_step_still_present_after_drift_closure() -> None:
    commands = _ci_workflow_commands()
    ratchet_hits = [
        c
        for c in commands
        if "scripts/quality/bys360_coverage_ratchet.py" in c
        and "--coverage-xml reports/quality/coverage.xml" in c
        and "--baseline reports/quality/coverage_baseline.json" in c
    ]
    assert len(ratchet_hits) == 1, "coverage ratchet step must still be invoked with its exact XML/baseline paths"


def test_mypy_step_still_present_and_ordered_after_ratchet_step() -> None:
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    step_names = re.findall(r"^\s*- name:\s*(.+)$", workflow_text, flags=re.MULTILINE)
    assert "Coverage ratchet gate" in step_names
    assert "Type check service layer" in step_names
    assert step_names.index("Coverage ratchet gate") < step_names.index("Type check service layer"), (
        "the mypy step must remain reachable AFTER the coverage ratchet gate, not before it "
        "(both are useless if a step earlier in the job silently aborts the whole job)"
    )


def test_quality9_ci_gate_reports_no_coverage_related_findings_after_drift_closure() -> None:
    """Re-runs the same structural gate CI itself calls
    (scripts/quality/bys360_quality9_ci_gate.py) against the fixed workflow --
    none of its coverage/ratchet-related finding codes may appear."""
    coverage_related_codes = {
        "pytest_not_enforced",
        "coverage_measurement_not_enforced",
        "coverage_xml_not_enforced",
        "coverage_ratchet_not_enforced",
        "missing_coverage_ratchet_script",
        "missing_coverage_baseline",
    }
    findings = quality9.check_workflow(ROOT, max_broad_except=2300)
    found_codes = {finding.code for finding in findings if finding.code in coverage_related_codes}
    assert not found_codes, f"drift closure introduced new Quality9 coverage findings: {found_codes}"


def test_no_continue_on_error_introduced_by_drift_closure() -> None:
    """Duplicates the intent of test_coverage_step_has_no_failure_suppression
    above (whole-file check) as an explicit, drift-closure-scoped assertion:
    fixing the stale path must not come with a quietly loosened gate."""
    workflow_text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "continue-on-error" not in workflow_text


# --- Test: this wave's own explicit non-goal -- the coverage baseline is unchanged ---


def test_coverage_ratchet_baseline_was_raised_past_pre_elevation_wave_value() -> None:
    """CI Coverage Gate Drift Closure itself did not touch the baseline
    (KEEP_24_16_BASELINE); the later Coverage Baseline Ratchet Elevation wave
    is the one that deliberately raised it -- this must never silently drop
    back to (or below) the pre-elevation floor."""
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    new_combined_pct = float(data["combined_pct"])
    assert new_combined_pct > PRE_BASELINE_ELEVATION_COMBINED_PCT, (
        f"new coverage_baseline.json combined_pct ({new_combined_pct}) must be strictly greater "
        f"than the pre-elevation baseline ({PRE_BASELINE_ELEVATION_COMBINED_PCT})"
    )


# =====================================================================
# BYS360 Coverage Baseline Ratchet Elevation (2026-08-11)
# =====================================================================


def test_coverage_baseline_tolerance_unchanged_by_elevation() -> None:
    """The elevation wave's own stated non-goal: tolerance_pct is a separate,
    already-reviewed safety-margin mechanism and must not be silently
    widened or narrowed alongside a baseline raise."""
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    assert float(data["tolerance_pct"]) == 0.5


def test_coverage_baseline_effective_threshold_still_well_above_pre_elevation_floor() -> None:
    """Locks in that raising the baseline actually tightened real regression
    protection: the new effective pass threshold (baseline - tolerance) must
    itself sit comfortably above the pre-elevation baseline, not just above
    the pre-elevation baseline's own (looser) effective threshold."""
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    effective_threshold = float(data["combined_pct"]) - float(data["tolerance_pct"])
    assert effective_threshold > PRE_BASELINE_ELEVATION_COMBINED_PCT, (
        f"new effective threshold ({effective_threshold}) must exceed the pre-elevation "
        f"baseline ({PRE_BASELINE_ELEVATION_COMBINED_PCT}) for this to be a real tightening"
    )


# =====================================================================
# BYS360 OpenAPI CI Assurance Debt Closure
#
# tests/quality/test_openapi_workflow_drift_cleanup_contract.py (44 tests,
# added in commit 7a605b2 alongside docs/api/openapi_draft.json's removal of
# 12 dead app/workflow/ OpenAPI path entries) carried no ci_safe marker and
# was named nowhere in either CI workflow -- 0 of its 44 tests ever ran in
# real CI. Unlike the tests/workflow drift closed above, this was not a
# stale-path bug (the file's own path was always valid); it was simply never
# wired in when it was written.
#
# Ownership: of tests/quality's 28 files, 26 (93%) already carry the
# ci_safe marker and are collected by Step1 (`tests/quality -m "ci_safe"`)
# with zero YAML changes -- this file and its 82-test sibling
# (test_workflow_orphan_presentation_subsystem_cleanup_contract.py, already
# wired into Step2 in the prior wave) were the only two exceptions. Four
# other ci_safe-marked tests/quality files already use the identical
# subprocess/isolated-create_app()-probe pattern this file uses
# (test_phase12b_route_ownership_contract.py, test_route_conflict_runtime_
# contract.py, test_president_approvals_route_contract.py, test_app_
# factory_registers_routes_without_duplicate_endpoints.py) -- proving no
# technical barrier to Step1. This file's own measured runtime (~0.12s/test)
# is faster than Step1's current average (~0.30s/test). OPENAPI_CONTRACT_
# CANONICAL_CI_OWNER = STEP1: the fix was a single pytestmark line in the
# test file itself, not a workflow YAML change -- the Step1 command
# (`tests/quality -m "ci_safe"`) is unchanged by this wave.
# =====================================================================

OPENAPI_CLEANUP_CONTRACT_PATH = "tests/quality/test_openapi_workflow_drift_cleanup_contract.py"
EXPECTED_OPENAPI_CLEANUP_CONTRACT_TEST_COUNT = 44


def test_openapi_cleanup_contract_declares_ci_safe_pytestmark() -> None:
    tree = ast.parse((ROOT / OPENAPI_CLEANUP_CONTRACT_PATH).read_text(encoding="utf-8"))
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets
        ):
            found = True
            break
    assert found, f"{OPENAPI_CLEANUP_CONTRACT_PATH} must declare a module-level pytestmark (pytest.mark.ci_safe)"


def test_openapi_cleanup_contract_file_exists_on_disk() -> None:
    assert (ROOT / OPENAPI_CLEANUP_CONTRACT_PATH).is_file()


def test_openapi_cleanup_contract_is_selected_by_the_unchanged_ci_safe_command() -> None:
    """Mirrors test_quality_candidate_file_is_selected_by_the_unchanged_ci_safe_command
    above (Phase 7 precedent): the file itself is never named in the ci_safe
    command (whole-directory-plus-marker collection) -- this asserts it still
    lives under the exact tests/quality tree that command scopes to, and that
    the ci_safe command itself is untouched."""
    commands = _ci_workflow_commands()
    matches = [c for c in commands if "tests/quality" in c and '"ci_safe"' in c]
    assert len(matches) == 1
    assert OPENAPI_CLEANUP_CONTRACT_PATH.startswith("tests/quality/")


def test_openapi_cleanup_contract_is_not_explicitly_named_in_the_coverage_instrumented_ci_step() -> None:
    """Guards against double execution the other way around: since this file
    is Step1-owned (via ci_safe marker, not explicit naming), it must never
    also be named in Step2's command -- that would run all 44 tests twice
    per CI run."""
    command = _coverage_instrumented_broad_step_command()
    assert OPENAPI_CLEANUP_CONTRACT_PATH not in command.split()


def test_openapi_cleanup_contract_collects_exactly_44_tests() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", OPENAPI_CLEANUP_CONTRACT_PATH],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match is not None, f"could not parse a collected-test count from pytest output: {result.stdout!r}"
    collected = int(match.group(1))
    assert collected == EXPECTED_OPENAPI_CLEANUP_CONTRACT_TEST_COUNT, (
        f"{OPENAPI_CLEANUP_CONTRACT_PATH} now collects {collected} tests, expected "
        f"{EXPECTED_OPENAPI_CLEANUP_CONTRACT_TEST_COUNT} -- if this is a deliberate change, "
        "update EXPECTED_OPENAPI_CLEANUP_CONTRACT_TEST_COUNT with a documented reason"
    )


# =====================================================================
# BYS360 Coverage Baseline Metadata Consistency Fix (2026-08-11)
#
# The elevation wave above correctly updated the ACTIVE combined_pct/lines/
# branches/measured_at, but left coverage_baseline.json's own commands/
# test_counts/repeatability fields describing the superseded Phase 9
# measurement (stale tests/workflow token; Phase-9-era counts and
# reproducibility numbers under a now-27.62 baseline). Unlike
# previous_baseline (whose entire purpose is to hold the immediately-
# preceding, historical snapshot), commands/test_counts/repeatability
# describe the ACTIVE baseline and must track it. This section locks that
# in going forward -- distinct from the existing tests above, which check
# the CI *workflow YAML*, not coverage_baseline.json's own recorded copy
# of those commands.
# =====================================================================


def test_coverage_baseline_pinned_at_current_elevated_value() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    assert data["combined_pct"] == 27.62
    assert data["combined_pct_precise"] == pytest.approx(27.619308622802812)


def test_coverage_baseline_recorded_commands_reference_no_stale_tests_workflow_path() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    for command in data.get("commands", []):
        assert "tests/workflow" not in command.split(), (
            "coverage_baseline.json's own recorded 'commands' must not reference the deleted "
            "tests/workflow path -- it describes the ACTIVE baseline measurement, not a historical one"
        )


def test_coverage_baseline_recorded_commands_paths_exist_on_disk() -> None:
    """coverage_baseline.json's own 'commands' field, not the CI workflow YAML
    (already covered above) -- these must independently stay truthful."""
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    for command in data.get("commands", []):
        for token in command.split():
            if token.startswith("tests/") and not (token.startswith("--")):
                assert (ROOT / token).exists(), f"coverage_baseline.json references {token!r} but it does not exist"


def test_coverage_baseline_recorded_commands_include_current_workflow_cleanup_contract() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    commands = data.get("commands", [])
    assert any(WORKFLOW_ORPHAN_CLEANUP_CONTRACT_PATH in c.split() for c in commands)


def test_coverage_baseline_recorded_commands_do_not_explicitly_name_the_step1_owned_openapi_contract() -> None:
    """The OpenAPI contract is Step1-owned via ci_safe marker (see the
    OPENAPI_CONTRACT_CANONICAL_CI_OWNER = STEP1 section above) -- it must
    never appear as an explicit token in the recorded Step2 command, which
    would misrepresent its real wiring mechanism."""
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    commands = data.get("commands", [])
    assert not any(OPENAPI_CLEANUP_CONTRACT_PATH in c.split() for c in commands)


def test_coverage_baseline_test_counts_match_current_step_totals() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    counts = data["test_counts"]
    assert counts["step1_ci_safe_passed"] + counts["step1_ci_safe_skipped"] == counts["step1_ci_safe_selected"]
    assert (
        counts["step2_broader_scope_passed"] + counts["step2_broader_scope_skipped"]
        == counts["step2_broader_scope_selected"]
    )
    step2_sub_total = sum(v for k, v in counts.items() if k.startswith("step2_") and k.endswith("_contribution"))
    assert step2_sub_total == counts["step2_broader_scope_selected"], (
        f"step2_*_contribution fields sum to {step2_sub_total}, expected "
        f"{counts['step2_broader_scope_selected']} (step2_broader_scope_selected)"
    )


def test_coverage_baseline_repeatability_is_zero_variance_across_all_recorded_runs() -> None:
    data = json.loads(COVERAGE_BASELINE.read_text(encoding="utf-8"))
    rep = data["repeatability"]
    run_values = [v for k, v in rep.items() if k.startswith("run_") and k.endswith("_combined_pct_precise")]
    assert len(run_values) >= 3, "expected at least 3 recorded independent runs for the elevated baseline"
    assert min(run_values) == max(run_values) == data["combined_pct_precise"], (
        "all recorded repeatability runs must be identical to each other and to the active "
        "combined_pct_precise -- zero variance is the elevation wave's own documented finding"
    )
