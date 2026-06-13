from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PACKAGE = "BYS360_OPS_HARDENING_V3_PRINT_CLEANUP"

CANDIDATE_DIRS = ["app"]
CANDIDATE_FILES = [
    "config.py",
    "wsgi.py",
    "run.py",
    "asgi.py",
    "manage.py",
]
EXCLUDE_PARTS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build", "reports", "backups", "archive",
}
MANUAL_KEYWORDS = {"file", "flush"}
LOGGER_NAME = "ops_logger"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def iter_py_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for d in CANDIDATE_DIRS:
        base = root / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            rel_parts = set(p.relative_to(root).parts)
            if rel_parts & EXCLUDE_PARTS:
                continue
            files.append(p)
    for f in CANDIDATE_FILES:
        p = root / f
        if p.exists() and p.suffix == ".py":
            files.append(p)
    return sorted(set(files))


def find_prints(path: Path, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    safe: List[Dict[str, Any]] = []
    manual: List[Dict[str, Any]] = []
    syntax_errors: List[Dict[str, Any]] = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        syntax_errors.append({
            "file": str(path),
            "line": exc.lineno,
            "error": str(exc),
        })
        return safe, manual, syntax_errors

    for node in ast.walk(tree):
        if not isinstance(node, ast.Expr):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if not isinstance(call.func, ast.Name) or call.func.id != "print":
            continue

        line = getattr(node, "lineno", None)
        end_line = getattr(node, "end_lineno", line)
        segment = ast.get_source_segment(text, call) or ""
        info = {
            "line": line,
            "end_line": end_line,
            "segment": segment.strip(),
        }

        keyword_names = {kw.arg for kw in call.keywords if kw.arg}
        if line is None or end_line is None or line != end_line:
            info["reason"] = "multi_line_or_unknown_line"
            manual.append(info)
            continue
        if keyword_names & MANUAL_KEYWORDS:
            info["reason"] = "file_or_flush_keyword_requires_manual_review"
            manual.append(info)
            continue
        if any(kw.arg is None for kw in call.keywords):
            info["reason"] = "star_keyword_requires_manual_review"
            manual.append(info)
            continue
        safe.append(info)
    return safe, manual, syntax_errors


def call_to_logger_expr(call_text: str) -> str | None:
    try:
        expr = ast.parse(call_text, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(expr, ast.Call) or not isinstance(expr.func, ast.Name) or expr.func.id != "print":
        return None
    args = [ast.get_source_segment(call_text, arg) for arg in expr.args]
    if any(a is None for a in args):
        return None
    arg_texts = [a.strip() for a in args if a is not None]
    sep = " "
    for kw in expr.keywords:
        if kw.arg == "sep":
            sep_seg = ast.get_source_segment(call_text, kw.value)
            if sep_seg:
                sep = None  # expression separator, handled below
                sep_expr = sep_seg.strip()
            else:
                return None
        elif kw.arg == "end":
            # end only controls console newline; logger zaten satır bazlıdır.
            continue
        else:
            return None
    if not arg_texts:
        return f'{LOGGER_NAME}.info("")'
    if len(arg_texts) == 1:
        return f"{LOGGER_NAME}.info(str({arg_texts[0]}))"
    joined_tuple = ", ".join(arg_texts)
    if len(arg_texts) == 1:
        joined_tuple += ","
    if sep is None:
        return f"{LOGGER_NAME}.info(str({sep_expr}).join(str(x) for x in ({joined_tuple})))"
    return f'{LOGGER_NAME}.info(" ".join(str(x) for x in ({joined_tuple})))'


def has_logging_import(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "import logging" in text
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name == "logging" for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom):
            # from logging import ... da yeterli değil; logging adı yoktur.
            continue
    return False


def has_logger(text: str) -> bool:
    return f"{LOGGER_NAME} = logging.getLogger(__name__)" in text


def insertion_index_for_logger(text: str) -> int:
    lines = text.splitlines(keepends=True)
    idx = 0
    # shebang / encoding comments
    while idx < len(lines) and (lines[idx].startswith("#!") or "coding" in lines[idx][:60]):
        idx += 1
    # module docstring
    try:
        tree = ast.parse(text)
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant) and isinstance(tree.body[0].value.value, str):
            idx = max(idx, getattr(tree.body[0], "end_lineno", 0))
    except SyntaxError:
        pass
    # future imports
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped.startswith("from __future__ import") or stripped == "":
            idx += 1
            continue
        break
    # initial import block
    j = idx
    while j < len(lines):
        stripped = lines[j].strip()
        if stripped.startswith("import ") or stripped.startswith("from ") or stripped == "":
            j += 1
            continue
        break
    return max(idx, j)


def ensure_logger(text: str) -> str:
    additions: List[str] = []
    if not has_logging_import(text):
        additions.append("import logging\n")
    if not has_logger(text):
        additions.append(f"{LOGGER_NAME} = logging.getLogger(__name__)\n")
    if not additions:
        return text
    lines = text.splitlines(keepends=True)
    idx = insertion_index_for_logger(text)
    if idx > 0 and idx <= len(lines) and lines[idx-1].strip() != "":
        additions.insert(0, "\n")
    if idx < len(lines) and lines[idx].strip() != "":
        additions.append("\n")
    lines[idx:idx] = additions
    return "".join(lines)


def apply_print_cleanup(path: Path, root: Path, safe_items: List[Dict[str, Any]], backup_root: Path) -> Dict[str, Any]:
    text = read_text(path)
    lines = text.splitlines(keepends=True)
    changed = 0
    skipped: List[Dict[str, Any]] = []

    for item in sorted(safe_items, key=lambda x: int(x["line"]), reverse=True):
        line_no = int(item["line"])
        original_line = lines[line_no - 1]
        indent = original_line[: len(original_line) - len(original_line.lstrip())]
        newline = "\n" if original_line.endswith("\n") else ""
        stripped = original_line.strip()
        replacement_expr = call_to_logger_expr(stripped)
        if replacement_expr is None:
            item = dict(item)
            item["reason"] = "could_not_build_logger_expression"
            skipped.append(item)
            continue
        lines[line_no - 1] = f"{indent}{replacement_expr}{newline}"
        changed += 1

    if changed:
        new_text = ensure_logger("".join(lines))
        backup_path = backup_root / path.relative_to(root)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        write_text(path, new_text)

    return {"changed_prints": changed, "skipped": skipped}


def compile_check(root: Path) -> Dict[str, Any]:
    targets = [str(root / "app")]
    for f in CANDIDATE_FILES:
        p = root / f
        if p.exists():
            targets.append(str(p))
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", *targets],
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
    except Exception as exc:  # rapor scripti için kontrollü yakalama
        return {"ok": False, "error": repr(exc)}


def build_report(root: Path, mode: str, apply_changes: bool) -> Dict[str, Any]:
    files = iter_py_files(root)
    all_safe: Dict[str, List[Dict[str, Any]]] = {}
    all_manual: Dict[str, List[Dict[str, Any]]] = {}
    syntax_errors: List[Dict[str, Any]] = []
    total_safe = 0
    total_manual = 0

    for path in files:
        text = read_text(path)
        safe, manual, syntax = find_prints(path, text)
        rel = str(path.relative_to(root))
        if safe:
            all_safe[rel] = safe
            total_safe += len(safe)
        if manual:
            all_manual[rel] = manual
            total_manual += len(manual)
        syntax_errors.extend(syntax)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "backups" / "ops_hardening_v3_print_cleanup" / timestamp
    changed_files: List[Dict[str, Any]] = []
    skipped_apply: Dict[str, List[Dict[str, Any]]] = {}

    if apply_changes:
        for rel, items in all_safe.items():
            result = apply_print_cleanup(root / rel, root, items, backup_root)
            if result["changed_prints"]:
                changed_files.append({"file": rel, "changed_prints": result["changed_prints"]})
            if result["skipped"]:
                skipped_apply[rel] = result["skipped"]

    post_safe = post_manual = 0
    post_by_file: Dict[str, Any] = {}
    if apply_changes:
        for path in files:
            text = read_text(path)
            safe, manual, _ = find_prints(path, text)
            rel = str(path.relative_to(root))
            if safe or manual:
                post_by_file[rel] = {"safe_remaining": len(safe), "manual_remaining": len(manual)}
            post_safe += len(safe)
            post_manual += len(manual)

    compile_result = compile_check(root) if apply_changes or mode in {"all", "compile"} else {"ok": None, "skipped": True}

    return {
        "package": PACKAGE,
        "mode": mode,
        "project_root": str(root),
        "scanned_python_files": len(files),
        "syntax_error_count": len(syntax_errors),
        "syntax_errors": syntax_errors,
        "pre_cleanup": {
            "safe_print_calls": total_safe,
            "manual_print_calls": total_manual,
            "total_print_calls": total_safe + total_manual,
            "safe_by_file": all_safe,
            "manual_by_file": all_manual,
        },
        "apply": {
            "applied": apply_changes,
            "backup_root": str(backup_root) if changed_files else None,
            "changed_files": changed_files,
            "changed_print_calls": sum(x["changed_prints"] for x in changed_files),
            "skipped_apply": skipped_apply,
        },
        "post_cleanup": {
            "safe_print_calls": post_safe if apply_changes else None,
            "manual_print_calls": post_manual if apply_changes else None,
            "total_print_calls": (post_safe + post_manual) if apply_changes else None,
            "remaining_by_file": post_by_file if apply_changes else None,
        },
        "compileall": compile_result,
    }


def write_reports(root: Path, report: Dict[str, Any]) -> Tuple[Path, Path]:
    out_dir = root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "BYS360_OPS_HARDENING_V3_PRINT_CLEANUP_REPORT.json"
    md_path = out_dir / "BYS360_OPS_HARDENING_V3_PRINT_CLEANUP_REPORT.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines: List[str] = []
    lines.append(f"# {PACKAGE} Raporu\n")
    lines.append("\n## Özet\n")
    lines.append(f"- Proje kökü: `{report['project_root']}`\n")
    lines.append(f"- Taranan Python dosyası: `{report['scanned_python_files']}`\n")
    lines.append(f"- Syntax hatası: `{report['syntax_error_count']}`\n")
    pre = report["pre_cleanup"]
    lines.append(f"- Temizlik öncesi güvenli dönüştürülebilir print: `{pre['safe_print_calls']}`\n")
    lines.append(f"- Manuel incelenecek print: `{pre['manual_print_calls']}`\n")
    lines.append(f"- Toplam print: `{pre['total_print_calls']}`\n")
    app = report["apply"]
    lines.append(f"- Uygulandı mı: `{app['applied']}`\n")
    lines.append(f"- Değiştirilen print: `{app['changed_print_calls']}`\n")
    if app["backup_root"]:
        lines.append(f"- Yedek klasörü: `{app['backup_root']}`\n")
    comp = report["compileall"]
    lines.append(f"- Compileall: `{comp.get('ok')}`\n")

    if app["changed_files"]:
        lines.append("\n## Değişen Dosyalar\n")
        lines.append("| Dosya | Dönüştürülen print |\n|---|---:|\n")
        for item in app["changed_files"]:
            lines.append(f"| `{item['file']}` | {item['changed_prints']} |\n")

    post = report["post_cleanup"]
    if post["total_print_calls"] is not None:
        lines.append("\n## Temizlik Sonrası\n")
        lines.append(f"- Kalan güvenli dönüştürülebilir print: `{post['safe_print_calls']}`\n")
        lines.append(f"- Kalan manuel print: `{post['manual_print_calls']}`\n")
        lines.append(f"- Kalan toplam print: `{post['total_print_calls']}`\n")

    if post.get("remaining_by_file"):
        lines.append("\n## Kalan Print Dağılımı\n")
        lines.append("| Dosya | Güvenli kalan | Manuel kalan |\n|---|---:|---:|\n")
        for rel, item in sorted(post["remaining_by_file"].items()):
            lines.append(f"| `{rel}` | {item['safe_remaining']} | {item['manual_remaining']} |\n")

    if pre["manual_by_file"]:
        lines.append("\n## Manuel İncelenecek Printler\n")
        for rel, items in sorted(pre["manual_by_file"].items()):
            lines.append(f"\n### `{rel}`\n")
            for item in items[:50]:
                lines.append(f"- Satır {item.get('line')}: `{item.get('segment')}` — {item.get('reason', 'manual')}\n")

    if not comp.get("ok") and comp.get("stderr"):
        lines.append("\n## Compileall Hata Çıktısı\n")
        lines.append("```text\n")
        lines.append(comp.get("stderr", ""))
        lines.append("\n```\n")

    md_path.write_text("".join(lines), encoding="utf-8")
    return md_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 print() -> logging temizliği V3")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="audit", choices=["audit", "apply", "all", "compile"])
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"Project root bulunamadi: {root}", file=sys.stderr)
        return 2

    apply_changes = args.mode in {"apply", "all"}
    report = build_report(root, args.mode, apply_changes)
    md_path, json_path = write_reports(root, report)

    print(f"BYS360_OPS_PRINT_CLEANUP_V3_REPORT={md_path}")
    print(f"BYS360_OPS_PRINT_CLEANUP_V3_JSON={json_path}")
    summary = {
        "scanned_python_files": report["scanned_python_files"],
        "syntax_errors": report["syntax_error_count"],
        "pre_total_print_calls": report["pre_cleanup"]["total_print_calls"],
        "changed_print_calls": report["apply"]["changed_print_calls"],
        "post_total_print_calls": report["post_cleanup"]["total_print_calls"],
        "compileall_ok": report["compileall"].get("ok"),
    }
    print(json.dumps(summary, ensure_ascii=False))

    if report["syntax_error_count"]:
        return 3
    if report["compileall"].get("ok") is False:
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
