"""BYS360 Score100 active-canonical-source contract.

Locks in the 2026-07-27 canonicalization: the real Score100 implementation now
lives at its active path and no longer depends on the archived snapshot at
runtime. Before this change, ``scripts/quality/bys360_score100_quality_gate_v1.py``
was a ``runpy.run_path()`` shim delegating to
``scripts/archive/pre_handover_20260708/quality/bys360_score100_quality_gate_v1.py``.

This test is intentionally implementation-detail-agnostic: it does not assert
on line counts, function counts, or a content hash, since the active file's
internals may legitimately change over time (e.g. further mypy/ruff cleanup).
It only asserts the structural contract: no runtime dependency on the archive,
and the workflow/repair-script wiring points at the active file.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_SCORE100 = ROOT / "scripts" / "quality" / "bys360_score100_quality_gate_v1.py"
ARCHIVE_SCORE100 = (
    ROOT
    / "scripts"
    / "archive"
    / "pre_handover_20260708"
    / "quality"
    / "bys360_score100_quality_gate_v1.py"
)
REPAIR_PS1 = ROOT / "scripts" / "windows" / "repair_bys360_score100_quality_gate_v1.ps1"
SCORE100_WORKFLOW = ROOT / ".github" / "workflows" / "bys360-score100-quality-gate-v1.yml"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_active_score100_file_exists() -> None:
    assert ACTIVE_SCORE100.is_file(), f"missing active Score100 gate: {ACTIVE_SCORE100}"


def test_archive_score100_snapshot_still_exists() -> None:
    # This test's purpose is not to modify or retire the archived snapshot -
    # it must still be present as a historical record.
    assert ARCHIVE_SCORE100.is_file(), f"archived Score100 snapshot missing: {ARCHIVE_SCORE100}"


def test_active_score100_does_not_import_runpy() -> None:
    tree = _parse(ACTIVE_SCORE100)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name != "runpy" for alias in node.names), (
                "active Score100 gate must not import runpy (that would mean "
                "it delegates to another file at runtime instead of being "
                "the real implementation)"
            )
        if isinstance(node, ast.ImportFrom):
            assert node.module != "runpy", (
                "active Score100 gate must not import from runpy"
            )


def test_active_score100_does_not_reference_file_dunder() -> None:
    tree = _parse(ACTIVE_SCORE100)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "__file__":
            raise AssertionError(
                "active Score100 gate must not use __file__ for path "
                "resolution; its own --project-root argument must be the "
                "only project-root source (this is what makes it safe to "
                "run from its active path)"
            )


def test_active_score100_has_no_runtime_archive_path_reference() -> None:
    """The archive path may appear in comments/docstrings (history), but not
    as part of any executable expression (string literal used in a call, an
    f-string built into a Path(...), etc.)."""
    tree = _parse(ACTIVE_SCORE100)
    marker = "scripts/archive"

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.violations: list[int] = []

        def visit_Constant(self, node: ast.Constant) -> None:  # noqa: N802
            if isinstance(node.value, str) and marker in node.value:
                # A bare string constant is only a violation if it is not the
                # module docstring (first statement of the module body).
                self.violations.append(node.lineno)
            self.generic_visit(node)

    module_docstring_line = None
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        module_docstring_line = tree.body[0].value.lineno

    visitor = _Visitor()
    visitor.visit(tree)
    non_docstring_hits = [ln for ln in visitor.violations if ln != module_docstring_line]
    assert not non_docstring_hits, (
        f"active Score100 gate references '{marker}' outside its module "
        f"docstring at line(s) {non_docstring_hits}; this would mean it "
        "still depends on the archived snapshot at runtime"
    )


def test_score100_workflow_uses_active_path() -> None:
    if not SCORE100_WORKFLOW.is_file():
        return
    text = SCORE100_WORKFLOW.read_text(encoding="utf-8")
    assert "scripts/archive" not in text, (
        "Score100 workflow must not reference the archive path directly"
    )


def test_repair_script_targets_active_path_only() -> None:
    if not REPAIR_PS1.is_file():
        return
    text = REPAIR_PS1.read_text(encoding="utf-8")
    assert "scripts/archive" not in text and "scripts\\archive" not in text, (
        "repair script must not reference the archive path"
    )
    assert re.search(r"scripts[\\/]quality[\\/]bys360_score100_quality_gate_v1\.py", text), (
        "repair script must resolve the gate script at the active "
        "scripts/quality path"
    )
