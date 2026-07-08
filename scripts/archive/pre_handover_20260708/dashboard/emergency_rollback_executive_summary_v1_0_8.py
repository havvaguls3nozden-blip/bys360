# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import py_compile
import re
import shutil
from datetime import datetime
from pathlib import Path

VERSION = "BYS360_EXECUTIVE_SUMMARY_V1_0_9_EMERGENCY_ROLLBACK"

TARGET_FILES = [
    "app/dashboard/routes.py",
    "app/templates/base.html",
    "app/menu_registry.py",
    "app/menu_registry_data_sections.py",
    "app/services/settings/effective_menu.py",
]

PY_COMPILE_FILES = [
    "app/dashboard/routes.py",
    "app/menu_registry.py",
    "app/menu_registry_data_sections.py",
    "app/services/settings/effective_menu.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safety_backup(path: Path) -> str | None:
    if not path.exists():
        return None
    bdir = path.parent / ".backup_emergency_before_v109"
    bdir.mkdir(parents=True, exist_ok=True)
    dst = bdir / f"{path.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(path, dst)
    return str(dst)


def find_latest_v108_backup(path: Path) -> Path | None:
    bdir = path.parent / ".backup_executive_summary_v108"
    if not bdir.exists():
        return None
    candidates = list(bdir.glob(f"{path.name}.*.bak"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def strip_v108_blocks(text: str) -> str:
    # Python marked blocks
    patterns = [
        r"\n?# BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_PROFESSIONAL_BEGIN.*?# BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_PROFESSIONAL_END\n?",
        r"\n?# BYS360_EXECUTIVE_SUMMARY_ADMIN_ONLY_V1_0_8_BEGIN.*?# BYS360_EXECUTIVE_SUMMARY_ADMIN_ONLY_V1_0_8_END\n?",
        # Jinja base menu block
        r"\s*\{#\s*BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_MENU_BEGIN\s*#\}.*?\{#\s*BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_MENU_END\s*#\}\s*",
        # Registry data section block
        r"\s*#\s*BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_SECTION\s*\n\s*\{.*?\}\s*,?\s*\n\s*#\s*/BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_SECTION\s*",
    ]
    for pat in patterns:
        text = re.sub(pat, "\n", text, flags=re.S)
    # Clean excessive blank lines introduced by emergency stripping.
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text


def restore_or_strip(root: Path, rel: str) -> dict:
    path = root / rel
    item = {"file": rel, "exists": path.exists(), "mode": None, "backup_before": None, "restored_from": None, "changed": False, "error": None}
    if not path.exists():
        return item
    try:
        item["backup_before"] = safety_backup(path)
        latest = find_latest_v108_backup(path)
        if latest and latest.exists():
            shutil.copy2(latest, path)
            item["mode"] = "restored_from_v108_backup"
            item["restored_from"] = str(latest)
            item["changed"] = True
            return item
        original = read_text(path)
        stripped = strip_v108_blocks(original)
        if stripped != original:
            write_text(path, stripped)
            item["mode"] = "stripped_v108_marked_blocks"
            item["changed"] = True
        else:
            item["mode"] = "no_v108_block_found"
        return item
    except Exception as exc:
        item["error"] = str(exc)
        return item


def disable_v108_template(root: Path) -> dict:
    path = root / "app/templates/dashboard/executive_summary_admin_panel.html"
    item = {"file": str(path.relative_to(root)), "exists": path.exists(), "disabled": False, "backup_before": None, "error": None}
    if not path.exists():
        return item
    try:
        item["backup_before"] = safety_backup(path)
        # Do not delete; just keep as inactive backup. Existing stable routes should not reference it after rollback.
        disabled = path.with_suffix(path.suffix + ".v108_disabled")
        if disabled.exists():
            disabled.unlink()
        shutil.move(str(path), str(disabled))
        item["disabled"] = True
        item["disabled_path"] = str(disabled)
    except Exception as exc:
        item["error"] = str(exc)
    return item


def compile_targets(root: Path) -> dict:
    out = {"ok": True, "files": [], "errors": []}
    for rel in PY_COMPILE_FILES:
        path = root / rel
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            out["files"].append({"file": rel, "ok": True})
        except Exception as exc:
            out["ok"] = False
            out["files"].append({"file": rel, "ok": False, "error": repr(exc)})
            out["errors"].append(f"{rel}: {exc}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    result = {"version": VERSION, "project_root": str(root), "restores": [], "template": None, "compile": None, "ok": False}

    for rel in TARGET_FILES:
        result["restores"].append(restore_or_strip(root, rel))

    result["template"] = disable_v108_template(root)
    result["compile"] = compile_targets(root)
    result["ok"] = bool(result["compile"].get("ok")) and not any(x.get("error") for x in result["restores"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        return 1
    print(f"{VERSION}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
