from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V12"
VERSION = "V12"

TARGET_FILES = [
    "app/templates/survey_create.html",
    "app/templates/survey_edit.html",
    "app/templates/announcement_new.html",
    "app/templates/hr_attendance.html",
    "app/templates/hr_leave.html",
    "app/templates/notifications_list.html",
    "app/templates/assistant_training_bank.html",
]

# Only user-facing wording replacements. The patcher applies these only inside
# HTML text nodes (> ... <), not attributes, input names, Jinja blocks, or JS code.
REPLACEMENTS = {
    "payload": "içerik verisi",
    "Payload": "İçerik verisi",
    "PAYLOAD": "İÇERİK VERİSİ",
    "json": "yapılandırılmış veri",
    "JSON": "Yapılandırılmış veri",
    "null": "boş değer",
    "Null": "Boş değer",
    "stack": "hata ayrıntısı",
    "Stack": "Hata ayrıntısı",
    "raw": "işlenmemiş kayıt",
    "Raw": "İşlenmemiş kayıt",
    "cache": "geçici kayıt",
    "Cache": "Geçici kayıt",
    "api": "servis",
    "API": "Servis",
    "route": "sayfa yolu",
    "Route": "Sayfa yolu",
    "gate": "kontrol adımı",
    "Gate": "Kontrol adımı",
    "log": "işlem kaydı",
    "Log": "İşlem kaydı",
}
TERM_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(REPLACEMENTS, key=len, reverse=True)) + r")\b")
TAG_SPLIT_RE = re.compile(r"(>)([^<>]*)(<)")


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("/", "\\")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def visible_text_candidate_count(text: str) -> int:
    count = 0
    for m in TAG_SPLIT_RE.finditer(text):
        node = m.group(2)
        if "{{" in node or "{%" in node or "{#" in node:
            continue
        count += len(TERM_RE.findall(node))
    return count


def total_term_count(text: str) -> int:
    return len(TERM_RE.findall(text))


def patch_html_visible_text(text: str) -> tuple[str, int]:
    changes = 0

    def repl_segment(match: re.Match[str]) -> str:
        nonlocal changes
        before = match.group(2)
        # Do not alter Jinja expressions/blocks or empty whitespace-only nodes.
        if "{{" in before or "{%" in before or "{#" in before:
            return match.group(0)
        if not before.strip():
            return match.group(0)

        def word_repl(wm: re.Match[str]) -> str:
            nonlocal changes
            old = wm.group(0)
            new = REPLACEMENTS.get(old, old)
            if new != old:
                changes += 1
            return new

        after = TERM_RE.sub(word_repl, before)
        return match.group(1) + after + match.group(3)

    return TAG_SPLIT_RE.sub(repl_segment, text), changes


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def backup_file(path: Path, project_root: Path, backup_root: Path) -> Path:
    dst = backup_root / path.relative_to(project_root)
    ensure_dir(dst.parent)
    shutil.copy2(path, dst)
    return dst


def compile_python(project_root: Path) -> dict:
    files = [p for p in project_root.rglob("*.py") if not any(part in {".venv", "venv", "__pycache__"} for part in p.parts)]
    errors = []
    for p in files:
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(p)], cwd=str(project_root), capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append({"path": rel(p, project_root), "error": (proc.stderr or proc.stdout)[-2000:]})
    return {"ok": not errors, "checked_python_files": len(files), "error_count": len(errors), "errors": errors[:20]}


def run_quality9(project_root: Path) -> dict:
    gate = project_root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not gate.exists():
        return {"returncode": None, "skipped": True, "reason": "quality9 gate bulunamadi"}
    proc = subprocess.run([sys.executable, str(gate)], cwd=str(project_root), capture_output=True, text=True)
    return {
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-1000:],
        "stderr_tail": (proc.stderr or "")[-1000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["audit", "patch", "all"])
    parser.add_argument("--output-root", default="C:\\bys360")
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    stamp = now_stamp()
    reports_dir = project_root / "reports" / "technical_debt"
    ensure_dir(reports_dir)
    backup_root = Path(args.output_root).resolve() / "backups" / f"technical_debt_safe_v12_{stamp}"

    targets = [project_root / p for p in TARGET_FILES]
    pre_counts = {}
    pre_visible_counts = {}
    for p in targets:
        if p.exists():
            txt = read_text(p)
            pre_counts[rel(p, project_root)] = total_term_count(txt)
            pre_visible_counts[rel(p, project_root)] = visible_text_candidate_count(txt)
        else:
            pre_counts[str(p)] = None
            pre_visible_counts[str(p)] = None

    changes = []
    changed_files = []
    change_count = 0
    if args.mode in {"patch", "all"}:
        ensure_dir(backup_root)
        for p in targets:
            if not p.exists():
                continue
            before = read_text(p)
            after, c = patch_html_visible_text(before)
            if c > 0 and after != before:
                backup_file(p, project_root, backup_root)
                write_text(p, after)
                changed_files.append(rel(p, project_root))
                change_count += c
                changes.append({"path": rel(p, project_root), "visible_text_replacements": c})

    post_counts = {}
    post_visible_counts = {}
    for p in targets:
        if p.exists():
            txt = read_text(p)
            post_counts[rel(p, project_root)] = total_term_count(txt)
            post_visible_counts[rel(p, project_root)] = visible_text_candidate_count(txt)
        else:
            post_counts[str(p)] = None
            post_visible_counts[str(p)] = None

    deltas = {}
    for k, v in pre_counts.items():
        pv = post_counts.get(k)
        deltas[k] = None if v is None or pv is None else pv - v

    visible_deltas = {}
    for k, v in pre_visible_counts.items():
        pv = post_visible_counts.get(k)
        visible_deltas[k] = None if v is None or pv is None else pv - v

    changes_csv = reports_dir / f"{PACKAGE}_{stamp}_HTML_VISIBLE_CHANGES.csv"
    with changes_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "visible_text_replacements"])
        writer.writeheader()
        for row in changes:
            writer.writerow(row)

    compile_result = None
    quality9 = None
    if args.run_compile:
        compile_result = compile_python(project_root)
        quality9 = run_quality9(project_root)

    report = {
        "ok": True,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "code_changed": bool(changed_files),
        "changed_files": changed_files,
        "change_count": change_count,
        "backup_root": str(backup_root) if changed_files else None,
        "pre_targeted_term_counts": pre_counts,
        "post_targeted_term_counts": post_counts,
        "delta_targeted_term_counts": deltas,
        "pre_visible_text_term_counts": pre_visible_counts,
        "post_visible_text_term_counts": post_visible_counts,
        "delta_visible_text_term_counts": visible_deltas,
        "quality_gate": {
            "compile_requested": bool(args.run_compile),
            "compile_ok": None if compile_result is None else compile_result.get("ok"),
            "compile_detail": compile_result,
            "quality9_run": quality9,
        },
        "reports": {
            "changes_csv": str(changes_csv),
        },
        "next_step": "V13: kalan HTML/JS gercek gorunur metinler icin rapor satir baglami; exception tarafinda effective_menu.py manuel review.",
    }

    if compile_result and not compile_result.get("ok"):
        report["ok"] = False
    if quality9 and quality9.get("returncode") not in (0, None):
        report["ok"] = False

    json_report = reports_dir / f"{PACKAGE}_{stamp}.json"
    json_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["reports"]["json_report"] = str(json_report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
