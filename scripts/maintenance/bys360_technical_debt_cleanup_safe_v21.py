# -*- coding: utf-8 -*-
"""
BYS360 Technical Debt Cleanup SAFE V21

Audit-only final live readiness and manual-risk closure report.
Does not modify application code.

Purpose:
- Confirm V20 closed automatic/safeish exception candidates.
- Keep remaining rollback/db.rollback/control-flow handlers as manual refactor warnings.
- Confirm compile + Quality9 stay green.
- Confirm .env/local SQLite are protected by SAFE V17 .gitignore rules.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import py_compile
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V21"
VERSION = "V21"

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

TECH_TERMS = [
    "workflow state", "authorized_scope", "endpoint", "traceback", "exception",
    "debug", "raw error", "stacktrace", "phase sync", "faz 3 senkronu",
    "sync", "gate", "unauthorized", "forbidden", "payload", "json", "null",
    "route", "cache", "api", "module", "log",
]

LOGGING_PATTERNS = (
    "logger.exception", "logger.warning", "logger.error", "logging.getLogger",
    "current_app.logger", "__import__(\"logging\")", "__import__('logging')",
    "_log_warning", "_log_error", ".exception(", ".warning(", ".error(",
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path).replace("/", "\\")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_python_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        try:
            parts = set(p.relative_to(root).parts)
        except Exception:
            parts = set(p.parts)
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
        except Exception as exc:  # report-only script must continue
            errors.append({"path": relpath(py, root), "error": str(exc)})
            if len(errors) >= 25:
                break
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors}


def run_quality9(root: Path) -> Dict[str, Any]:
    gate = root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not gate.exists():
        return {"missing": True, "returncode": None, "stdout_tail": "", "stderr_tail": ""}
    python_exe = root / ".venv" / "Scripts" / "python.exe"
    cmd = [str(python_exe if python_exe.exists() else sys.executable), str(gate)]
    try:
        cp = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True, timeout=180)
        return {
            "missing": False,
            "returncode": cp.returncode,
            "stdout_tail": (cp.stdout or "")[-2000:],
            "stderr_tail": (cp.stderr or "")[-2000:],
        }
    except Exception as exc:
        return {"missing": False, "returncode": -1, "stdout_tail": "", "stderr_tail": str(exc)}


def is_broad_exception(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    t = handler.type
    if isinstance(t, ast.Name):
        return t.id in {"Exception", "BaseException"}
    if isinstance(t, ast.Attribute):
        return t.attr in {"Exception", "BaseException"}
    if isinstance(t, ast.Tuple):
        return any((isinstance(e, ast.Name) and e.id in {"Exception", "BaseException"}) or (isinstance(e, ast.Attribute) and e.attr in {"Exception", "BaseException"}) for e in t.elts)
    return False


def node_source_segment(text: str, node: ast.AST) -> str:
    lines = text.splitlines()
    lineno = max(1, int(getattr(node, "lineno", 1)))
    end_lineno = max(lineno, int(getattr(node, "end_lineno", lineno)))
    return "\n".join(lines[lineno - 1:min(len(lines), end_lineno)])


def handler_body_text(text: str, handler: ast.ExceptHandler) -> str:
    return "\n".join(node_source_segment(text, stmt) for stmt in handler.body)


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
        elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
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
    body_low = body.lower()
    kind_low = kind.lower()
    if "_rollback(" in body and "return" in kind_low:
        return "manual_risky_rollback_return"
    if "db.session.rollback" in body_low:
        if "raise" in kind_low:
            return "manual_risky_db_rollback_raise"
        return "manual_risky_db_rollback"
    if "raise" in kind_low or "return" in kind_low or "continue" in kind_low or "break" in kind_low:
        return "manual_risky_control_flow"
    if "set_setting" in body or "result[" in body or "warnings" in body_low or "errors" in body_low:
        return "manual_business_review"
    if "fallback_assignment" in kind_low:
        return "manual_noncritical_fallback"
    return "manual_review"


def is_auto_patch_candidate(category: str) -> bool:
    # V21 should confirm no remaining automatic/safeish candidates.
    return category in {"manual_safeish_last_error_setting", "manual_safeish_result_warning", "manual_noncritical_fallback"}


def scan_exception_file(root: Path, rel: Path) -> Dict[str, Any]:
    path = root / rel
    result: Dict[str, Any] = {
        "path": str(rel).replace("/", "\\"),
        "exists": path.exists(),
        "broad_except_count": 0,
        "logged_count": 0,
        "manual_count": 0,
        "manual_risky_count": 0,
        "manual_business_review_count": 0,
        "auto_patch_candidate_count": 0,
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
        preview = node_source_segment(text, node)
        ctx = {
            "path": str(rel).replace("/", "\\"),
            "lineno": getattr(node, "lineno", None),
            "end_lineno": getattr(node, "end_lineno", None),
            "body_lineno": getattr(node.body[0], "lineno", None) if node.body else None,
            "kind": kind,
            "logged": logged,
            "category": category,
            "auto_patch_candidate": is_auto_patch_candidate(category),
            "first_body": body.strip().splitlines()[0].strip() if body.strip() else "",
            "source_preview": preview[:1000],
        }
        handlers.append(ctx)
        by_category[category] += 1
        by_kind[kind] += 1
    manual = [h for h in handlers if h["category"] != "already_logged"]
    risky = [h for h in manual if "risky" in h["category"]]
    business = [h for h in manual if h["category"] == "manual_business_review"]
    auto_candidates = [h for h in manual if h.get("auto_patch_candidate")]
    result.update({
        "broad_except_count": len(handlers),
        "logged_count": len(handlers) - len(manual),
        "manual_count": len(manual),
        "manual_risky_count": len(risky),
        "manual_business_review_count": len(business),
        "auto_patch_candidate_count": len(auto_candidates),
        "by_category": dict(by_category),
        "by_kind": dict(by_kind),
        "top_manual_contexts": manual[:40],
    })
    return result


def scan_ui_file(root: Path, rel: Path) -> Dict[str, Any]:
    path = root / rel
    result = {"path": str(rel).replace("/", "\\"), "exists": path.exists(), "attention_count": 0, "term_counts": {}, "contexts": []}
    if not path.exists():
        return result
    text = read_text(path)
    term_counts = Counter()
    contexts: List[Dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        low = stripped.lower()
        terms = [t for t in TECH_TERMS if t in low]
        if not terms:
            continue
        # Keep only lines that look like Turkish user-facing text or explicit comments with old gate names.
        natural_tr = any(ch in stripped for ch in "çğıöşüÇĞİÖŞÜ") or any(w in low for w in ["başkan", "menü", "yetki", "kullanıcı", "hata", "görün", "canlı", "kontrol"])
        comment_or_text = stripped.startswith(("'", '"', "<", "//", "/*", "*"))
        if not (natural_tr and comment_or_text):
            continue
        for t in terms:
            term_counts[t] += 1
        contexts.append({"line": lineno, "terms": terms, "text": stripped[:500]})
    result.update({"attention_count": len(contexts), "term_counts": dict(term_counts), "contexts": contexts[:80]})
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
        if name in {".env", ".flaskenv"}:
            env_files.append(rel_s)
        elif name.startswith(".env") and "example" in name:
            env_examples.append(rel_s)
        elif name.endswith((".sqlite", ".sqlite3", ".db")):
            local_dbs.append(rel_s)
    gitignore = root / ".gitignore"
    gitignore_text = read_text(gitignore) if gitignore.exists() else ""
    protections = {
        "has_env_rule": bool(re.search(r"(?m)^\.env$", gitignore_text)) or ".env" in gitignore_text,
        "has_sqlite_rule": ".sqlite" in gitignore_text or "*.db" in gitignore_text or ".sqlite3" in gitignore_text,
        "has_safe_v17_block": "BEGIN BYS360 SAFE V17 sensitive/local runtime files" in gitignore_text,
    }
    return {
        "env_files": sorted(env_files),
        "env_examples": sorted(env_examples),
        "local_dbs": sorted(local_dbs),
        "gitignore_exists": gitignore.exists(),
        "gitignore_protections": protections,
    }


def smoke_static_checks(root: Path) -> Dict[str, Any]:
    checks = []
    required_paths = [
        "app",
        "scripts/quality/bys360_quality9_ci_gate.py",
        "scripts/windows",
        "reports/quality",
        "reports/technical_debt",
        ".gitignore",
    ]
    for rel in required_paths:
        p = root / rel
        checks.append({"path": rel.replace("/", "\\"), "exists": p.exists()})
    return {"required_paths": checks, "missing": [c["path"] for c in checks if not c["exists"]]}


def make_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# {PACKAGE} — Final Canlı Hazırlık ve Manuel Risk Raporu")
    lines.append("")
    lines.append(f"- Versiyon: {VERSION}")
    lines.append(f"- Kod değişikliği: {report.get('code_changed')}")
    lines.append(f"- Oluşturma zamanı: {report.get('created_at')}")
    lines.append("")
    lines.append("## Canlı Hazırlık")
    for k, v in report.get("live_readiness", {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Kalan Manuel Riskler")
    for item in report.get("exception_summaries", []):
        lines.append(f"### {item.get('path')}")
        lines.append(f"- broad_except_count: {item.get('broad_except_count')}")
        lines.append(f"- logged_count: {item.get('logged_count')}")
        lines.append(f"- manual_count: {item.get('manual_count')}")
        lines.append(f"- manual_risky_count: {item.get('manual_risky_count')}")
        lines.append(f"- manual_business_review_count: {item.get('manual_business_review_count')}")
        lines.append(f"- auto_patch_candidate_count: {item.get('auto_patch_candidate_count')}")
        lines.append("- by_category:")
        for ck, cv in item.get("by_category", {}).items():
            lines.append(f"  - {ck}: {cv}")
        for ctx in item.get("top_manual_contexts", [])[:14]:
            preview = str(ctx.get("source_preview", "")).replace("\n", " | ")
            lines.append(f"  - Satır {ctx.get('lineno')}: {ctx.get('category')} — `{preview[:220]}`")
        lines.append("")
    lines.append("## UI Dikkat Alanları")
    for ui in report.get("ui_summaries", []):
        lines.append(f"- {ui.get('path')}: attention_count={ui.get('attention_count')}, terms={ui.get('term_counts')}")
    lines.append("")
    lines.append("## Güvenlik Hijyeni")
    sec = report.get("security_hygiene", {})
    lines.append(f"- env_files: {sec.get('env_files')}")
    lines.append(f"- env_examples: {sec.get('env_examples')}")
    lines.append(f"- local_dbs: {sec.get('local_dbs')}")
    lines.append(f"- gitignore_protections: {sec.get('gitignore_protections')}")
    lines.append("")
    lines.append("## Sonraki Adım")
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
                    "kind": "ui_attention",
                    "path": ui.get("path"),
                    "line": ctx.get("line"),
                    "category": "ui_attention",
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
    smoke_checks = smoke_static_checks(root)

    total_manual = sum(int(x.get("manual_count", 0)) for x in exception_summaries)
    total_risky = sum(int(x.get("manual_risky_count", 0)) for x in exception_summaries)
    total_business = sum(int(x.get("manual_business_review_count", 0)) for x in exception_summaries)
    total_auto_candidates = sum(int(x.get("auto_patch_candidate_count", 0)) for x in exception_summaries)
    total_ui_attention = sum(int(x.get("attention_count", 0)) for x in ui_summaries)

    quality_gate: Dict[str, Any] = {"compile_requested": bool(args.run_compile), "compile_ok": None}
    if args.run_compile:
        compile_detail = compile_project(root)
        q9 = run_quality9(root)
        quality_gate.update({
            "compile_ok": compile_detail.get("ok"),
            "compile_detail": compile_detail,
            "existing_quality_gate": str(root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"),
            "quality9_run": q9,
        })
    else:
        q9 = {}

    blockers: List[str] = []
    warnings: List[str] = []
    if args.run_compile and quality_gate.get("compile_ok") is not True:
        blockers.append("compile_failed")
    if args.run_compile and isinstance(q9, dict) and q9.get("returncode") != 0:
        blockers.append("quality9_failed")
    if total_auto_candidates > 0:
        blockers.append("auto_patch_candidate_left")
    if smoke_checks.get("missing"):
        blockers.append("static_required_path_missing")
    prot = security_hygiene.get("gitignore_protections", {})
    if not (prot.get("has_env_rule") and prot.get("has_sqlite_rule") and prot.get("has_safe_v17_block")):
        blockers.append("security_gitignore_protection_missing")
    if total_risky > 0:
        warnings.append("manual_risky_exception_review_left")
    if total_business > 0:
        warnings.append("manual_business_review_left")
    if total_ui_attention > 0:
        warnings.append("ui_attention_contexts_left")
    if security_hygiene.get("env_files"):
        warnings.append("env_present_but_gitignore_protected")
    if security_hygiene.get("local_dbs"):
        warnings.append("local_db_present_but_gitignore_protected")

    readiness = {
        "compile_green": quality_gate.get("compile_ok") is True if args.run_compile else None,
        "quality9_green": (q9.get("returncode") == 0) if isinstance(q9, dict) and q9.get("returncode") is not None else None,
        "auto_patch_candidate_remaining": total_auto_candidates,
        "manual_risky_remaining": total_risky,
        "manual_business_review_remaining": total_business,
        "ui_attention_remaining": total_ui_attention,
        "security_env_present": len(security_hygiene.get("env_files", [])),
        "security_local_db_present": len(security_hygiene.get("local_dbs", [])),
        "gitignore_safe_v17_protected": bool(prot.get("has_safe_v17_block")),
        "static_smoke_missing": smoke_checks.get("missing", []),
        "blockers": blockers,
        "warnings": warnings,
    }

    report: Dict[str, Any] = {
        "ok": not blockers,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "code_changed": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "audit_metrics": {
            "target_exception_manual_count": total_manual,
            "target_exception_risky_count": total_risky,
            "target_exception_business_review_count": total_business,
            "target_exception_auto_patch_candidate_count": total_auto_candidates,
            "target_ui_attention_count": total_ui_attention,
            "env_file_count": len(security_hygiene.get("env_files", [])),
            "local_db_count": len(security_hygiene.get("local_dbs", [])),
        },
        "exception_summaries": exception_summaries,
        "ui_summaries": ui_summaries,
        "security_hygiene": security_hygiene,
        "static_smoke_checks": smoke_checks,
        "live_readiness": readiness,
        "quality_gate": quality_gate,
        "next_step": "Teknik borç otomatik patch hattı kapatılabilir. Kalan rollback/db.rollback/control-flow blokları için ayrı manuel refactor planı veya canlı final smoke test komutları uygulanmalı.",
    }

    json_path = reports_dir / f"{PACKAGE}_{stamp}.json"
    md_path = reports_dir / f"{PACKAGE}_{stamp}_FINAL_LIVE_READINESS_REPORT.md"
    csv_path = reports_dir / f"{PACKAGE}_{stamp}_MANUAL_RISK_CONTEXTS.csv"
    report["reports"] = {
        "json_report": str(json_path),
        "final_live_readiness_report": str(md_path),
        "manual_risk_contexts_csv": str(csv_path),
    }
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(make_markdown(report), encoding="utf-8")
    write_csv_contexts(csv_path, exception_summaries, ui_summaries)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
