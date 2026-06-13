#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BYS360 Technical Debt Cleanup SAFE V1

Default mode is audit-only. It does not delete or rewrite application code.
It reports repository hygiene, secret-risk files, CSS sprawl, broad except usage,
large modules, versioned overlay files and release-copy exclusions.

Modes:
  audit          Generate full technical debt audit report.
  css-report     Generate CSS/template inventory report.
  clean-copy     Create sanitized source copy under --output-root.
  prepare-gitignore Append a managed safe-ignore block to .gitignore.
  ratchet-gate   Count broad exceptions and optionally fail over --max-broad-except.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V1"
REPORT_DIR = Path("reports") / "technical_debt"

EXCLUDE_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "ENV",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "node_modules",
    "dist",
    "build",
    "htmlcov",
    "backups",
    "backup",
    "releases",
    "release",
    ".quarantine",
    "quarantine",
    "archive",
}

SOFT_EXCLUDE_FOR_SCAN = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "ENV",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "htmlcov",
}

DANGEROUS_ENV_BASENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.prod",
    ".env.dev",
    ".env.development",
    ".env.docker.local",
    ".env.docker",
    ".flaskenv",
}

SECRET_HINT_KEYS = [
    "SECRET_KEY",
    "POSTGRES_PASSWORD",
    "DATABASE_URL",
    "TCKN_ENCRYPTION_KEY",
    "INSTAGRAM_ACCESS_TOKEN",
    "ACCESS_TOKEN",
    "PRIVATE_KEY",
    "API_KEY",
    "JWT_SECRET",
    "SENTRY_DSN",
    "REDIS_URL",
]

BINARY_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".docx", ".xlsx",
    ".zip", ".7z", ".rar", ".gz", ".tar", ".exe", ".dll", ".pyd", ".pyc", ".sqlite",
    ".db", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mov", ".avi", ".mp3",
}

CSS_LINK_RE = re.compile(r"<link[^>]+href=[\"']([^\"']+)[\"'][^>]*>", re.I)
STATIC_CSS_RE = re.compile(r"url_for\(\s*['\"]static['\"]\s*,\s*filename\s*=\s*['\"]([^'\"]+\.css)['\"]", re.I)
PLAIN_CSS_RE = re.compile(r"(?:href|src)\s*=\s*[\"']([^\"']+\.css(?:\?[^\"']*)?)[\"']", re.I)
BROAD_EXCEPT_RE = re.compile(r"\bexcept\s+Exception\b|\bexcept\s*:")
PRINT_RE = re.compile(r"(^|[^\w.])print\s*\(", re.M)
VERSION_FILE_RE = re.compile(r"(^|[/\\])(?:v\d+(?:_\d+){1,}|.*_v\d+(?:_\d+){1,}.*)", re.I)
TECHNICAL_UI_TERMS = [
    "workflow state", "phase sync", "Faz 3", "sync", "debug", "traceback", "endpoint",
    "unauthorized_scope", "president_pending", "blocked_president_pending",
]

@dataclass
class FileMetric:
    path: str
    lines: int = 0
    size_bytes: int = 0
    broad_except_count: int = 0
    print_count: int = 0


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def normalize_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def should_skip_dir(path: Path, root: Path, *, hard: bool = False) -> bool:
    rel_parts = path.relative_to(root).parts if path != root else ()
    names = EXCLUDE_DIR_NAMES if hard else SOFT_EXCLUDE_FOR_SCAN
    return any(part in names for part in rel_parts)


def iter_files(root: Path, *, hard_exclude: bool = False) -> Iterable[Path]:
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        if should_skip_dir(d, root, hard=hard_exclude):
            dirnames[:] = []
            continue
        dirnames[:] = [x for x in dirnames if x not in (EXCLUDE_DIR_NAMES if hard_exclude else SOFT_EXCLUDE_FOR_SCAN)]
        for f in filenames:
            yield d / f


def read_text_safely(path: Path) -> str:
    try:
        if path.suffix.lower() in BINARY_EXTS:
            return ""
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def is_secret_risk_path(path: Path, root: Path) -> bool:
    rel_parts = set(path.relative_to(root).parts)
    base = path.name.lower()
    if base in DANGEROUS_ENV_BASENAMES or base.startswith(".env"):
        return True
    if {"backups", "backup", ".quarantine", "quarantine", "releases", "release"} & rel_parts:
        if base.startswith(".env") or base.endswith(".env") or "secret" in path.as_posix().lower():
            return True
    return False


def find_secret_hints(path: Path) -> list[str]:
    text = read_text_safely(path)
    if not text:
        return []
    found: list[str] = []
    for key in SECRET_HINT_KEYS:
        # Report only key names, never values.
        if re.search(rf"\b{re.escape(key)}\b\s*=", text):
            found.append(key)
    # Generic high-risk tokens, still report only the pattern type.
    if re.search(r"ghp_[A-Za-z0-9_]{20,}", text):
        found.append("GITHUB_TOKEN_PATTERN")
    if re.search(r"(?:IGQVJ|EAAC)[A-Za-z0-9_-]{20,}", text):
        found.append("META_OR_INSTAGRAM_TOKEN_PATTERN")
    return sorted(set(found))


def collect_tree_stats(root: Path) -> dict[str, Any]:
    stats = {
        "total_files_all": 0,
        "total_size_all_bytes": 0,
        "top_level": {},
        "risky_dirs": {},
        "nested_project_paths": [],
    }
    for p in iter_files(root, hard_exclude=False):
        try:
            st = p.stat()
        except Exception:
            continue
        rel = normalize_rel(p, root)
        stats["total_files_all"] += 1
        stats["total_size_all_bytes"] += st.st_size
        top = rel.split("/")[0]
        stats["top_level"].setdefault(top, {"files": 0, "size_bytes": 0})
        stats["top_level"][top]["files"] += 1
        stats["top_level"][top]["size_bytes"] += st.st_size
        parts = set(Path(rel).parts)
        for risky in ["backups", "releases", ".quarantine", "archive"]:
            if risky in parts:
                stats["risky_dirs"].setdefault(risky, {"files": 0, "size_bytes": 0})
                stats["risky_dirs"][risky]["files"] += 1
                stats["risky_dirs"][risky]["size_bytes"] += st.st_size
        if "/project/" in f"/{rel}/" or rel.startswith("project/"):
            if len(stats["nested_project_paths"]) < 50:
                stats["nested_project_paths"].append(rel)
    return stats


def collect_python_metrics(root: Path) -> dict[str, Any]:
    files: list[FileMetric] = []
    total_lines = 0
    total_broad = 0
    total_print = 0
    syntax_errors: list[dict[str, Any]] = []
    for p in iter_files(root, hard_exclude=True):
        if p.suffix != ".py":
            continue
        text = read_text_safely(p)
        rel = normalize_rel(p, root)
        lines = text.count("\n") + 1 if text else 0
        broad = len(BROAD_EXCEPT_RE.findall(text))
        prints = len(PRINT_RE.findall(text))
        total_lines += lines
        total_broad += broad
        total_print += prints
        files.append(FileMetric(rel, lines, p.stat().st_size, broad, prints))
        try:
            ast.parse(text or "", filename=rel)
        except SyntaxError as e:
            syntax_errors.append({"path": rel, "line": e.lineno, "message": e.msg})
        except Exception as e:
            syntax_errors.append({"path": rel, "line": None, "message": type(e).__name__})
    top_broad = sorted(files, key=lambda x: (x.broad_except_count, x.lines), reverse=True)[:30]
    largest = sorted(files, key=lambda x: x.lines, reverse=True)[:30]
    return {
        "python_file_count": len(files),
        "python_total_lines": total_lines,
        "broad_except_total": total_broad,
        "print_call_total": total_print,
        "syntax_error_count": len(syntax_errors),
        "syntax_errors": syntax_errors[:50],
        "top_broad_except_files": [asdict(x) for x in top_broad if x.broad_except_count > 0],
        "largest_python_files": [asdict(x) for x in largest],
    }


def collect_css_metrics(root: Path) -> dict[str, Any]:
    css_files: list[dict[str, Any]] = []
    css_by_dir: dict[str, int] = {}
    css_names: set[str] = set()
    for p in iter_files(root, hard_exclude=True):
        if p.suffix.lower() != ".css":
            continue
        rel = normalize_rel(p, root)
        css_files.append({"path": rel, "size_bytes": p.stat().st_size})
        css_by_dir[str(Path(rel).parent).replace("\\", "/")] = css_by_dir.get(str(Path(rel).parent).replace("\\", "/"), 0) + 1
        css_names.add(Path(rel).name)

    template_refs: dict[str, list[str]] = {}
    js_files: list[str] = []
    for p in iter_files(root, hard_exclude=True):
        if p.suffix.lower() in {".html", ".jinja", ".j2"}:
            text = read_text_safely(p)
            refs: list[str] = []
            refs.extend(CSS_LINK_RE.findall(text))
            refs.extend(STATIC_CSS_RE.findall(text))
            refs.extend(PLAIN_CSS_RE.findall(text))
            refs = sorted(set(refs))
            if refs:
                template_refs[normalize_rel(p, root)] = refs
        elif p.suffix.lower() == ".js":
            js_files.append(normalize_rel(p, root))

    referenced_names: set[str] = set()
    for refs in template_refs.values():
        for r in refs:
            clean = r.split("?")[0]
            referenced_names.add(Path(clean).name)
    unreferenced_by_name = sorted(css_names - referenced_names)
    return {
        "css_file_count": len(css_files),
        "css_total_size_bytes": sum(x["size_bytes"] for x in css_files),
        "css_by_dir": dict(sorted(css_by_dir.items(), key=lambda kv: (-kv[1], kv[0]))),
        "template_css_references": template_refs,
        "template_css_reference_total": sum(len(v) for v in template_refs.values()),
        "js_file_count": len(js_files),
        "possibly_unreferenced_css_by_filename": unreferenced_by_name[:200],
        "note": "Unreferenced list is filename-based only; dynamic imports or CSS @import may still use files.",
    }


def collect_secret_metrics(root: Path) -> dict[str, Any]:
    risk_paths: list[dict[str, Any]] = []
    hint_files: list[dict[str, Any]] = []
    for p in iter_files(root, hard_exclude=False):
        rel = normalize_rel(p, root)
        if is_secret_risk_path(p, root):
            risk_paths.append({"path": rel, "size_bytes": p.stat().st_size, "sha256": file_sha256(p)})
        hints = find_secret_hints(p)
        if hints:
            hint_files.append({"path": rel, "hints": hints, "size_bytes": p.stat().st_size})
    return {
        "secret_risk_path_count": len(risk_paths),
        "secret_risk_paths": risk_paths[:200],
        "secret_hint_file_count": len(hint_files),
        "secret_hint_files": hint_files[:200],
        "redaction_note": "Only variable/pattern names and file paths are reported; secret values are intentionally never printed.",
    }


def collect_overlay_metrics(root: Path) -> dict[str, Any]:
    versioned: list[str] = []
    hotfix_readmes: list[str] = []
    ps_scripts: list[str] = []
    portal_overlay_scripts: list[str] = []
    for p in iter_files(root, hard_exclude=True):
        rel = normalize_rel(p, root)
        if VERSION_FILE_RE.search(rel):
            versioned.append(rel)
        if p.name.upper().startswith("README") and ("HOTFIX" in p.name.upper() or "OVERLAY" in p.name.upper()):
            hotfix_readmes.append(rel)
        if rel.startswith("scripts/windows/") and p.suffix.lower() == ".ps1":
            ps_scripts.append(rel)
        if rel.startswith("scripts/portal/") and p.suffix.lower() == ".py":
            portal_overlay_scripts.append(rel)
    return {
        "versioned_or_overlay_named_file_count": len(versioned),
        "versioned_or_overlay_named_files_sample": versioned[:200],
        "hotfix_readme_count": len(hotfix_readmes),
        "hotfix_readmes_sample": hotfix_readmes[:100],
        "windows_script_count": len(ps_scripts),
        "portal_script_count": len(portal_overlay_scripts),
    }


def collect_ui_language_metrics(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for p in iter_files(root, hard_exclude=True):
        if p.suffix.lower() not in {".html", ".py", ".js", ".ts", ".dart"}:
            continue
        text = read_text_safely(p)
        if not text:
            continue
        found = [term for term in TECHNICAL_UI_TERMS if term.lower() in text.lower()]
        if found:
            findings.append({"path": normalize_rel(p, root), "terms": sorted(set(found))})
    return {"technical_ui_language_file_count": len(findings), "files": findings[:200]}


def build_audit(root: Path) -> dict[str, Any]:
    return {
        "package": PACKAGE,
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root.resolve()),
        "tree": collect_tree_stats(root),
        "secrets": collect_secret_metrics(root),
        "python": collect_python_metrics(root),
        "css": collect_css_metrics(root),
        "overlay_hygiene": collect_overlay_metrics(root),
        "ui_language": collect_ui_language_metrics(root),
    }


def ensure_report_dir(root: Path) -> Path:
    out = root / REPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    return out


def size_mb(n: int | float) -> str:
    return f"{n / 1024 / 1024:.2f} MB"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_markdown(path: Path, audit: dict[str, Any], *, title_suffix: str = "Audit") -> None:
    tree = audit.get("tree", {})
    secrets = audit.get("secrets", {})
    py = audit.get("python", {})
    css = audit.get("css", {})
    overlay = audit.get("overlay_hygiene", {})
    ui = audit.get("ui_language", {})

    lines: list[str] = []
    lines.append(f"# {PACKAGE} — {title_suffix} Raporu")
    lines.append("")
    lines.append(f"Üretim zamanı: `{audit.get('generated_at')}`")
    lines.append(f"Proje kökü: `{audit.get('project_root')}`")
    lines.append("")
    lines.append("## Yönetici Özeti")
    lines.append("")
    lines.append(f"- Toplam dosya: **{tree.get('total_files_all', 0)}**")
    lines.append(f"- Toplam boyut: **{size_mb(tree.get('total_size_all_bytes', 0))}**")
    lines.append(f"- Secret riskli dosya/yol: **{secrets.get('secret_risk_path_count', 0)}**")
    lines.append(f"- Secret anahtar izi bulunan dosya: **{secrets.get('secret_hint_file_count', 0)}**")
    lines.append(f"- Python dosyası: **{py.get('python_file_count', 0)}**")
    lines.append(f"- Broad except toplamı: **{py.get('broad_except_total', 0)}**")
    lines.append(f"- Print çağrısı toplamı: **{py.get('print_call_total', 0)}**")
    lines.append(f"- CSS dosyası: **{css.get('css_file_count', 0)}**")
    lines.append(f"- Template CSS referansı: **{css.get('template_css_reference_total', 0)}**")
    lines.append(f"- Sürüm/overlay isimli dosya: **{overlay.get('versioned_or_overlay_named_file_count', 0)}**")
    lines.append(f"- Teknik kullanıcı dili içeren dosya: **{ui.get('technical_ui_language_file_count', 0)}**")
    lines.append("")
    lines.append("## P0 — Bugün Yapılacaklar")
    lines.append("")
    lines.append("1. Secret rotasyonu gerekiyorsa canlıdan bağımsız olarak yapılmalı; rapor secret değerlerini göstermediği için dosyalar elle açılmadan sadece yol/anahtar adına göre hareket edilmeli.")
    lines.append("2. `backups/`, `.quarantine/`, `.venv/`, eski release paketleri ve `.env*` dosyaları paylaşılacak pakete girmemeli.")
    lines.append("3. `clean-copy` modu ile temiz kaynak kopyası üretilmeli; canlıya doğrudan temizlik uygulanmamalı.")
    lines.append("4. Clean copy üzerinde `python -m compileall app config.py scripts` ve mevcut CI-safe testler çalıştırılmalı.")
    lines.append("")

    lines.append("## Secret ve Arşiv Hijyeni")
    lines.append("")
    lines.append("Secret değerleri bu raporda yazılmaz; yalnızca dosya yolu ve değişken/pattern adı gösterilir.")
    if secrets.get("secret_risk_paths"):
        lines.append("")
        lines.append("### Riskli yollar")
        lines.append("")
        for item in secrets["secret_risk_paths"][:50]:
            lines.append(f"- `{item['path']}` — {size_mb(item.get('size_bytes', 0))}")
    if secrets.get("secret_hint_files"):
        lines.append("")
        lines.append("### Anahtar izi bulunan dosyalar")
        lines.append("")
        for item in secrets["secret_hint_files"][:50]:
            hints = ", ".join(item.get("hints", []))
            lines.append(f"- `{item['path']}` — `{hints}`")
    lines.append("")

    lines.append("## CSS Envanteri")
    lines.append("")
    lines.append(f"CSS dosyası: **{css.get('css_file_count', 0)}**")
    lines.append(f"CSS toplam boyut: **{size_mb(css.get('css_total_size_bytes', 0))}**")
    lines.append("")
    lines.append("### En yoğun CSS klasörleri")
    lines.append("")
    for d, count in list(css.get("css_by_dir", {}).items())[:20]:
        lines.append(f"- `{d}`: {count}")
    if css.get("template_css_references"):
        lines.append("")
        lines.append("### Template CSS referansları")
        lines.append("")
        for tmpl, refs in list(css["template_css_references"].items())[:30]:
            lines.append(f"- `{tmpl}`: {len(refs)} referans")
            for ref in refs[:12]:
                lines.append(f"  - `{ref}`")
    lines.append("")

    lines.append("## Python Kod Borcu")
    lines.append("")
    lines.append(f"Broad except toplamı: **{py.get('broad_except_total', 0)}**")
    lines.append(f"Syntax hata sayısı: **{py.get('syntax_error_count', 0)}**")
    lines.append("")
    lines.append("### En büyük Python dosyaları")
    lines.append("")
    for item in py.get("largest_python_files", [])[:15]:
        lines.append(f"- `{item['path']}` — {item['lines']} satır, broad except: {item['broad_except_count']}")
    lines.append("")
    lines.append("### Broad except en yüksek dosyalar")
    lines.append("")
    for item in py.get("top_broad_except_files", [])[:20]:
        lines.append(f"- `{item['path']}` — {item['broad_except_count']} broad except, {item['lines']} satır")
    lines.append("")

    lines.append("## Overlay / Hotfix Hijyeni")
    lines.append("")
    lines.append(f"Sürüm/overlay isimli dosya sayısı: **{overlay.get('versioned_or_overlay_named_file_count', 0)}**")
    lines.append(f"Windows script sayısı: **{overlay.get('windows_script_count', 0)}**")
    lines.append(f"Portal script sayısı: **{overlay.get('portal_script_count', 0)}**")
    lines.append("")
    lines.append("## Önerilen Güvenli Sıra")
    lines.append("")
    lines.append("```powershell")
    lines.append("cd C:\\bys360\\project")
    lines.append("powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\repair_bys360_tech_debt_cleanup_safe_v1.ps1 -ProjectRoot \"C:\\bys360\\project\" -Mode audit")
    lines.append("powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\repair_bys360_tech_debt_cleanup_safe_v1.ps1 -ProjectRoot \"C:\\bys360\\project\" -Mode clean-copy -OutputRoot \"C:\\bys360\\releases\\BYS360_CLEAN_SOURCE_SAFE_V1\"")
    lines.append("powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\repair_bys360_tech_debt_cleanup_safe_v1.ps1 -ProjectRoot \"C:\\bys360\\project\" -Mode ratchet-gate")
    lines.append("```")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_audit(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(json.dumps({"ok": False, "error": f"Project root not found: {root}"}, ensure_ascii=False))
        return 2
    audit = build_audit(root)
    out = ensure_report_dir(root)
    json_path = out / "BYS360_TECH_DEBT_CLEANUP_SAFE_V1_AUDIT.json"
    md_path = out / "BYS360_TECH_DEBT_CLEANUP_SAFE_V1_AUDIT.md"
    write_json(json_path, audit)
    write_markdown(md_path, audit)
    print(json.dumps({
        "ok": True,
        "mode": "audit",
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "broad_except_total": audit["python"]["broad_except_total"],
        "css_file_count": audit["css"]["css_file_count"],
        "secret_risk_path_count": audit["secrets"]["secret_risk_path_count"],
    }, ensure_ascii=False, indent=2))
    return 0


def run_css_report(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    data = {"package": PACKAGE, "generated_at": _dt.datetime.now().isoformat(timespec="seconds"), "project_root": str(root), "css": collect_css_metrics(root)}
    out = ensure_report_dir(root)
    json_path = out / "BYS360_CSS_INVENTORY_SAFE_V1.json"
    md_path = out / "BYS360_CSS_INVENTORY_SAFE_V1.md"
    write_json(json_path, data)
    audit_like = {"generated_at": data["generated_at"], "project_root": str(root), "tree": {}, "secrets": {}, "python": {}, "css": data["css"], "overlay_hygiene": {}, "ui_language": {}}
    write_markdown(md_path, audit_like, title_suffix="CSS Envanteri")
    print(json.dumps({"ok": True, "mode": "css-report", "json_report": str(json_path), "markdown_report": str(md_path), "css_file_count": data["css"]["css_file_count"]}, ensure_ascii=False, indent=2))
    return 0


def should_copy_file(src: Path, root: Path) -> tuple[bool, str]:
    rel = src.relative_to(root)
    parts = set(rel.parts)
    base = src.name.lower()
    if parts & EXCLUDE_DIR_NAMES:
        return False, "excluded_dir"
    if base.startswith(".env") or base in DANGEROUS_ENV_BASENAMES:
        return False, "env_file"
    if src.suffix.lower() in {".pyc", ".pyo"}:
        return False, "bytecode"
    if src.name.endswith((".bak", ".tmp", ".temp", ".orig")):
        return False, "backup_suffix"
    # Keep normal docs, migrations, scripts and source files; do not content-scan-copy block here.
    return True, "included"


def run_clean_copy(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    if not args.output_root:
        print(json.dumps({"ok": False, "error": "--output-root is required for clean-copy"}, ensure_ascii=False))
        return 2
    out_root = Path(args.output_root).resolve()
    if out_root.exists() and any(out_root.iterdir()):
        if not args.force:
            print(json.dumps({"ok": False, "error": f"OutputRoot exists and is not empty: {out_root}. Use --force to overwrite."}, ensure_ascii=False))
            return 2
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped: dict[str, int] = {}
    bytes_copied = 0
    skipped_samples: dict[str, list[str]] = {}
    for src in iter_files(root, hard_exclude=False):
        ok, reason = should_copy_file(src, root)
        rel = src.relative_to(root)
        if not ok:
            skipped[reason] = skipped.get(reason, 0) + 1
            skipped_samples.setdefault(reason, [])
            if len(skipped_samples[reason]) < 30:
                skipped_samples[reason].append(rel.as_posix())
            continue
        dest = out_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dest)
            copied += 1
            bytes_copied += src.stat().st_size
        except Exception as e:
            skipped["copy_error"] = skipped.get("copy_error", 0) + 1
            skipped_samples.setdefault("copy_error", [])
            if len(skipped_samples["copy_error"]) < 30:
                skipped_samples["copy_error"].append(f"{rel.as_posix()} :: {type(e).__name__}")

    report = {
        "package": PACKAGE,
        "mode": "clean-copy",
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "source_root": str(root),
        "output_root": str(out_root),
        "copied_files": copied,
        "copied_size_bytes": bytes_copied,
        "skipped": skipped,
        "skipped_samples": skipped_samples,
        "warning": "This is a sanitized source copy. Run compile/test before release. Secret values were not copied intentionally if they were in .env-like files or excluded folders.",
    }
    report_path = out_root / "BYS360_CLEAN_SOURCE_SAFE_V1_REPORT.json"
    write_json(report_path, report)
    (out_root / "BYS360_CLEAN_SOURCE_SAFE_V1_README.md").write_text(
        "# BYS360 Clean Source SAFE V1\n\n"
        "Bu klasör `backups/`, `releases/`, `.quarantine/`, `.venv/`, cache ve `.env*` dosyaları dışarıda bırakılarak üretildi.\n\n"
        "Canlıya doğrudan kopyalamadan önce şu kontrolleri çalıştırın:\n\n"
        "```powershell\n"
        "python -m compileall app config.py scripts\n"
        "python -m pytest tests/quality -m ci_safe\n"
        "```\n\n"
        "Not: Gerçek ortam değişkenleri temiz release paketine konulmamalı; canlı sunucuda güvenli şekilde yönetilmelidir.\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "mode": "clean-copy", "output_root": str(out_root), "copied_files": copied, "skipped": skipped, "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0


def run_prepare_gitignore(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    gi = root / ".gitignore"
    block = """

# BEGIN BYS360_TECH_DEBT_CLEANUP_SAFE_V1
# Local secrets and environment files
.env
.env.*
!.env.template
!.env.safe.example
.flaskenv

# Local Python/runtime artifacts
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# BYS360 generated/local-only artifacts
backups/
backup/
releases/
release/
.quarantine/
quarantine/
archive/
logs/*.log
reports/technical_debt/*.json
reports/technical_debt/*.md

# Local zip/overlay drops
*.zip
*.7z
*.rar
# END BYS360_TECH_DEBT_CLEANUP_SAFE_V1
""".strip("\n") + "\n"
    existing = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
    if "BEGIN BYS360_TECH_DEBT_CLEANUP_SAFE_V1" in existing:
        print(json.dumps({"ok": True, "mode": "prepare-gitignore", "changed": False, "path": str(gi), "message": "Managed block already exists."}, ensure_ascii=False, indent=2))
        return 0
    backup = None
    if gi.exists():
        backup = gi.with_suffix(gi.suffix + f".bak_{now_stamp()}")
        shutil.copy2(gi, backup)
    with gi.open("a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n" + block)
    print(json.dumps({"ok": True, "mode": "prepare-gitignore", "changed": True, "path": str(gi), "backup": str(backup) if backup else None}, ensure_ascii=False, indent=2))
    return 0


def run_ratchet_gate(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    py = collect_python_metrics(root)
    out = ensure_report_dir(root)
    report = {
        "package": PACKAGE,
        "mode": "ratchet-gate",
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "broad_except_total": py["broad_except_total"],
        "max_broad_except": args.max_broad_except,
        "ok": True,
        "top_broad_except_files": py["top_broad_except_files"],
        "recommendation": "Her sprint bu limiti 100-150 azaltın; önce auth, security, performance approval ve settings route dosyalarından başlayın.",
    }
    if args.max_broad_except is not None and py["broad_except_total"] > args.max_broad_except:
        report["ok"] = False
    path = out / "BYS360_BROAD_EXCEPT_RATCHET_SAFE_V1.json"
    write_json(path, report)
    print(json.dumps({"ok": report["ok"], "mode": "ratchet-gate", "broad_except_total": py["broad_except_total"], "max_broad_except": args.max_broad_except, "report": str(path)}, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def run_compile(args: argparse.Namespace) -> int:
    root = Path(args.project_root).resolve()
    targets = ["app", "config.py", "scripts"]
    cmd = [sys.executable, "-m", "compileall", *targets]
    proc = subprocess.run(cmd, cwd=str(root), text=True)
    return int(proc.returncode)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=PACKAGE)
    p.add_argument("--project-root", required=True)
    p.add_argument("--mode", choices=["audit", "css-report", "clean-copy", "prepare-gitignore", "ratchet-gate", "compile"], default="audit")
    p.add_argument("--output-root")
    p.add_argument("--force", action="store_true")
    p.add_argument("--max-broad-except", type=int)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "audit":
        return run_audit(args)
    if args.mode == "css-report":
        return run_css_report(args)
    if args.mode == "clean-copy":
        return run_clean_copy(args)
    if args.mode == "prepare-gitignore":
        return run_prepare_gitignore(args)
    if args.mode == "ratchet-gate":
        return run_ratchet_gate(args)
    if args.mode == "compile":
        return run_compile(args)
    raise AssertionError(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
