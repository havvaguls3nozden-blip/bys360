from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_ci_safe_scope_is_explicit_and_limited_to_quality_tests() -> None:
    text = read("tests/conftest.py")
    assert "BYS360_QUALITY9_CI_SAFE_SCOPE_DISCIPLINE_START" in text
    assert "tests/quality" in text.replace("\\", "/")
    assert "item.add_marker(ci_safe_marker)" not in text
    assert "pytest_deselected" in text


def test_ci_workflow_runs_deterministic_quality_scope() -> None:
    text = read(".github/workflows/bys360-ci.yml").replace("'", '"')
    assert "name: Run tests" in text
    assert 'python -m pytest tests/quality -m "ci_safe" --tb=short -q' in text
    assert "--max-broad-except 2300" in text
    assert "--source-paths app config.py wsgi.py run.py" in text


def test_quality9_gate_supports_current_and_legacy_cli_arguments() -> None:
    text = read("scripts/quality/bys360_quality9_ci_gate.py")
    assert 'parser.add_argument("--root"' in text
    assert 'parser.add_argument("--project-root"' in text
    assert 'parser.add_argument("--max-broad-except"' in text
    assert "tests/quality" in text


def test_compat_endpoint_cleanup_module_is_available() -> None:
    path = ROOT / "app" / "compat_endpoint_cleanup.py"
    assert path.exists()
    text = path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(text)
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert "_soft_redirect" in function_names
    assert "redirect" in text
    assert "url_for" in text


def test_app_sources_have_no_print_calls() -> None:
    offenders: list[str] = []
    for path in (ROOT / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                offenders.append(str(path.relative_to(ROOT)))
                break
    assert offenders == []
