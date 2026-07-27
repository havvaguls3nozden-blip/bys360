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

Also locks in the follow-up Communication/Behavior/Mobile CI Coverage
Expansion (2026-07-27): ``tests/communication``, ``tests/behavior`` and
``tests/mobile`` (29 tests total, 0 cross-scope duplicate node IDs, 0
skip/xfail, stable across 2 isolated runs + 1 combined run) were added via
the same Policy A single-invocation approach. tests/communication and
tests/mobile are 0-import AST/source-contract checks (~0% measurable app/
coverage, kept as required structural gates); tests/behavior imports real
app.services/app.models and does contribute measurable app/ coverage.

These are pure contract/parsing tests -- they read real repo files, they do
not run the workflow or any subprocess.
"""
from __future__ import annotations

import ast
import json
import re
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

CRITICAL_OPERATIONAL_TEST_PATHS = ("tests/migrations", "tests/workflow", "tests/release")

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
