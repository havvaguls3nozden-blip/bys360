"""BYS360 mypy archive-exclude scope contract.

Locks in the 2026-07-27 archive mypy policy: historical files under
``scripts/archive/`` are excluded from the official mypy gate, while every
other active source tree (``app/``, ``tests/``, ``scripts/quality/``,
``scripts/communication/`` and any other active scripts subdirectory) stays
in scope. Guards against the exclude regex silently widening to swallow the
whole ``scripts/`` tree, and against someone narrowing it back to nothing.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = ROOT / "pyproject.toml"


def _mypy_exclude_pattern() -> re.Pattern[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    exclude = data["tool"]["mypy"]["exclude"]
    assert isinstance(exclude, str), "tool.mypy.exclude must be a single regex string"
    return re.compile(exclude)


def test_mypy_files_scope_still_includes_scripts() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    files = data["tool"]["mypy"]["files"]
    assert files == ["app", "tests", "scripts"], (
        "the CI mypy command (`mypy app tests scripts`) must keep matching "
        "tool.mypy.files; narrowing this list is a separate, explicit "
        "decision and out of scope for the archive-exclude policy"
    )


def test_archive_paths_are_excluded() -> None:
    pattern = _mypy_exclude_pattern()
    sample_archive_paths = [
        "scripts/archive/pre_handover_20260708/quality/bys360_score100_quality_gate_v1.py",
        "scripts/archive/quality/phase2y-wave1/analyze_p11_b_mobile_routes_inventory_v1.py",
        "scripts/archive/quality/phase2y-wave2/plan_p11_refactor_v1.py",
    ]
    for rel in sample_archive_paths:
        assert pattern.search(rel), f"expected mypy exclude to match archive path: {rel}"


def test_active_script_paths_are_not_excluded() -> None:
    pattern = _mypy_exclude_pattern()
    sample_active_paths = [
        "scripts/quality/bys360_score100_quality_gate_v1.py",
        "scripts/quality/bys360_secret_repo_gate.py",
        "scripts/communication/send_daily_pulse_check_mail.py",
        "scripts/windows/repair_bys360_score100_quality_gate_v1.ps1",
        "scripts/release/build_bys360_safe_release.py",
    ]
    for rel in sample_active_paths:
        assert not pattern.search(rel), (
            f"mypy exclude must NOT match active script path: {rel} "
            "(the archive-exclude regex must not swallow the whole scripts/ tree)"
        )


def test_app_and_tests_are_not_excluded() -> None:
    pattern = _mypy_exclude_pattern()
    sample_paths = [
        "app/__init__.py",
        "app/services/executive_mail_center.py",
        "tests/architecture/test_score100_active_canonical_source_contract.py",
        "tests/services/test_mobile_service_base_phase4at.py",
    ]
    for rel in sample_paths:
        assert not pattern.search(rel), f"mypy exclude must NOT match: {rel}"


def test_existing_exclusions_are_preserved() -> None:
    pattern = _mypy_exclude_pattern()
    for rel in ("migrations/0001_initial.py", "app/static/js/app.js", "app/templates/base.html"):
        assert pattern.search(rel), f"expected pre-existing mypy exclude to still match: {rel}"
