# -*- coding: utf-8 -*-
"""
BYS360 EMERGENCY FULL SIDEBAR RESTORE V2.14.12

Acil amaç:
- V2.14.11 ile base.html içine giren güvenli menü JS/CSS bloğunu kaldırır.
- V2.14.9 öncesi alınan en güncel backup içinden base.html'i geri yükler.
- V2.14.9'un dokunduğu diğer iki template'i de backup'tan geri yükler.
- Yeni Yönetici Özeti menüsü eklemez.
- Veritabanına, route'lara, Yönetici Özeti sayfasına dokunmaz.
- Öncelik: Canlı sol şeridi eski sağlam haline döndürmek.

"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path


VERSION = "V2.14.12"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def backup_current(path: Path, project_root: Path) -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = project_root / "backups" / f"emergency_full_sidebar_restore_{VERSION}_{stamp}" / path.relative_to(project_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, out)
    return str(out)


def latest_backup(project_root: Path, pattern: str) -> Path | None:
    bdir = project_root / "backups"
    if not bdir.exists():
        return None
    matches = sorted([p for p in bdir.glob(pattern) if p.is_dir()], key=lambda p: p.name, reverse=True)
    return matches[0] if matches else None


def strip_bad_blocks(text: str) -> str:
    # V2.14.11 safe JS/CSS block
    text = re.sub(
        r"\s*<!--\s*BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_START[^>]*-->.*?<!--\s*BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_END[^>]*-->\s*",
        "\n",
        text,
        flags=re.I | re.S,
    )
    # V2.14.9 HTML block
    text = re.sub(
        r"\s*<!--\s*BYS360_EXECUTIVE_SUMMARY_MENU_START[^>]*-->.*?<!--\s*BYS360_EXECUTIVE_SUMMARY_MENU_END[^>]*-->\s*",
        "\n",
        text,
        flags=re.I | re.S,
    )
    # Any injected styles/scripts by id
    text = re.sub(
        r"\s*<style[^>]*(?:bys360-exec-summary|bys360-executive-summary)[^>]*>.*?</style>\s*",
        "\n",
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r"\s*<script[^>]*(?:bys360-exec-summary|bys360-executive-summary)[^>]*>.*?</script>\s*",
        "\n",
        text,
        flags=re.I | re.S,
    )
    return re.sub(r"\n{3,}", "\n\n", text)


def restore_file_from_backup(project_root: Path, rel: str, backup_root: Path | None) -> dict:
    dest = project_root / rel
    result = {"file": rel, "restored": False, "backup_before_restore": None, "from": None, "note": None}

    if not dest.exists():
        result["note"] = "hedef dosya yok"
        return result

    current_backup = backup_current(dest, project_root)
    result["backup_before_restore"] = current_backup

    src = backup_root / rel if backup_root else None
    if src and src.exists():
        shutil.copy2(src, dest)
        # Ensure no later bad blocks remain even if wrong backup was selected.
        cleaned = strip_bad_blocks(read_text(dest))
        write_text(dest, cleaned)
        result["restored"] = True
        result["from"] = str(src)
        result["note"] = "backup'tan geri yüklendi ve kötü bloklar temizlendi"
        return result

    # Fallback: clean current file only
    cleaned = strip_bad_blocks(read_text(dest))
    write_text(dest, cleaned)
    result["restored"] = True
    result["from"] = "current-cleaned"
    result["note"] = "backup bulunamadı; mevcut dosyadan kötü bloklar temizlendi"
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"ERROR: ProjectRoot bulunamadı: {project_root}", file=sys.stderr)
        return 2

    # Best source: V2.14.9 backup because it is before menu damage.
    backup_root = latest_backup(project_root, "executive_summary_menu_V2.14.9_*")

    targets = [
        "app/templates/base.html",
        "app/templates/ai_decision/faz1_health_layout.html",
        "app/templates/admin/performance_menu_visibility_settings.html",
    ]

    results = [restore_file_from_backup(project_root, rel, backup_root) for rel in targets]

    print({
        "ok": True,
        "version": VERSION,
        "message": "Canlı sol şerit eski sağlam haline döndürülmek üzere restore edildi. Yönetici Özeti menüsü eklenmedi.",
        "backup_root_used": str(backup_root) if backup_root else None,
        "results": results,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
