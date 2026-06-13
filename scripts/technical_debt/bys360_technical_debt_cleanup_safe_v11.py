# -*- coding: utf-8 -*-
"""
BYS360 Technical Debt Cleanup SAFE V11
Targeted UI language cleanup for visible text only.
- Backs up every changed file.
- Does not touch Python business logic.
- For HTML: edits visible text nodes and safe UI attributes only; skips tags, Jinja, script/style blocks.
- For JS: edits only natural-language string literals; skips identifier-like strings and route/path/key-like values.
- Runs Python compile and existing Quality 9 gate when requested.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V11"
VERSION = "V11"

TARGET_HTML = [
    Path("app/templates/survey_create.html"),
    Path("app/templates/survey_edit.html"),
    Path("app/templates/announcement_new.html"),
    Path("app/templates/hr_attendance.html"),
    Path("app/templates/hr_leave.html"),
    Path("app/templates/notifications_list.html"),
    Path("app/templates/assistant_training_bank.html"),
]
TARGET_JS = [Path("app/static/js/bys360_assistant_module.js")]

# Conservative replacements for visible UI wording. These are intentionally not used for identifiers.
TERM_REPLACEMENTS = {
    "payload": "form verisi",
    "Payload": "Form verisi",
    "PAYLOAD": "FORM VERİSİ",
    "json": "sistem verisi",
    "JSON": "sistem verisi",
    "Json": "Sistem verisi",
    "null": "boş",
    "NULL": "BOŞ",
    "stack": "hata ayrıntısı",
    "Stack": "Hata ayrıntısı",
    "raw": "işlenmemiş veri",
    "Raw": "İşlenmemiş veri",
    "api": "sistem bağlantısı",
    "API": "sistem bağlantısı",
    "route": "sayfa yolu",
    "Route": "Sayfa yolu",
    "cache": "geçici kayıt",
    "Cache": "Geçici kayıt",
    "gate": "son kontrol",
    "Gate": "Son kontrol",
    "module": "bölüm",
    "Module": "Bölüm",
    "log": "kayıt",
    "Log": "Kayıt",
}
TECH_TERMS = sorted(set(TERM_REPLACEMENTS.keys()), key=len, reverse=True)

SAFE_ATTRS = {"title", "placeholder", "aria-label", "data-empty", "data-error", "data-title"}

@dataclass
class Change:
    path: str
    line: int
    before: str
    after: str
    kind: str


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def line_no(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def has_tech_term(s: str) -> bool:
    low = s.lower()
    return any(t.lower() in low for t in TECH_TERMS)


def replace_terms(s: str) -> str:
    out = s
    # Replace whole technical words where possible. Turkish chars are not matched as \w by default robustly; use explicit boundaries.
    for old, new in TERM_REPLACEMENTS.items():
        # Avoid replacing inside longer ascii identifiers.
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(old)}(?![A-Za-z0-9_])")
        out = pattern.sub(new, out)
    return out


def natural_language_like(s: str) -> bool:
    stripped = s.strip()
    if len(stripped) < 8:
        return False
    # Do not alter route names, CSS selectors, URLs, endpoint values, object keys, ids.
    if re.fullmatch(r"[A-Za-z0-9_./:#?&=%{}$\-]+", stripped):
        return False
    if any(x in stripped for x in ("http://", "https://", "/api/", "{{", "}}", "{%", "%}", "function(", "=>")):
        return False
    # Require either whitespace or Turkish chars or punctuation used in messages.
    return bool(re.search(r"\s|[çğıöşüÇĞİÖŞÜ]|[,.!?;:]", stripped))


def mask_jinja_and_blocks(text: str) -> List[Tuple[str, bool]]:
    """Return segments (segment, editable). Skips Jinja, tags, script/style blocks."""
    token_re = re.compile(r"(<script\b.*?</script\s*>|<style\b.*?</style\s*>|{#.*?#}|{{.*?}}|{%.*?%}|<[^>]+>)", re.I | re.S)
    parts: List[Tuple[str, bool]] = []
    pos = 0
    for m in token_re.finditer(text):
        if m.start() > pos:
            parts.append((text[pos:m.start()], True))
        parts.append((m.group(0), False))
        pos = m.end()
    if pos < len(text):
        parts.append((text[pos:], True))
    return parts


def patch_html_visible_text(path: Path, rel: Path) -> Tuple[str, List[Change]]:
    text = read_text(path)
    changes: List[Change] = []
    out_parts: List[str] = []
    cursor = 0
    for seg, editable in mask_jinja_and_blocks(text):
        if editable and has_tech_term(seg):
            new_seg = replace_terms(seg)
            if new_seg != seg:
                # record per changed line, compacted
                base_idx = cursor
                for i, (b, a) in enumerate(zip(seg.splitlines(), new_seg.splitlines()), start=0):
                    if b != a:
                        changes.append(Change(str(rel), line_no(text, base_idx + sum(len(x)+1 for x in seg.splitlines()[:i])), b.strip()[:240], a.strip()[:240], "html_visible_text"))
                seg = new_seg
        out_parts.append(seg)
        cursor += len(seg)
    return "".join(out_parts), changes


def patch_html_safe_attrs(text: str, rel: Path) -> Tuple[str, List[Change]]:
    changes: List[Change] = []
    attr_re = re.compile(r"\b(" + "|".join(re.escape(a) for a in SAFE_ATTRS) + r")\s*=\s*(['\"])(.*?)\2", re.I | re.S)

    def repl(m: re.Match) -> str:
        val = m.group(3)
        if not has_tech_term(val) or not natural_language_like(val):
            return m.group(0)
        new_val = replace_terms(val)
        if new_val != val:
            changes.append(Change(str(rel), line_no(text, m.start(3)), val.strip()[:240], new_val.strip()[:240], "html_safe_attr"))
            return f"{m.group(1)}={m.group(2)}{new_val}{m.group(2)}"
        return m.group(0)

    return attr_re.sub(repl, text), changes


def patch_js_string_literals(path: Path, rel: Path) -> Tuple[str, List[Change]]:
    text = read_text(path)
    changes: List[Change] = []
    # JS strings, simple but conservative; preserves quote type. Skips template literals with ${}.
    str_re = re.compile(r"(?P<quote>['\"`])(?P<body>(?:\\.|(?!\1).)*?)(?P=quote)", re.S)

    def repl(m: re.Match) -> str:
        quote = m.group("quote")
        body = m.group("body")
        if quote == "`" and "${" in body:
            return m.group(0)
        if not has_tech_term(body):
            return m.group(0)
        if not natural_language_like(body):
            return m.group(0)
        new_body = replace_terms(body)
        if new_body != body:
            changes.append(Change(str(rel), line_no(text, m.start("body")), body.strip()[:240], new_body.strip()[:240], "js_visible_string"))
            return f"{quote}{new_body}{quote}"
        return m.group(0)

    return str_re.sub(repl, text), changes


def count_terms_in_targets(root: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for rel in TARGET_HTML + TARGET_JS:
        path = root / rel
        if not path.exists():
            continue
        text = read_text(path)
        counts[str(rel)] = sum(len(re.findall(rf"(?<![A-Za-z0-9_]){re.escape(term)}(?![A-Za-z0-9_])", text)) for term in TECH_TERMS)
    return counts


def backup_file(root: Path, backup_root: Path, rel: Path) -> None:
    src = root / rel
    dst = backup_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def compile_python_files(root: Path) -> Dict[str, object]:
    errors = []
    checked = 0
    for path in root.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__", ".git"} for part in path.parts):
            continue
        checked += 1
        try:
            subprocess.run([sys.executable, "-m", "py_compile", str(path)], cwd=str(root), check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            errors.append({"path": str(path.relative_to(root)), "error": (e.stderr or e.stdout or str(e))[-1200:]})
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors[:20]}


def run_quality9(root: Path) -> Dict[str, object]:
    script = root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not script.exists():
        return {"skipped": True, "reason": "quality9 script not found"}
    proc = subprocess.run([sys.executable, str(script)], cwd=str(root), capture_output=True, text=True)
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-1000:], "stderr_tail": proc.stderr[-1000:]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", default="all")
    ap.add_argument("--output-root", default="C:\\bys360")
    ap.add_argument("--run-compile", action="store_true")
    ns = ap.parse_args()

    root = Path(ns.project_root).resolve()
    stamp = now_stamp()
    report_dir = root / "reports" / "technical_debt"
    report_dir.mkdir(parents=True, exist_ok=True)
    backup_root = Path(ns.output_root) / "backups" / f"technical_debt_safe_v11_{stamp}"
    backup_root.mkdir(parents=True, exist_ok=True)

    pre_counts = count_terms_in_targets(root)
    all_changes: List[Change] = []
    changed_files: List[str] = []

    if ns.mode.lower() in {"all", "patch", "ui"}:
        for rel in TARGET_HTML:
            path = root / rel
            if not path.exists():
                continue
            original = read_text(path)
            new_text, ch1 = patch_html_visible_text(path, rel)
            new_text, ch2 = patch_html_safe_attrs(new_text, rel)
            changes = ch1 + ch2
            if new_text != original:
                backup_file(root, backup_root, rel)
                write_text(path, new_text)
                changed_files.append(str(rel))
                all_changes.extend(changes)

        for rel in TARGET_JS:
            path = root / rel
            if not path.exists():
                continue
            original = read_text(path)
            new_text, changes = patch_js_string_literals(path, rel)
            if new_text != original:
                backup_file(root, backup_root, rel)
                write_text(path, new_text)
                changed_files.append(str(rel))
                all_changes.extend(changes)

    post_counts = count_terms_in_targets(root)

    changes_csv = report_dir / f"{PACKAGE}_{stamp}_UI_CHANGES.csv"
    with changes_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "line", "kind", "before", "after"])
        w.writeheader()
        for c in all_changes:
            w.writerow(asdict(c))

    summary_md = report_dir / f"{PACKAGE}_{stamp}_REPORT.md"
    with summary_md.open("w", encoding="utf-8") as f:
        f.write(f"# {PACKAGE} {VERSION}\n\n")
        f.write("## Amaç\nKullanıcıya görünen teknik ifadeleri güvenli ve hedefli şekilde kurumsal Türkçe dile çevirmek.\n\n")
        f.write("## Değişen Dosyalar\n")
        if changed_files:
            for p in changed_files:
                f.write(f"- `{p}`\n")
        else:
            f.write("- Değişen dosya yok.\n")
        f.write("\n## Terim Sayısı Karşılaştırması\n")
        for p in sorted(set(pre_counts) | set(post_counts)):
            f.write(f"- `{p}`: {pre_counts.get(p, 0)} → {post_counts.get(p, 0)}\n")
        f.write(f"\nDetay CSV: `{changes_csv}`\n")

    quality = {}
    if ns.run_compile:
        compile_result = compile_python_files(root)
        q9 = run_quality9(root)
        quality = {"compile_requested": True, "compile_ok": bool(compile_result.get("ok")), "compile_detail": compile_result, "quality9_run": q9}
    else:
        quality = {"compile_requested": False}

    result = {
        "ok": bool(quality.get("compile_ok", True)) and quality.get("quality9_run", {}).get("returncode", 0) == 0,
        "package": PACKAGE,
        "version": VERSION,
        "mode": ns.mode,
        "code_changed": bool(changed_files),
        "changed_files": changed_files,
        "change_count": len(all_changes),
        "backup_root": str(backup_root),
        "pre_targeted_term_counts": pre_counts,
        "post_targeted_term_counts": post_counts,
        "delta_targeted_term_counts": {p: post_counts.get(p, 0) - pre_counts.get(p, 0) for p in sorted(set(pre_counts) | set(post_counts))},
        "quality_gate": quality,
        "reports": {"summary_report": str(summary_md), "changes_csv": str(changes_csv)},
        "next_step": "V12: kalan gerçek görünür teknik metinler varsa dosya bazlı manuel metin düzeltme; exception tarafı için ayrı modül bazlı review paketi.",
    }
    json_report = report_dir / f"{PACKAGE}_{stamp}.json"
    json_report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["reports"]["json_report"] = str(json_report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
