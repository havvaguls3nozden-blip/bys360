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

These are pure contract/parsing tests -- they read real repo files, they do
not run the workflow or any subprocess.
"""
from __future__ import annotations

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
