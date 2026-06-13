from __future__ import annotations

import argparse
import ast
import json
import py_compile
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

PACKAGE = "BYS360_OPS_HARDENING_V6A_CRITICAL_EXCEPTION_CLEANUP"
TARGET_PARTS = {"auth", "security", "session", "sessions", "permission", "permissions", "access", "rbac"}
TARGET_BASENAMES = {"config.py", "wsgi.py", "run.py"}
EXCLUDE_PARTS = {".venv", "venv", "__pycache__", "migrations", "alembic", "tests", "test", "scripts", "backups", "archive", "reports"}
EXCEPT_RE = re.compile(r"^(?P<indent>\s*)except\s+Exception(?:\s+as\s+(?P<var>[A-Za-z_][A-Za-z0-9_]*))?\s*:\s*(?:#.*)?$")
LOG_HINT_RE = re.compile(r"\b(logger|current_app\.logger|app\.logger|logging)\.(exception|error|warning|critical)\b")


def is_target(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = {p.lower() for p in rel.parts}
    if parts & EXCLUDE_PARTS:
        return False
    if path.name.lower() in TARGET_BASENAMES:
        return True
    if not str(rel).lower().startswith("app"):
        return False
    return bool(parts & TARGET_PARTS)


def iter_py_files(root: Path) -> List[Path]:
    result: List[Path] = []
    for path in root.rglob("*.py"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        parts = {p.lower() for p in rel.parts}
        if parts & EXCLUDE_PARTS:
            continue
        if is_target(path, root):
            result.append(path)
    return sorted(result)


def has_logger_setup(text: str) -> bool:
    return "logging.getLogger(__name__)" in text or re.search(r"^\s*logger\s*=", text, re.M) is not None


def ensure_logger(text: str) -> Tuple[str, bool]:
    changed = False
    if "import logging" not in text and "from logging import" not in text:
        # Place after __future__ imports and module docstring if possible.
        lines = text.splitlines(True)
        insert_at = 0
        # Skip shebang/encoding
        while insert_at < len(lines) and (lines[insert_at].startswith("#!") or "coding" in lines[insert_at][:80]):
            insert_at += 1
        # Skip module docstring using AST when possible
        try:
            mod = ast.parse(text)
            if mod.body and isinstance(mod.body[0], ast.Expr) and isinstance(getattr(mod.body[0], "value", None), ast.Constant) and isinstance(mod.body[0].value.value, str):
                insert_at = max(insert_at, getattr(mod.body[0], "end_lineno", 1))
        except Exception:
            pass
        # Skip future imports
        while insert_at < len(lines) and re.match(r"\s*from\s+__future__\s+import\s+", lines[insert_at]):
            insert_at += 1
        lines.insert(insert_at, "import logging\n")
        text = "".join(lines)
        changed = True
    if not has_logger_setup(text):
        lines = text.splitlines(True)
        # after imports block
        insert_at = 0
        try:
            mod = ast.parse(text)
            last_import = 0
            for node in mod.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import = max(last_import, getattr(node, "end_lineno", node.lineno))
            insert_at = last_import
        except Exception:
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    insert_at = i + 1
        line_to_add = "\nlogger = logging.getLogger(__name__)\n" if insert_at < len(lines) and lines[insert_at].strip() else "logger = logging.getLogger(__name__)\n"
        lines.insert(insert_at, line_to_add)
        text = "".join(lines)
        changed = True
    return text, changed


def line_indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def block_has_logging_or_raise(lines: List[str], start_idx: int, except_indent: int) -> bool:
    i = start_idx + 1
    block: List[str] = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped and line_indent_width(line) <= except_indent:
            break
        block.append(line)
        i += 1
    block_text = "".join(block)
    return bool(LOG_HINT_RE.search(block_text) or re.search(r"^\s*raise\b", block_text, re.M))


def cleanup_file(path: Path, root: Path, backup_root: Path, apply: bool) -> Dict:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        ast.parse(raw)
        syntax_before = True
    except SyntaxError as exc:
        return {"file": str(path.relative_to(root)), "syntax_before": False, "error": f"{exc.msg} line {exc.lineno}", "changed_blocks": 0}

    lines = raw.splitlines(True)
    insertions: List[Tuple[int, str]] = []
    candidates = 0
    for idx, line in enumerate(lines):
        m = EXCEPT_RE.match(line.rstrip("\n\r"))
        if not m:
            continue
        candidates += 1
        except_indent = line_indent_width(line)
        if block_has_logging_or_raise(lines, idx, except_indent):
            continue
        body_indent = m.group("indent") + "    "
        exc_var = m.group("var") or "exc"
        rel = str(path.relative_to(root)).replace("\\", "/")
        msg = f'{body_indent}logger.exception("BYS360 critical exception captured in {rel}", exc_info={exc_var})\n'
        insertions.append((idx + 1, msg))

    if not insertions:
        return {"file": str(path.relative_to(root)), "syntax_before": True, "candidates": candidates, "changed_blocks": 0}

    new_lines = list(lines)
    for pos, text in reversed(insertions):
        new_lines.insert(pos, text)
    new_text = "".join(new_lines)
    new_text, logger_changed = ensure_logger(new_text)

    try:
        ast.parse(new_text)
        syntax_after = True
    except SyntaxError as exc:
        return {"file": str(path.relative_to(root)), "syntax_before": True, "syntax_after": False, "error": f"{exc.msg} line {exc.lineno}", "changed_blocks": 0}

    if apply:
        backup_path = backup_root / path.relative_to(root)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        path.write_text(new_text, encoding="utf-8")

    return {
        "file": str(path.relative_to(root)),
        "syntax_before": True,
        "syntax_after": syntax_after,
        "candidates": candidates,
        "changed_blocks": len(insertions),
        "logger_setup_added": logger_changed,
        "applied": apply,
    }


def compile_all(files: List[Path]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    for path in files:
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{path}: {exc.msg}")
    return not errors, errors


def write_reports(root: Path, results: List[Dict], compile_ok: bool, compile_errors: List[str], apply: bool) -> Dict:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "BYS360_OPS_HARDENING_V6A_CRITICAL_EXCEPTION_CLEANUP_REPORT.json"
    md_path = report_dir / "BYS360_OPS_HARDENING_V6A_CRITICAL_EXCEPTION_CLEANUP_REPORT.md"
    summary = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "apply" if apply else "audit",
        "target_files": len(results),
        "files_changed": sum(1 for r in results if r.get("changed_blocks", 0) > 0),
        "changed_blocks": sum(int(r.get("changed_blocks", 0)) for r in results),
        "candidates": sum(int(r.get("candidates", 0)) for r in results),
        "compile_ok": compile_ok,
        "compile_error_count": len(compile_errors),
    }
    payload = {"summary": summary, "results": results, "compile_errors": compile_errors[:50]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# {PACKAGE}",
        "",
        "Bu paket yalnızca kritik canlı hatlarda geniş `except Exception` bloklarını görünür hale getirmek için güvenli `logger.exception(...)` satırı ekler.",
        "Davranışı körlemesine değiştirmez; mevcut `return`, `pass`, `fallback` veya yönlendirme mantığını bozmaz.",
        "",
        "## Özet",
        "",
        f"- Mod: `{summary['mode']}`",
        f"- Hedef dosya: `{summary['target_files']}`",
        f"- Değişen dosya: `{summary['files_changed']}`",
        f"- Logging eklenen blok: `{summary['changed_blocks']}`",
        f"- Toplam aday blok: `{summary['candidates']}`",
        f"- Compile OK: `{compile_ok}`",
        "",
        "## Değişen Dosyalar",
        "",
    ]
    changed = [r for r in results if r.get("changed_blocks", 0) > 0]
    if changed:
        lines.append("| Dosya | Blok | Logger kurulumu |")
        lines.append("|---|---:|---|")
        for r in changed:
            lines.append(f"| `{r['file']}` | {r.get('changed_blocks', 0)} | {r.get('logger_setup_added', False)} |")
    else:
        lines.append("Değişiklik gerektiren hedef blok bulunmadı.")
    if compile_errors:
        lines.extend(["", "## Compile Hataları", ""])
        lines.extend(f"- `{e}`" for e in compile_errors[:50])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"summary": summary, "json": str(json_path), "md": str(md_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    apply = args.mode in {"apply", "all"}
    files = iter_py_files(root)
    backup_root = root / "backups" / "ops_hardening_v6a_critical_exception_cleanup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    results = [cleanup_file(path, root, backup_root, apply) for path in files]
    compile_ok, compile_errors = compile_all(files)
    reports = write_reports(root, results, compile_ok, compile_errors, apply)
    print(f"BYS360_OPS_V6A_REPORT={reports['md']}")
    print(f"BYS360_OPS_V6A_JSON={reports['json']}")
    print(json.dumps(reports["summary"], ensure_ascii=False))
    if not compile_ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
