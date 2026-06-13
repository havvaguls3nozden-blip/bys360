# -*- coding: utf-8 -*-
"""BYS360 Technical Debt Cleanup SAFE V9

Purpose:
- No code modification.
- Build a targeted manual cleanup map for the remaining technical debt.
- Extract line-level context for the top exception and technical UI hotspots.
- Run compile and existing Quality 9 gate if requested.
"""
from __future__ import annotations

import argparse
import ast
import csv
import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V9"
VERSION = "V9"

TOP_EXCEPTION_FILES = [
    "app/services/corporate_information_center.py",
    "app/services/settings/effective_menu.py",
    "app/menu_registry.py",
    "app/main_handlers/account_settings_helpers.py",
    "app/institutional/hr_personnel_operations_routes.py",
    "app/services/ai_agent/service.py",
    "app/ai/routes.py",
    "app/services/menu_visibility.py",
    "app/institutional/hr_common.py",
    "app/main_handlers/account_communication_helpers.py",
]

TOP_UI_FILES = [
    "app/templates/survey_create.html",
    "app/templates/survey_edit.html",
    "app/templates/announcement_new.html",
    "app/static/js/bys360_assistant_module.js",
    "app/templates/hr_attendance.html",
    "app/templates/hr_leave.html",
    "app/templates/notifications_list.html",
    "app/static/css/performance_completion_phase12_final_gate.css",
    "app/templates/task_management.html",
    "app/templates/assistant_training_bank.html",
]

TECHNICAL_TERMS = [
    "api", "json", "debug", "workflow", "phase", "sync", "gate", "endpoint",
    "exception", "traceback", "stack", "payload", "raw", "unauthorized_scope",
    "unauthorized", "forbidden", "null", "undefined", "console", "dev", "todo", "fixme",
    "http 500", "500", "403", "404", "csrf", "token", "session", "route",
]

EXCLUDE_DIR_PARTS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "backups", "releases",
    "archive", ".quarantine", "reports", "logs",
}


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def norm_rel(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def iter_files(root: Path, suffixes: Tuple[str, ...]) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.relative_to(root).parts)
        if parts & EXCLUDE_DIR_PARTS:
            continue
        if p.suffix.lower() in suffixes:
            yield p


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def line_context(lines: List[str], lineno: int, before: int = 3, after: int = 8) -> str:
    start = max(1, lineno - before)
    end = min(len(lines), lineno + after)
    out = []
    for n in range(start, end + 1):
        marker = ">>" if n == lineno else "  "
        out.append(f"{marker} {n:5d}: {lines[n-1].rstrip()}")
    return "\n".join(out)


def classify_except_block(node: ast.ExceptHandler, lines: List[str]) -> Dict[str, Any]:
    body_text = "\n".join(lines[max(0, node.lineno - 1): max(0, getattr(node, 'end_lineno', node.lineno))])
    lower = body_text.lower()
    has_logging = any(x in lower for x in ("logger.", "logging.", "current_app.logger"))
    body_kinds = [type(stmt).__name__ for stmt in node.body]
    is_silent = not has_logging
    simple_returns = (ast.Pass, ast.Continue, ast.Break, ast.Return)
    is_simple = all(isinstance(stmt, simple_returns) for stmt in node.body)
    return {
        "lineno": node.lineno,
        "end_lineno": getattr(node, "end_lineno", node.lineno),
        "body_kinds": body_kinds,
        "has_logging": has_logging,
        "is_silent": is_silent,
        "is_simple": is_simple,
        "context": line_context(lines, node.lineno),
    }


def scan_exception_file(root: Path, rel: str) -> Dict[str, Any]:
    path = root / norm_rel(rel)
    result = {"file": rel.replace("/", "\\"), "exists": path.exists(), "broad_except_count": 0, "silent_count": 0, "items": []}
    if not path.exists():
        return result
    text = read_text(path)
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        result["syntax_error"] = str(exc)
        return result
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            is_broad = False
            if node.type is None:
                is_broad = True
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                is_broad = True
            elif isinstance(node.type, ast.Tuple):
                is_broad = any(isinstance(e, ast.Name) and e.id == "Exception" for e in node.type.elts)
            if is_broad:
                result["broad_except_count"] += 1
                item = classify_except_block(node, lines)
                if item["is_silent"]:
                    result["silent_count"] += 1
                if len(result["items"]) < 15:
                    result["items"].append(item)
    return result


def scan_ui_file(root: Path, rel: str) -> Dict[str, Any]:
    path = root / norm_rel(rel)
    result = {"file": rel.replace("/", "\\"), "exists": path.exists(), "term_count": 0, "items": []}
    if not path.exists():
        return result
    text = read_text(path)
    lines = text.splitlines()
    patterns = [(term, re.compile(r"\b" + re.escape(term) + r"\b", re.I)) for term in TECHNICAL_TERMS]
    for idx, line in enumerate(lines, 1):
        found_terms = sorted({term for term, pat in patterns if pat.search(line)})
        if found_terms:
            result["term_count"] += len(found_terms)
            if len(result["items"]) < 25:
                result["items"].append({
                    "lineno": idx,
                    "terms": found_terms,
                    "context": line_context(lines, idx, before=2, after=2),
                })
    return result


def count_global_metrics(root: Path) -> Dict[str, int]:
    python_files = list(iter_files(root, (".py",)))
    python_lines = 0
    broad = 0
    silent = 0
    for p in python_files:
        text = read_text(p)
        python_lines += len(text.splitlines())
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                is_broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception")
                if isinstance(node.type, ast.Tuple):
                    is_broad = any(isinstance(e, ast.Name) and e.id == "Exception" for e in node.type.elts)
                if is_broad:
                    broad += 1
                    if classify_except_block(node, lines)["is_silent"]:
                        silent += 1
    app_python_files = [p for p in python_files if p.relative_to(root).parts and p.relative_to(root).parts[0] == "app"]
    env_count = len([p for p in root.glob(".env") if p.is_file()])
    local_db_count = len(list((root / "instance").glob("*.sqlite*"))) if (root / "instance").exists() else 0
    return {
        "python_files": len(python_files),
        "python_lines": python_lines,
        "app_python_files": len(app_python_files),
        "broad_except_count": broad,
        "silent_broad_except_count": silent,
        "env_file_count": env_count,
        "local_db_count": local_db_count,
    }


def compile_all(root: Path) -> Dict[str, Any]:
    errors = []
    checked = 0
    for p in iter_files(root, (".py",)):
        checked += 1
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(p)], capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append({"path": str(p.relative_to(root)), "error": (proc.stderr or proc.stdout)[-2000:]})
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors[:20]}


def run_quality9(root: Path) -> Dict[str, Any]:
    q = root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not q.exists():
        return {"skipped": True, "reason": "quality9 script not found"}
    proc = subprocess.run([sys.executable, str(q), "--project-root", str(root)], cwd=str(root), capture_output=True, text=True)
    return {"returncode": proc.returncode, "stdout_tail": (proc.stdout or "")[-1200:], "stderr_tail": (proc.stderr or "")[-1200:]}


def build_markdown(report: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# {PACKAGE} {VERSION} — Hedefli Manuel Temizlik Haritası")
    lines.append("")
    lines.append("Bu rapor kod değiştirmez. Kalan teknik borç için dosya ve satır düzeyinde güvenli manuel temizlik sırası üretir.")
    lines.append("")
    lines.append("## Genel Ölçümler")
    for k, v in report["audit_metrics"].items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Öncelikli Exception Dosyaları")
    for item in report["exception_details"]:
        lines.append(f"### {item['file']} — broad: {item.get('broad_except_count', 0)}, silent: {item.get('silent_count', 0)}")
        if not item.get("exists"):
            lines.append("Dosya bulunamadı.")
            continue
        for ex in item.get("items", [])[:5]:
            lines.append(f"- Satır {ex['lineno']} | silent={ex['is_silent']} | simple={ex['is_simple']} | body={','.join(ex['body_kinds'])}")
            lines.append("```text")
            lines.append(ex["context"])
            lines.append("```")
    lines.append("")
    lines.append("## Öncelikli UI Teknik Dil Dosyaları")
    for item in report["ui_details"]:
        lines.append(f"### {item['file']} — terim: {item.get('term_count', 0)}")
        if not item.get("exists"):
            lines.append("Dosya bulunamadı.")
            continue
        for ui in item.get("items", [])[:8]:
            lines.append(f"- Satır {ui['lineno']} | terimler: {', '.join(ui['terms'])}")
            lines.append("```text")
            lines.append(ui["context"])
            lines.append("```")
    lines.append("")
    lines.append("## Önerilen V10 Sırası")
    lines.append("1. `app\\services\\corporate_information_center.py` — exception mantığı manuel log ve fallback ayrımı.")
    lines.append("2. `app\\services\\settings\\effective_menu.py` — menü yetki fallbackleri ve hata logları.")
    lines.append("3. `app\\templates\\survey_create.html`, `survey_edit.html`, `announcement_new.html` — kullanıcıya görünen teknik terim temizliği.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all")
    parser.add_argument("--output-root", default="C:\\bys360")
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    stamp = now_stamp()
    report_dir = root / "reports" / "technical_debt"
    report_dir.mkdir(parents=True, exist_ok=True)

    metrics = count_global_metrics(root)
    exception_details = [scan_exception_file(root, rel) for rel in TOP_EXCEPTION_FILES]
    ui_details = [scan_ui_file(root, rel) for rel in TOP_UI_FILES]

    technical_ui_total = sum(x.get("term_count", 0) for x in ui_details)
    report: Dict[str, Any] = {
        "ok": True,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "generated_at": stamp,
        "audit_metrics": {**metrics, "targeted_ui_term_count": technical_ui_total},
        "exception_details": exception_details,
        "ui_details": ui_details,
        "security_hygiene": {
            "env_files": [str(p.relative_to(root)) for p in root.glob(".env") if p.is_file()],
            "env_examples": [str(p.relative_to(root)) for p in root.glob(".env.example") if p.is_file()],
            "local_dbs": [str(p.relative_to(root)) for p in (root / "instance").glob("*.sqlite*")] if (root / "instance").exists() else [],
        },
    }

    md_path = report_dir / f"{PACKAGE}_{stamp}_TARGETED_TRIAGE.md"
    json_path = report_dir / f"{PACKAGE}_{stamp}.json"
    csv_path = report_dir / f"{PACKAGE}_{stamp}_UI_TERMS.csv"
    write_text(md_path, build_markdown(report))
    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "line", "terms", "context"])
        for item in ui_details:
            for ui in item.get("items", []):
                writer.writerow([item["file"], ui["lineno"], ";".join(ui["terms"]), ui["context"]])

    quality_gate = {"compile_requested": bool(args.run_compile)}
    if args.run_compile:
        compile_detail = compile_all(root)
        quality_gate["compile_ok"] = compile_detail["ok"]
        quality_gate["compile_detail"] = compile_detail
        quality_gate["existing_quality_gate"] = str(root / "scripts" / "quality" / "bys360_quality9_ci_gate.py")
        quality_gate["quality9_run"] = run_quality9(root)
    report["quality_gate"] = quality_gate
    report["reports"] = {"targeted_triage": str(md_path), "json_report": str(json_path), "ui_terms_csv": str(csv_path)}

    write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2))

    output = {
        "ok": bool(not args.run_compile or quality_gate.get("compile_ok")),
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "audit_metrics": report["audit_metrics"],
        "top_exception_details": [[x["file"], x.get("broad_except_count", 0), x.get("silent_count", 0)] for x in exception_details[:10]],
        "top_ui_details": [[x["file"], x.get("term_count", 0)] for x in ui_details[:10]],
        "security_hygiene": report["security_hygiene"],
        "quality_gate": quality_gate,
        "reports": report["reports"],
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["ok"] and (not args.run_compile or quality_gate.get("quality9_run", {}).get("returncode", 0) == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
