"""TD-032 closure -- PostgreSQL 15 migration-integrity CI enforcement contract.

Locks in that the real-PostgreSQL migration-integrity gate
(``scripts/quality/bys360_postgres_migration_integrity_gate.py``) is not
just a local ad-hoc script but genuinely wired into
``.github/workflows/bys360-ci.yml``: a ``postgres:15`` service container is
present, the gate is actually invoked (not merely referenced in a comment),
it does not use production secrets, it is not marked ``continue-on-error``
(an allow-failure step would make the gate decorative), and the pre-existing
Step1/Step2 pytest commands are unchanged by this addition -- this is meant
to be a purely additive CI change, not a rewrite of the existing gates.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "bys360-ci.yml"

STEP1_COMMAND_NEEDLE = 'pytest tests/quality -m "ci_safe"'
STEP2_COMMAND_NEEDLE = "pytest tests/integration tests/architecture tests/security"


def _workflow_text() -> str:
    return CI_WORKFLOW.read_text(encoding="utf-8")


def test_ci_workflow_file_exists() -> None:
    assert CI_WORKFLOW.exists(), f"{CI_WORKFLOW} not found."


def test_postgres_15_service_is_declared() -> None:
    text = _workflow_text()
    assert "services:" in text
    assert "postgres:" in text
    assert "image: postgres:15" in text


def test_postgres_service_has_a_healthcheck() -> None:
    text = _workflow_text()
    assert "pg_isready" in text, "postgres service must gate readiness with pg_isready (or equivalent)."


def test_migration_integrity_gate_script_is_actually_invoked() -> None:
    text = _workflow_text()
    assert "run: python scripts/quality/bys360_postgres_migration_integrity_gate.py" in text, (
        "The gate script must be genuinely invoked as a `run:` command, not just mentioned "
        "in a comment."
    )


def test_migration_integrity_gate_script_exists() -> None:
    gate_path = REPO_ROOT / "scripts" / "quality" / "bys360_postgres_migration_integrity_gate.py"
    assert gate_path.exists(), f"{gate_path} referenced by CI but missing."


def test_gate_env_var_is_wired_and_points_at_the_ci_service_host() -> None:
    text = _workflow_text()
    assert "BYS360_REALDB_MIGRATION_TEST_URL:" in text
    assert "@postgres:5432/bys360_migration_test_ci" in text


def test_no_production_secret_pattern_used_for_the_ci_postgres_credentials() -> None:
    """The CI-only disposable password is a literal, self-documenting
    placeholder hardcoded in the workflow -- not read from a real secret
    store or an ``.env`` file (this repo's real secrets live in an
    untracked ``.env``, never committed and never referenced here)."""
    text = _workflow_text()
    assert "bys360_ci_test_only_password" in text
    assert ".env" not in text
    assert "${{ secrets." not in text, (
        "This workflow defines no GitHub Actions repository secrets to read; the "
        "PostgreSQL credentials are disposable, CI-local, and hardcoded on purpose."
    )


def test_migration_integrity_gate_step_is_not_allow_failure() -> None:
    """An allow-failure migration gate would be decorative, not enforcement."""
    text = _workflow_text()
    gate_step_start = text.index("- name: PostgreSQL 15 migration integrity gate")
    next_step_start = text.find("\n      - name:", gate_step_start + 1)
    gate_step_text = text[gate_step_start : next_step_start if next_step_start != -1 else len(text)]
    assert "continue-on-error" not in gate_step_text


def test_step1_pytest_command_is_unchanged() -> None:
    text = _workflow_text()
    assert STEP1_COMMAND_NEEDLE in text


def test_step2_pytest_command_is_unchanged() -> None:
    text = _workflow_text()
    assert STEP2_COMMAND_NEEDLE in text


def test_existing_named_steps_are_all_still_present() -> None:
    """Every step name this workflow had before the TD-032 PostgreSQL
    addition is still present, unrenamed and unremoved -- this addition
    only inserts new steps, it does not touch any existing one."""
    text = _workflow_text()
    pre_existing_step_names = (
        "Checkout",
        "Set up Python 3.12",
        "Install dependencies",
        "BYS360 secret/repo gate",
        "Build safe release audit",
        "Ruff full-select gate (E,F,I,UP,B,SIM)",
        "Compile Python source",
        "BYS360 safe release audit",
        "Run quality tests",
        "Run integration and architecture tests",
        "Coverage ratchet gate",
        "Type check service layer",
        "BYS360 operations audit",
        "BYS360 Quality 9 CI contract gate",
        "Ruff syntax/import sanity",
        "Dependency vulnerability audit",
        "Upload quality reports",
    )
    for step_name in pre_existing_step_names:
        assert f"- name: {step_name}" in text, f"Pre-existing step {step_name!r} is missing or renamed."


def test_new_steps_do_not_shadow_an_existing_step_name() -> None:
    text = _workflow_text()
    new_step_names = (
        "Create disposable PostgreSQL 15 migration-test database",
        "PostgreSQL 15 migration integrity gate",
    )
    for step_name in new_step_names:
        assert text.count(f"- name: {step_name}") == 1
