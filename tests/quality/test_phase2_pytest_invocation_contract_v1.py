from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe


def test_phase2_windows_test_runner_uses_venv_python_m_pytest() -> None:
    root = Path(__file__).resolve().parents[2]
    runner = root / "scripts" / "windows" / "run_bys360_tests.ps1"

    assert runner.exists(), "Faz 2 test runner eksik."

    text = runner.read_text(encoding="utf-8")

    assert ".venv\\Scripts\\python.exe" in text
    assert "-m pytest" in text
    assert "& $Python -m pytest @PytestArgs" in text
    assert "where.exe pytest" not in text
    assert "pytest.exe" not in text
