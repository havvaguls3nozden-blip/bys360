from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import List, Tuple


TARGET_RELATIVE = Path("app/services/performance/hierarchy.py")


def _read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def _has_logging_import(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "logging":
                    return True
        if isinstance(node, ast.ImportFrom):
            if node.module == "logging":
                return True
    return False


def _uses_logging_name(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "logging":
            return True
    return False


def _insertion_line_after_docstring_future_and_encoding(text: str) -> int:
    """Return 0-based insertion line for import logging."""
    lines = text.splitlines()
    idx = 0

    # Shebang / coding comment block
    while idx < len(lines) and (
        lines[idx].startswith("#!") or "coding" in lines[idx][:80]
    ):
        idx += 1

    # Module docstring
    probe = "\n".join(lines[idx:])
    try:
        mod = ast.parse(text)
        if mod.body and isinstance(mod.body[0], ast.Expr) and isinstance(getattr(mod.body[0], "value", None), ast.Constant) and isinstance(mod.body[0].value.value, str):
            idx = mod.body[0].end_lineno or idx
    except SyntaxError:
        pass

    # __future__ imports must stay first after docstring/comments
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("from __future__ import "):
            idx += 1
            continue
        if stripped == "":
            idx += 1
            continue
        break

    return idx


def ensure_logging_import(path: Path) -> Tuple[bool, str]:
    text = _read_text(path)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return False, f"syntax_error:{exc}"

    if not _uses_logging_name(tree):
        return False, "logging_not_used"

    if _has_logging_import(tree):
        return False, "already_has_import"

    lines = text.splitlines()
    insert_at = _insertion_line_after_docstring_future_and_encoding(text)

    # Avoid duplicate blank-line noise: insert import logging and preserve readable spacing.
    new_lines = list(lines)
    new_lines.insert(insert_at, "import logging")

    new_text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    _write_text(path, new_text)

    # Validate after write.
    ast.parse(_read_text(path))
    return True, "added_import_logging"


def scan_logging_import_contract(project_root: Path) -> List[str]:
    findings: List[str] = []
    for path in (project_root / "app").rglob("*.py"):
        try:
            text = _read_text(path)
            tree = ast.parse(text)
        except Exception as exc:
            findings.append(f"{path.relative_to(project_root)}: parse_failed: {exc}")
            continue

        if _uses_logging_name(tree) and not _has_logging_import(tree):
            findings.append(f"{path.relative_to(project_root)}: uses logging without import logging")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["all", "patch", "audit"], default="all")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_RELATIVE
    if not target.exists():
        raise SystemExit(f"Target file not found: {target}")

    changed = []
    notes = []

    if args.mode in {"all", "patch"}:
        did_change, status = ensure_logging_import(target)
        notes.append({"file": str(TARGET_RELATIVE), "status": status})
        if did_change:
            changed.append(str(TARGET_RELATIVE))

        # Defensive scan: fix same bug anywhere under app if future cleanup created it.
        for path in (project_root / "app").rglob("*.py"):
            if path == target:
                continue
            text = _read_text(path)
            if "logging" not in text:
                continue
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            if _uses_logging_name(tree) and not _has_logging_import(tree):
                did_change, status = ensure_logging_import(path)
                notes.append({"file": str(path.relative_to(project_root)), "status": status})
                if did_change:
                    changed.append(str(path.relative_to(project_root)))

    findings = scan_logging_import_contract(project_root)
    ok = not findings

    report = {
        "package": "BYS360_QUALITY9_PERFORMANCE_HIERARCHY_LOGGING_HOTFIX_V3",
        "ok": ok,
        "changed": changed,
        "notes": notes,
        "finding_count": len(findings),
        "findings": findings,
    }

    report_path = project_root / "reports" / "quality" / "BYS360_QUALITY9_LOGGING_IMPORT_HOTFIX_V3_REPORT.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    if not ok:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
