# -*- coding: utf-8 -*-
"""
BYS360 Technical Debt Cleanup SAFE V19

Audit-only live readiness / manual risk verification package.
Does not modify application code.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import py_compile
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V19"
VERSION = "V19"

EXCLUDED_DIR_NAMES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules",
    "reports", "logs", "backups", "archive", "releases", "dist", "build",
}

TARGET_EXCEPTION_FILES = [
    Path("app/services/settings/effective_menu.py"),
    Path("app/services/corporate_information_center.py"),
    Path("app/menu_registry.py"),
]

TARGET_UI_FILES = [
    Path("app/static/js/bys360_assistant_module.js"),
    Path("app/templates/survey_create.html"),
    Path("app/templates/survey_edit.html"),
    Path("app/templates/announcement_new.html"),
    Path("app/templates/hr_attendance.html"),
    Path("app/templates/hr_leave.html"),
    Path("app/templates/notifications_list.html"),
    Path("app/templates/assistant_training_bank.html"),
]

TECH_UI_TERMS = [
    "workflow state", "authorized_scope", "endpoint", "traceback", "exception",
    "debug", "raw error", "stacktrace", "phase sync", "faz 3 senkronu",
    "sync", "gate", "unauthorized", "forbidden", "payload", "json", "null",
]

VISIBLE_UI_HINTS = [
    "route", "cache", "api", "module", "log", "gate",
]

LOGGING_PATTERNS = (
    "logger.exception", "logger.warning", "logger.error", "logging.getLogger",
    "current_app.logger", "__import__(\"logging\")", "__import__('logging')",
    "_log_warning", "_log_error",
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path).replace("/", "\\")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_python_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        parts = set(p.relative_to(root).parts)
        if parts & EXCLUDED_DIR_NAMES:
            continue
        yield p


def compile_project(root: Path) -> Dict[str, Any]:
    checked = 0
    errors: List[Dict[str, Any]] = []
    for py in iter_python_files(root):
        checked += 1
        try:
            py_compile.compile(str(py), doraise=True)
        except Exception as exc:  # audit script must continue and report
            errors.append({"path": relpath(py, root), "error": str(exc)})
            if len(errors) >= 25:
                break
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors}


def run_quality9(root: Path) -> Dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not gate.exists():
        return {"returncode": None, "stdout_tail": "", "stderr_tail": "", "missing": True}
    python_exe = root / ".venv" / "Scripts" / "python.exe"
    cmd = [str(python_exe if python_exe.exists() else sys.executable), str(gate)]
    try:
        cp = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, timeout=180)
        return {
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-2000:],
            "stderr_tail": cp.stderr[-2000:],
            "missing": False,
        }
    except Exception as exc:  # audit script must continue and report
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": str(exc), "missing": False}


def node_source_segment(text: str, node: ast.AST) -> str:
    lines = text.splitlines()
    lineno = getattr(node, "lineno", 1)
    end_lineno = getattr(node, "end_lineno", lineno)
    start = max(1, lineno) - 1
    end = min(len(lines), end_lineno)
    return "\n".join(lines[start:end])


def handler_body_text(text: str, handler: ast.ExceptHandler) -> str:
    pieces: List[str] = []
    for stmt in handler.body:
        pieces.append(node_source_segment(text, stmt))
    return "\n".join(pieces)


def is_broad_exception(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    t = handler.type
    if isinstance(t, ast.Name):
        return t.id in {"Exception", "BaseException"}
    if isinstance(t, ast.Attribute):
        return t.attr in {"Exception", "BaseException"}
    if isinstance(t, ast.Tuple):
        for elt in t.elts:
            if isinstance(elt, ast.Name) and elt.id in {"Exception", "BaseException"}:
                return True
            if isinstance(elt, ast.Attribute) and elt.attr in {"Exception", "BaseException"}:
                return True
    return False


def contains_logging(body: str) -> bool:
    return any(p in body for p in LOGGING_PATTERNS)


def body_kind(handler: ast.ExceptHandler) -> str:
    names: List[str] = []
    for stmt in handler.body:
        if isinstance(stmt, ast.Pass):
            names.append("pass")
        elif isinstance(stmt, ast.Return):
            names.append("return")
        elif isinstance(stmt, ast.Raise):
            names.append("raise")
        elif isinstance(stmt, ast.Continue):
            names.append("continue")
        elif isinstance(stmt, ast.Break):
            names.append("break")
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            names.append("fallback_assignment")
        elif isinstance(stmt, ast.Import) or isinstance(stmt, ast.ImportFrom):
            names.append("import")
        elif isinstance(stmt, ast.Try):
            names.append("try")
        elif isinstance(stmt, ast.For):
            names.append("for")
        elif isinstance(stmt, ast.If):
            names.append("if")
        else:
            names.append("expression")
    return "+".join(names) if names else "empty"


def classify_handler(body: str, kind: str, logged: bool) -> str:
    if logged:
        return "already_logged"
    lowered = body.lower()
    if "_rollback(" in body and "return" in kind:
        return "manual_risky_rollback_return"
    if "db.session.rollback" in body:
        if "raise" in kind:
            return "manual_risky_db_rollback_raise"
        return "manual_risky_db_rollback"
    if "raise" in kind or "return" in kind or "continue" in kind or "break" in kind:
        return "manual_risky_control_flow"
    if "fallback_assignment" in kind:
        return "manual_fallback_assignment"
    if "set_setting" in body or "warning" in lowered or "errors" in lowered:
        return "manual_expression_review"
    return "manual_review"


def scan_exception_file(root: Path, rel: Path) -> Dict[str, Any]:
    path = root / rel
    result: Dict[str, Any] = {
        "path": str(rel).replace("/", "\\"),
        "exists": path.exists(),
        "broad_except_count": 0,
        "logged_count": 0,
        "manual_count": 0,
        "manual_risky_count": 0,
        "manual_safeish_count": 0,
        "by_category": {},
        "by_kind": {},
        "top_manual_contexts": [],
    }
    if not path.exists():
        return result
    text = read_text(path)
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        result["syntax_error"] = str(exc)
        return result
    handlers: List[Dict[str, Any]] = []
    by_category = Counter()
    by_kind = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or not is_broad_exception(node):
            continue
        body = handler_body_text(text, node)
        kind = body_kind(node)
        logged = contains_logging(body)
        category = classify_handler(body, kind, logged)
        ctx = {
            "path": str(rel).replace("/", "\\"),
            "lineno": getattr(node, "lineno", None),
            "end_lineno": getattr(node, "end_lineno", None),
            "body_lineno": getattr(node.body[0], "lineno", None) if node.body else None,
            "kind": kind,
            "logged": logged,
            "category": category,
            "first_body": body.strip().splitlines()[0].strip() if body.strip() else "",
            "source_preview": node_source_segment(text, node)[:1000],
        }
        handlers.append(ctx)
        by_category[category] += 1
        by_kind[kind] += 1
    manual = [h for h in handlers if h["category"] != "already_logged"]
    risky = [h for h in manual if "risky" in h["category"]]
    safeish = [h for h in manual if "risky" not in h["category"]]
    result.update({
        "broad_except_count": len(handlers),
        "logged_count": len(handlers) - len(manual),
        "manual_count": len(manual),
        "manual_risky_count": len(risky),
        "manual_safeish_count": len(safeish),
        "by_category": dict(by_category),
        "by_kind": dict(by_kind),
        "top_manual_contexts": manual[:25],
    })
    return result


def scan_ui_file(root: Path, rel: Path) -> Dict[str, Any]:
    path = root / rel
    result = {"path": str(rel).replace("/", "\\"), "exists": path.exists(), "candidate_count": 0, "term_counts": {}, "contexts": []}
    if not path.exists():
        return result
    text = read_text(path)
    term_counts = Counter()
    contexts: List[Dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        terms = [t for t in (TECH_UI_TERMS + VISIBLE_UI_HINTS) if t in lowered]
        if not terms:
            continue
        # Skip clear code-only JS/API/attribute lines where there is no natural language.
        natural_tr = any(ch in stripped for ch in "çğıöşüÇĞİÖŞÜ") or any(word in lowered for word in ["başkan", "menü", "yetki", "kontrol", "görün", "hata", "yenileyin", "kullanıcı"])
        if not natural_tr and any(x in stripped for x in ["function", "var ", "const ", "let ", "data-", "querySelector", "fetch(", "return ", "className", "setAttribute"]):
            continue
        for t in terms:
            term_counts[t] += 1
        contexts.append({"line": lineno, "terms": terms, "text": stripped[:500]})
    result.update({"candidate_count": len(contexts), "term_counts": dict(term_counts), "contexts": contexts[:80]})
    return result


def scan_security(root: Path) -> Dict[str, Any]:
    env_files: List[str] = []
    env_examples: List[str] = []
    local_dbs: List[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(root)
        except Exception:
            continue
        parts = set(rel.parts)
        if parts & EXCLUDED_DIR_NAMES:
            continue
        name = p.name.lower()
        rel_s = str(rel).replace("/", "\\")
        if name == ".env" or name == ".flaskenv":
            env_files.append(rel_s)
        elif name.startswith(".env") and "example" in name:
            env_examples.append(rel_s)
        elif name.endswith((".sqlite", ".sqlite3", ".db")):
            local_dbs.append(rel_s)
    gitignore = root / ".gitignore"
    gitignore_text = read_text(gitignore) if gitignore.exists() else ""
    protections = {
        "has_env_rule": bool(re.search(r"(?m)^\.env$", gitignore_text)) or ".env" in gitignore_text,
        "has_sqlite_rule": ".sqlite" in gitignore_text or "*.db" in gitignore_text,
        "has_safe_v17_block": "BEGIN BYS360 SAFE V17 sensitive/local runtime files" in gitignore_text,
    }
    return {
        "env_files": sorted(env_files),
        "env_examples": sorted(env_examples),
        "local_dbs": sorted(local_dbs),
        "gitignore_exists": gitignore.exists(),
        "gitignore_protections": protections,
    }


def make_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# {PACKAGE} — Manuel Risk ve Canlı Hazırlık Raporu")
    lines.append("")
    lines.append(f"- Versiyon: {VERSION}")
    lines.append(f"- Kod değişikliği: {report.get('code_changed')}")
    lines.append(f"- Oluşturma zamanı: {report.get('created_at')}")
    lines.append("")
    lines.append("## Özet")
    metrics = report.get("audit_metrics", {})
    for k, v in metrics.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Exception Dosya Özeti")
    for item in report.get("exception_summaries", []):
        lines.append(f"### {item.get('path')}")
        lines.append(f"- broad_except_count: {item.get('broad_except_count')}")
        lines.append(f"- logged_count: {item.get('logged_count')}")
        lines.append(f"- manual_count: {item.get('manual_count')}")
        lines.append(f"- manual_risky_count: {item.get('manual_risky_count')}")
        lines.append(f"- manual_safeish_count: {item.get('manual_safeish_count')}")
        lines.append("- by_category:")
        for ck, cv in item.get("by_category", {}).items():
            lines.append(f"  - {ck}: {cv}")
        if item.get("top_manual_contexts"):
            lines.append("- Kalan manuel bağlamlar:")
            for ctx in item.get("top_manual_contexts", [])[:12]:
                preview = str(ctx.get("source_preview", "")).replace("\n", " | ")
                lines.append(f"  - Satır {ctx.get('lineno')}: {ctx.get('category')} — `{preview[:220]}`")
        lines.append("")
    lines.append("## UI Görünür Teknik Dil Özeti")
    for ui in report.get("ui_summaries", []):
        lines.append(f"- {ui.get('path')}: candidate_count={ui.get('candidate_count')}, terms={ui.get('term_counts')}")
    lines.append("")
    lines.append("## Güvenlik Hijyeni")
    sec = report.get("security_hygiene", {})
    lines.append(f"- env_files: {sec.get('env_files')}")
    lines.append(f"- env_examples: {sec.get('env_examples')}")
    lines.append(f"- local_dbs: {sec.get('local_dbs')}")
    lines.append(f"- gitignore_protections: {sec.get('gitignore_protections')}")
    lines.append("")
    lines.append("## Önerilen Sonraki Adım")
    lines.append(str(report.get("next_step", "")))
    lines.append("")
    return "\n".join(lines)


def write_csv_contexts(path: Path, exception_summaries: List[Dict[str, Any]], ui_summaries: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["kind", "path", "line", "category", "terms", "text"])
        writer.writeheader()
        for item in exception_summaries:
            for ctx in item.get("top_manual_contexts", []):
                writer.writerow({
                    "kind": "exception",
                    "path": item.get("path"),
                    "line": ctx.get("lineno"),
                    "category": ctx.get("category"),
                    "terms": ctx.get("kind"),
                    "text": str(ctx.get("source_preview", "")).replace("\n", " | "),
                })
        for ui in ui_summaries:
            for ctx in ui.get("contexts", []):
                writer.writerow({
                    "kind": "ui",
                    "path": ui.get("path"),
                    "line": ctx.get("line"),
                    "category": "ui_candidate",
                    "terms": ",".join(ctx.get("terms", [])),
                    "text": ctx.get("text", ""),
                })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--output-root", default="C:\\bys360")
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    stamp = now_stamp()
    reports_dir = root / "reports" / "technical_debt"
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(json.dumps({"package": PACKAGE, "version": VERSION, "mode": args.mode, "project_root": str(root)}, ensure_ascii=False))

    exception_summaries = [scan_exception_file(root, rel) for rel in TARGET_EXCEPTION_FILES]
    ui_summaries = [scan_ui_file(root, rel) for rel in TARGET_UI_FILES]
    security_hygiene = scan_security(root)

    total_manual = sum(int(x.get("manual_count", 0)) for x in exception_summaries)
    total_risky = sum(int(x.get("manual_risky_count", 0)) for x in exception_summaries)
    total_safeish = sum(int(x.get("manual_safeish_count", 0)) for x in exception_summaries)
    total_ui_candidates = sum(int(x.get("candidate_count", 0)) for x in ui_summaries)

    quality_gate: Dict[str, Any] = {"compile_requested": bool(args.run_compile), "compile_ok": None}
    if args.run_compile:
        compile_detail = compile_project(root)
        quality_gate.update({"compile_ok": compile_detail.get("ok"), "compile_detail": compile_detail})
        quality_gate["existing_quality_gate"] = str(root / "scripts" / "quality" / "bys360_quality9_ci_gate.py")
        quality_gate["quality9_run"] = run_quality9(root)

    final_blockers: List[str] = []
    if quality_gate.get("compile_ok") is False:
        final_blockers.append("compile_failed")
    q9 = quality_gate.get("quality9_run") or {}
    if isinstance(q9, dict) and q9.get("returncode") not in (0, None):
        final_blockers.append("quality9_failed")
    if total_safeish > 0:
        final_blockers.append("safeish_manual_exception_left")
    if total_ui_candidates > 0:
        # Not blocker; assistant JS has code-like candidates. Keep as attention item.
        pass

    readiness = {
        "compile_green": quality_gate.get("compile_ok") is True if args.run_compile else None,
        "quality9_green": (q9.get("returncode") == 0) if isinstance(q9, dict) and q9.get("returncode") is not None else None,
        "exception_safeish_remaining": total_safeish,
        "exception_risky_remaining": total_risky,
        "ui_candidate_remaining": total_ui_candidates,
        "security_env_present": len(security_hygiene.get("env_files", [])),
        "security_local_db_present": len(security_hygiene.get("local_dbs", [])),
        "gitignore_safe_v17_protected": bool(security_hygiene.get("gitignore_protections", {}).get("has_safe_v17_block")),
        "blockers": final_blockers,
    }

    report: Dict[str, Any] = {
        "ok": not final_blockers,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "code_changed": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "audit_metrics": {
            "target_exception_manual_count": total_manual,
            "target_exception_risky_count": total_risky,
            "target_exception_safeish_count": total_safeish,
            "target_ui_visible_candidate_count": total_ui_candidates,
            "env_file_count": len(security_hygiene.get("env_files", [])),
            "local_db_count": len(security_hygiene.get("local_dbs", [])),
        },
        "exception_summaries": exception_summaries,
        "ui_summaries": ui_summaries,
        "security_hygiene": security_hygiene,
        "live_readiness": readiness,
        "quality_gate": quality_gate,
        "next_step": "V20: code patch yerine canlı hazırlık final kontrolü veya sadece üç rollback/return bloğu için insan onaylı manuel refactor planı.",
    }

    json_path = reports_dir / f"{PACKAGE}_{stamp}.json"
    md_path = reports_dir / f"{PACKAGE}_{stamp}_LIVE_READINESS_REPORT.md"
    csv_path = reports_dir / f"{PACKAGE}_{stamp}_MANUAL_AND_UI_CONTEXTS.csv"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(make_markdown(report), encoding="utf-8")
    write_csv_contexts(csv_path, exception_summaries, ui_summaries)

    report["reports"] = {
        "json_report": str(json_path),
        "live_readiness_report": str(md_path),
        "contexts_csv": str(csv_path),
    }
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 0  # Audit package reports blockers but should not fail shell.


if __name__ == "__main__":
    raise SystemExit(main())
