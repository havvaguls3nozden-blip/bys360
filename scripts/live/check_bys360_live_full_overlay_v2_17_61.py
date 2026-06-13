from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
import sys
from datetime import datetime
from typing import Any

VERSION = "V2.17.61"
VERSION_SLUG = "v2_17_61"
CHECK_NAME = "BYS360_LIVE_FULL_OVERLAY_V2_17_61_CHECK"

EXPECTED_ARTIFACTS = [
    "scripts/windows/repair_bys360_live_full_overlay_v2_17_61.ps1",
    "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
]

EXPECTED_HINTS = [
    "BYS360_LIVE_FULL_OVERLAY_V2_17_61",
    "LIVE_FULL_OVERLAY_V2_17_61",
    "repair_bys360_live_full_overlay_v2_17_61",
    "v2_17_61",
    "2.17.61",
]

SOURCE_SUFFIXES = {
    ".py", ".ps1", ".html", ".jinja", ".jinja2", ".css", ".js", ".ts",
    ".dart", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".ini",
}

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "build", "dist", "backups", "backup", "archive", "_cleanup_quarantine",
    ".gradle", ".dart_tool", ".idea", ".vscode",
}

SELF_NAME_PARTS = {
    "check_bys360_live_full_overlay_v2_17_61",
    "bys360_live_full_overlay_v2_17_61_check",
}


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in EXCLUDED_DIRS for part in parts)


def iter_source_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if is_excluded(p, root):
            continue
        if p.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        name_low = p.name.lower()
        if any(part in name_low for part in SELF_NAME_PARTS):
            continue
        yield p


def read_text_safely(path: Path) -> tuple[str | None, str | None]:
    try:
        data = path.read_bytes()
    except Exception as exc:
        return None, f"read_error:{exc}"
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return data.decode(enc), None
        except UnicodeDecodeError:
            continue
    return None, "decode_error"


def scan_version_markers(root: Path) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    total = 0
    patterns = [re.compile(re.escape(hint), re.IGNORECASE) for hint in EXPECTED_HINTS]
    for p in iter_source_files(root):
        text, err = read_text_safely(p)
        if err or text is None:
            continue
        matched = []
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            for patt in patterns:
                if patt.search(line):
                    matched.append({"line": i, "text": line.strip()[:240]})
                    break
            if len(matched) >= 8:
                break
        if matched:
            total += len(matched)
            hits.append({
                "file": rel(p, root),
                "match_count_limited": len(matched),
                "matches": matched,
            })
    return {
        "marker_file_count": len(hits),
        "marker_line_count_limited": total,
        "files": hits[:80],
        "truncated": len(hits) > 80,
    }


def find_nested_artifacts(root: Path) -> list[str]:
    found: list[str] = []
    needles = [Path(x).name.lower() for x in EXPECTED_ARTIFACTS]
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if is_excluded(p, root):
            continue
        if p.name.lower() in needles:
            found.append(rel(p, root))
    return sorted(found)


def check_expected(root: Path) -> dict[str, Any]:
    rows = []
    for item in EXPECTED_ARTIFACTS:
        p = root / item
        rows.append({
            "path": item,
            "exists": p.exists(),
            "size": p.stat().st_size if p.exists() else None,
        })
    return {
        "all_expected_exist": all(r["exists"] for r in rows),
        "missing": [r["path"] for r in rows if not r["exists"]],
        "items": rows,
    }


def check_reports(root: Path) -> dict[str, Any]:
    report_dir = root / "reports"
    found: list[str] = []
    if report_dir.exists():
        for p in report_dir.rglob("*"):
            if not p.is_file():
                continue
            low = p.name.lower()
            if any(x in low for x in ("v2.17.61", "v2_17_61", "2_17_61")):
                found.append(rel(p, root))
    return {"report_count": len(found), "reports": sorted(found)[:80], "truncated": len(found) > 80}


def python_quality_snapshot(root: Path, compile_all: bool) -> dict[str, Any]:
    py_files = [p for p in iter_source_files(root) if p.suffix.lower() == ".py"]
    bom_files = []
    ast_errors = []
    py_compile_errors = []
    for p in py_files:
        try:
            data = p.read_bytes()
        except Exception as exc:
            ast_errors.append({"file": rel(p, root), "error": f"read_error:{exc}"})
            continue
        if data.startswith(b"\xef\xbb\xbf"):
            bom_files.append(rel(p, root))
        try:
            text = data.decode("utf-8")
            ast.parse(text, filename=str(p))
        except Exception as exc:
            ast_errors.append({"file": rel(p, root), "error": str(exc)[:300]})
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as exc:
            py_compile_errors.append({"file": rel(p, root), "error": str(exc)[:300]})

    compileall_result: dict[str, Any] = {"ran": False}
    if compile_all:
        proc = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", str(root / "app"), str(root / "config.py"), str(root / "scripts")],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        compileall_result = {
            "ran": True,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-1200:],
            "stderr_tail": proc.stderr[-1200:],
        }

    return {
        "python_file_count": len(py_files),
        "bom_count": len(bom_files),
        "bom_files": bom_files[:80],
        "ast_error_count": len(ast_errors),
        "ast_errors": ast_errors[:80],
        "py_compile_error_count": len(py_compile_errors),
        "py_compile_errors": py_compile_errors[:80],
        "compileall": compileall_result,
    }


def determine_status(expected: dict[str, Any], nested: list[str], markers: dict[str, Any], reports: dict[str, Any]) -> dict[str, Any]:
    has_expected = expected["all_expected_exist"]
    has_markers = markers["marker_file_count"] > 0 or reports["report_count"] > 0
    nested_only = bool(nested) and not has_expected

    if has_expected and has_markers:
        state = "likely_available"
        ok = True
        summary = "V2.17.61 onarim artifactlari projede mevcut ve marker/rapor izi bulundu."
    elif has_expected:
        state = "artifact_exists_but_no_marker_evidence"
        ok = False
        summary = "V2.17.61 onarim scriptleri mevcut; fakat uygulama izi/rapor marker'i bulunamadi."
    elif nested_only:
        state = "nested_artifact_detected_not_applied_to_project_root"
        ok = False
        summary = "V2.17.61 dosyalari proje kokune islenmemis; muhtemelen zip klasorlu acilmis veya dosyalar yan klasorde kalmis."
    elif has_markers:
        state = "marker_evidence_without_expected_scripts"
        ok = False
        summary = "V2.17.61 izleri var; ancak beklenen onarim scriptleri proje kokunde yok. Uygulama durumu kesin degil."
    else:
        state = "cannot_confirm_v2_17_61"
        ok = False
        summary = "V2.17.61 onarim scriptleri ve uygulanma izi bulunamadi. Bu proje paketi son overlay'i tasimiyor olabilir."

    return {"ok": ok, "state": state, "summary": summary}


def write_markdown(report: dict[str, Any], md_path: Path) -> None:
    lines = []
    lines.append(f"# BYS360 Live Full Overlay {VERSION} Kontrol Raporu")
    lines.append("")
    lines.append(f"Üretim zamanı: `{report['generated_at']}`")
    lines.append(f"Proje kökü: `{report['project_root']}`")
    lines.append("")
    status = report["status"]
    lines.append("## Sonuç")
    lines.append("")
    lines.append(f"- Durum: `{status['state']}`")
    lines.append(f"- OK: `{status['ok']}`")
    lines.append(f"- Özet: {status['summary']}")
    lines.append("")
    lines.append("## Beklenen V2.17.61 dosyaları")
    lines.append("")
    lines.append("| Dosya | Var mı | Boyut |")
    lines.append("|---|---:|---:|")
    for item in report["expected_artifacts"]["items"]:
        lines.append(f"| `{item['path']}` | `{item['exists']}` | `{item['size']}` |")
    lines.append("")
    if report["expected_artifacts"]["missing"]:
        lines.append("Eksik dosyalar:")
        for m in report["expected_artifacts"]["missing"]:
            lines.append(f"- `{m}`")
        lines.append("")
    if report["nested_artifacts"]:
        lines.append("## Yan klasörde / iç içe tespit edilen V2.17.61 dosyaları")
        lines.append("")
        for p in report["nested_artifacts"][:40]:
            lines.append(f"- `{p}`")
        lines.append("")
    lines.append("## V2.17.61 marker taraması")
    lines.append("")
    markers = report["version_markers"]
    lines.append(f"- Marker bulunan dosya sayısı: `{markers['marker_file_count']}`")
    lines.append(f"- Marker satır sayısı sınırlı: `{markers['marker_line_count_limited']}`")
    for hit in markers["files"][:20]:
        lines.append(f"- `{hit['file']}`")
    lines.append("")
    lines.append("## Rapor izleri")
    lines.append("")
    lines.append(f"- Rapor sayısı: `{report['reports']['report_count']}`")
    for p in report["reports"]["reports"][:30]:
        lines.append(f"- `{p}`")
    lines.append("")
    q = report.get("quality_snapshot")
    if q:
        lines.append("## Python kalite özeti")
        lines.append("")
        lines.append(f"- Python dosyası: `{q['python_file_count']}`")
        lines.append(f"- BOM dosyası: `{q['bom_count']}`")
        lines.append(f"- AST hatası: `{q['ast_error_count']}`")
        lines.append(f"- py_compile hatası: `{q['py_compile_error_count']}`")
        lines.append(f"- compileall çalıştı mı: `{q['compileall']['ran']}`")
        if q['compileall'].get('ran'):
            lines.append(f"- compileall OK: `{q['compileall'].get('ok')}`")
        lines.append("")
    lines.append("## Yorum")
    lines.append("")
    lines.append("Bu kontrol paketi kod değiştirmez. Sadece `reports/` altına JSON ve Markdown rapor üretir.")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="audit")
    parser.add_argument("--compile-all", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"ProjectRoot bulunamadi: {root}")

    expected = check_expected(root)
    nested = find_nested_artifacts(root)
    # Eger normal beklenen dosyalar bulunduysa nested listesinden ayni dosyalari cikart.
    nested = [p for p in nested if p not in EXPECTED_ARTIFACTS]
    markers = scan_version_markers(root)
    reports = check_reports(root)
    status = determine_status(expected, nested, markers, reports)
    quality = python_quality_snapshot(root, args.compile_all)

    generated_at = datetime.now().isoformat(timespec="seconds")
    report: dict[str, Any] = {
        "check": CHECK_NAME,
        "version": VERSION,
        "mode": args.mode,
        "generated_at": generated_at,
        "project_root": str(root),
        "expected_artifacts": expected,
        "nested_artifacts": nested,
        "version_markers": markers,
        "reports": reports,
        "quality_snapshot": quality,
        "status": status,
    }

    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"bys360_live_full_overlay_v2_17_61_check_{stamp}.json"
    md_path = reports_dir / f"bys360_live_full_overlay_v2_17_61_check_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["json_report"] = rel(json_path, root)
    report["md_report"] = rel(md_path, root)
    write_markdown(report, md_path)

    print(json.dumps({
        "check": CHECK_NAME,
        "version": VERSION,
        "project_root": str(root),
        "json_report": rel(json_path, root),
        "md_report": rel(md_path, root),
        "expected_all_exist": expected["all_expected_exist"],
        "missing": expected["missing"],
        "nested_artifact_count": len(nested),
        "marker_file_count": markers["marker_file_count"],
        "report_count": reports["report_count"],
        "quality": {
            "bom_count": quality["bom_count"],
            "ast_error_count": quality["ast_error_count"],
            "py_compile_error_count": quality["py_compile_error_count"],
            "compileall_ok": quality["compileall"].get("ok") if quality["compileall"].get("ran") else None,
        },
        "status": status,
    }, ensure_ascii=False, indent=2))

    if status["ok"]:
        print("BYS360_LIVE_FULL_OVERLAY_V2_17_61_CHECK_OK")
    else:
        print("BYS360_LIVE_FULL_OVERLAY_V2_17_61_CHECK_REVIEW_REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
