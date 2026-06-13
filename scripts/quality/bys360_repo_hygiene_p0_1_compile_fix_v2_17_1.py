# -*- coding: utf-8 -*-
"""
BYS360 Repo Hijyeni P0.1 Compile Fix V2.17.1

Amaç:
- P0 temizlikten sonra compileall'i bozan eski/onarım amaçlı scriptleri canlı koda dokunmadan karantinaya almak.
- Proje içinde kalan .backup / _backup / _bys360_backups klasörlerini karantinaya almak.
- .gitignore kalıplarını güçlendirmek.
- Audit/apply raporu üretmek.

Not:
Bu script aktif Flask uygulama kodunu refactor etmez. Sadece backup/eski repair/check dosyalarını ve backup klasörlerini taşır.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

VERSION = "V2.17.1"

BROKEN_COMPILE_FILES = [
    # compileall logunda SyntaxError veren eski onarım scripti
    "scripts/communication/repair_corporate_information_center_v3_0_phase7_1_base_css_link_fix.py",
    # compileall logunda SyntaxError veren eski kalite kontrol scripti
    "scripts/quality/check_bys360_cic_v3_0_live_final_release.py",
    # compileall logunda IndentationError veren eski template dosyası
    "scripts/repair/templates/app_init_factory_clean_v2_15_4.py",
]

BACKUP_DIR_NAMES_EXACT = {
    ".backup",
    ".quality_backup",
    "_backup",
    "_bys360_backups",
}

BACKUP_DIR_PREFIXES = (
    ".backup_",
    "_backup_",
)

EXCLUDED_SCAN_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "_local_quarantine",
}

GITIGNORE_LINES = [
    "",
    "# BYS360 local hygiene / generated cleanup",
    "_local_quarantine/",
    "reports/quality/*_apply_log.json",
    "reports/quality/*_report.json",
    "*.bak",
    "*.backup",
    "*.orig",
    "*.tmp",
    "tmp_*.py",
    "**/.backup*/",
    "**/_backup*/",
    "**/_bys360_backups/",
]


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip_dir(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDED_SCAN_DIRS for part in parts)


def is_backup_dir(path: Path) -> bool:
    name = path.name
    if name in BACKUP_DIR_NAMES_EXACT:
        return True
    return any(name.startswith(prefix) for prefix in BACKUP_DIR_PREFIXES)


def find_backup_dirs(root: Path) -> List[str]:
    found: List[str] = []
    for current, dirs, _files in os.walk(root):
        cur = Path(current)
        # os.walk pruning
        dirs[:] = [d for d in dirs if d not in EXCLUDED_SCAN_DIRS]
        if should_skip_dir(cur, root):
            continue
        for d in list(dirs):
            p = cur / d
            if is_backup_dir(p):
                found.append(relpath(p, root))
                # Do not descend into matched backup dir
                try:
                    dirs.remove(d)
                except ValueError:
                    pass
    return sorted(set(found), key=lambda x: (x.count("/"), x.lower()))


def find_existing_broken_files(root: Path) -> List[str]:
    return [p for p in BROKEN_COMPILE_FILES if (root / p).exists()]


def move_to_quarantine(root: Path, rel: str, quarantine_root: Path) -> Dict[str, str]:
    src = root / rel
    dst = quarantine_root / rel
    if not src.exists():
        return {"path": rel, "status": "missing"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        # Avoid overwriting a prior moved item in the same run.
        suffix = _dt.datetime.now().strftime("%H%M%S%f")
        dst = dst.with_name(dst.name + f".{suffix}")
    shutil.move(str(src), str(dst))
    return {"path": rel, "status": "moved", "to": relpath(dst, root)}


def strengthen_gitignore(root: Path, mode: str) -> Dict[str, object]:
    gitignore = root / ".gitignore"
    old = gitignore.read_text(encoding="utf-8", errors="ignore") if gitignore.exists() else ""
    lines = old.splitlines()
    changed = False
    for line in GITIGNORE_LINES:
        if line == "":
            continue
        if line not in lines:
            lines.append(line)
            changed = True
    if changed and mode == "apply":
        text = "\n".join(lines).rstrip() + "\n"
        gitignore.write_text(text, encoding="utf-8")
    return {"path": ".gitignore", "changed": changed, "applied": changed and mode == "apply"}


def run_compile_check(root: Path) -> Dict[str, object]:
    cmd = [sys.executable, "-m", "compileall", "app", "config.py", "scripts"]
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )
    output = proc.stdout or ""
    # Keep report readable; full console output can be long.
    error_lines = [line for line in output.splitlines() if "SyntaxError" in line or "IndentationError" in line or line.startswith("***")]
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "error_lines": error_lines[:80],
        "output_tail": "\n".join(output.splitlines()[-80:]),
    }


def write_reports(root: Path, payload: Dict[str, object]) -> Tuple[str, str]:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "bys360_repo_hygiene_p0_1_compile_fix_v2_17_1_report.json"
    md_path = report_dir / "bys360_repo_hygiene_p0_1_compile_fix_v2_17_1_report.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    audit = payload.get("audit", {}) if isinstance(payload.get("audit"), dict) else {}
    apply = payload.get("apply", {}) if isinstance(payload.get("apply"), dict) else {}
    lines = [
        "# BYS360 Repo Hijyeni P0.1 Compile Fix V2.17.1 Raporu",
        "",
        f"- Mod: `{payload.get('mode')}`",
        f"- Proje kökü: `{payload.get('project_root')}`",
        f"- Bozuk compile dosyası sayısı: `{len(audit.get('broken_compile_files', []))}`",
        f"- Backup klasörü sayısı: `{len(audit.get('backup_dirs', []))}`",
        "",
        "## Bozuk Compile Dosyaları",
    ]
    broken = audit.get("broken_compile_files", [])
    if broken:
        lines.extend([f"- `{x}`" for x in broken])
    else:
        lines.append("- Bulunmadı.")

    lines.extend(["", "## Kalan Backup Klasörleri"])
    backup_dirs = audit.get("backup_dirs", [])
    if backup_dirs:
        for x in backup_dirs[:250]:
            lines.append(f"- `{x}`")
        if len(backup_dirs) > 250:
            lines.append(f"- ... ve {len(backup_dirs)-250} kayıt daha")
    else:
        lines.append("- Bulunmadı.")

    if apply:
        lines.extend(["", "## Uygulama Özeti"])
        moved = apply.get("moved", [])
        errors = apply.get("errors", [])
        lines.append(f"- Taşınan kayıt: `{len([m for m in moved if m.get('status') == 'moved'])}`")
        lines.append(f"- Hata: `{len(errors)}`")
        if errors:
            lines.extend([f"- `{e}`" for e in errors[:80]])

    compile_result = payload.get("compile_check")
    if isinstance(compile_result, dict):
        lines.extend(["", "## Compile Kontrolü"])
        lines.append(f"- Komut: `{compile_result.get('command')}`")
        lines.append(f"- Sonuç: `{'OK' if compile_result.get('ok') else 'FAIL'}`")
        lines.append(f"- Return code: `{compile_result.get('returncode')}`")
        if compile_result.get("error_lines"):
            lines.append("")
            lines.append("### Hata Satırları")
            for line in compile_result.get("error_lines", [])[:80]:
                lines.append(f"- `{line}`")

    lines.extend([
        "",
        "## Notlar",
        "- Bu paket aktif uygulama modüllerini refactor etmez.",
        "- Karantinaya alınan dosyalar `_local_quarantine` altında saklanır.",
        "- `.env` geçmişe girdiyse secret rotasyonu yine zorunludur.",
    ])
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return relpath(json_path, root), relpath(md_path, root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "apply"], default="audit")
    parser.add_argument("--run-compile-check", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(json.dumps({"ok": False, "error": f"Project root not found: {root}"}, ensure_ascii=False, indent=2))
        return 2

    broken = find_existing_broken_files(root)
    backup_dirs = find_backup_dirs(root)
    gitignore = strengthen_gitignore(root, args.mode)

    payload: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "audit": {
            "broken_compile_files": broken,
            "backup_dirs": backup_dirs,
        },
        "gitignore": gitignore,
    }

    if args.mode == "apply":
        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        quarantine_root = root / "_local_quarantine" / f"bys360_repo_hygiene_p0_1_compile_fix_{stamp}"
        moved: List[Dict[str, str]] = []
        errors: List[str] = []

        # Move broken files first, then backup dirs. Backup dirs are sorted shallow-first.
        targets = list(broken) + list(backup_dirs)
        seen = set()
        for rel in targets:
            if rel in seen:
                continue
            seen.add(rel)
            try:
                moved.append(move_to_quarantine(root, rel, quarantine_root))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{rel}: {exc}")

        payload["apply"] = {
            "quarantine_root": relpath(quarantine_root, root),
            "moved": moved,
            "errors": errors,
        }

    if args.run_compile_check:
        try:
            payload["compile_check"] = run_compile_check(root)
        except Exception as exc:  # noqa: BLE001
            payload["compile_check"] = {"ok": False, "error": str(exc)}

    json_report, md_report = write_reports(root, payload)
    payload["json_report"] = json_report
    payload["md_report"] = md_report

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.mode == "apply":
        print("BYS360_REPO_HYGIENE_P0_1_COMPILE_FIX_V2_17_1_APPLY_OK")
    else:
        print("BYS360_REPO_HYGIENE_P0_1_COMPILE_FIX_V2_17_1_REPORT_OK")
    print("BYS360_REPO_HYGIENE_P0_1_COMPILE_FIX_V2_17_1_OK")
    print("Rapor dosyalari:")
    print(f"- {md_report.replace('/', os.sep)}")
    print(f"- {json_report.replace('/', os.sep)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
