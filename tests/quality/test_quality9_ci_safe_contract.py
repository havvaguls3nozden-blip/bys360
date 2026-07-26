from __future__ import annotations

import ast
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.quality import bys360_quality9_ci_gate as quality9

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]

VALID_WORKFLOW = """
name: Run tests
jobs:
  quality:
    steps:
      - name: Run quality tests
        run: python -m pytest tests/quality -m "ci_safe" --cov=app --cov-report= --cov-fail-under=0 -q
      - name: Run broader tests
        run: python -m pytest tests/integration --cov=app --cov-append --cov-report=xml:reports/quality/coverage.xml --cov-fail-under=0 -q
      - name: Coverage ratchet gate
        run: python scripts/quality/bys360_coverage_ratchet.py --coverage-xml reports/quality/coverage.xml --baseline reports/quality/coverage_baseline.json
      - name: Operations audit
        run: python scripts/quality/bys360_ops_audit.py --source-paths app config.py wsgi.py run.py --max-broad-except 2300
"""


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _finding_codes(findings: list[quality9.GateFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _write_workflow_fixture(tmp_path: Path, workflow: str) -> Path:
    workflow_path = tmp_path / ".github" / "workflows" / "bys360-ci.yml"
    workflow_path.parent.mkdir(parents=True)
    workflow_path.write_text(textwrap.dedent(workflow), encoding="utf-8")

    ratchet = tmp_path / "scripts" / "quality" / "bys360_coverage_ratchet.py"
    ratchet.parent.mkdir(parents=True)
    ratchet.write_text("# fixture\n", encoding="utf-8")

    baseline = tmp_path / "reports" / "quality" / "coverage_baseline.json"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("{}\n", encoding="utf-8")
    return tmp_path


def test_ci_safe_scope_is_explicit_and_limited_to_quality_tests() -> None:
    assert quality9.check_ci_safe_hook(ROOT) == []


def test_ci_workflow_runs_deterministic_quality_scope() -> None:
    assert quality9.check_workflow(ROOT, 2300) == []


def test_quality9_rejects_workflow_without_pytest(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace(
        'run: python -m pytest tests/quality -m "ci_safe" --cov=app '
        "--cov-report= --cov-fail-under=0 -q",
        "run: echo quality tests omitted",
    )
    root = _write_workflow_fixture(tmp_path, workflow)

    codes = _finding_codes(quality9.check_workflow(root, 2300))

    assert "pytest_not_enforced" in codes


def test_quality9_rejects_pytest_and_ratchet_mentions_in_comments(tmp_path: Path) -> None:
    workflow = """
    name: Comment-only workflow
    jobs:
      quality:
        steps:
          # run: python -m pytest tests/quality -m ci_safe --cov=app
          # run: python scripts/quality/bys360_coverage_ratchet.py --coverage-xml reports/quality/coverage.xml --baseline reports/quality/coverage_baseline.json
          - name: No quality enforcement
            run: echo comments are not executable
    """
    root = _write_workflow_fixture(tmp_path, workflow)

    codes = _finding_codes(quality9.check_workflow(root, 2300))

    assert "pytest_not_enforced" in codes
    assert "coverage_measurement_not_enforced" in codes
    assert "coverage_ratchet_not_enforced" in codes


def test_quality9_rejects_ci_safe_pytest_without_app_coverage(tmp_path: Path) -> None:
    workflow = VALID_WORKFLOW.replace("--cov=app --cov-report=", "--cov-report=")
    root = _write_workflow_fixture(tmp_path, workflow)

    codes = _finding_codes(quality9.check_workflow(root, 2300))

    assert "coverage_measurement_not_enforced" in codes


@pytest.mark.parametrize(
    "ratchet_command",
    [
        "run: echo ratchet omitted",
        (
            "run: python scripts/quality/bys360_coverage_ratchet.py "
            "--coverage-xml reports/quality/coverage.xml "
            "--baseline reports/quality/wrong-baseline.json"
        ),
    ],
)
def test_quality9_rejects_missing_or_wrong_ratchet(
    tmp_path: Path,
    ratchet_command: str,
) -> None:
    expected = (
        "run: python scripts/quality/bys360_coverage_ratchet.py "
        "--coverage-xml reports/quality/coverage.xml "
        "--baseline reports/quality/coverage_baseline.json"
    )
    root = _write_workflow_fixture(
        tmp_path,
        VALID_WORKFLOW.replace(expected, ratchet_command),
    )

    codes = _finding_codes(quality9.check_workflow(root, 2300))

    assert "coverage_ratchet_not_enforced" in codes


def test_ci_safe_comments_do_not_replace_native_marker_contract(tmp_path: Path) -> None:
    conftest = tmp_path / "tests" / "conftest.py"
    conftest.parent.mkdir(parents=True)
    conftest.write_text(
        "# pytest_collection_modifyitems\n# pytest_deselected\n# ci_safe\n",
        encoding="utf-8",
    )
    quality_test = tmp_path / "tests" / "quality" / "test_quality9_ci_safe_contract.py"
    quality_test.parent.mkdir(parents=True)
    quality_test.write_text("# pytestmark = pytest.mark.ci_safe\n", encoding="utf-8")
    (tmp_path / "pytest.ini").write_text("[pytest]\nmarkers =\n", encoding="utf-8")

    codes = _finding_codes(quality9.check_ci_safe_hook(tmp_path))

    assert "ci_safe_marker_not_registered" in codes
    assert "quality9_tests_not_ci_safe" in codes


def test_quality9_gate_supports_current_and_legacy_cli_arguments(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["bys360_quality9_ci_gate.py", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        quality9.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--root" in help_text
    assert "--project-root" in help_text
    assert "--max-broad-except" in help_text


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
