# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

START = "BYS360_EXECUTIVE_SUMMARY_SOLID_MENU_START_V2_14_14"
BAD = [
    "BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_MENU_START_V2_14_9",
    "bys360-exec-safe-group",
    "bys360-executive-summary-menu",
]


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    base = root / "app" / "templates" / "base.html"
    if not base.exists():
        print({"ok": False, "message": "base.html bulunamadı"})
        return 1

    text = read_text(base)

    missing = [t for t in [
        START,
        "Yönetici Özeti",
        "Yönetici Paneli",
        "Otomatik E-Postalar",
        "Mail Logları",
        "Zamanlanmış İşler",
        "Test Gönderimi",
        "AI Karar Destek",
    ] if t not in text]
    if missing:
        print({"ok": False, "missing": missing})
        return 2

    bad = [b for b in BAD if b in text]
    if bad:
        print({"ok": False, "bad_tokens": bad})
        return 3

    print({"ok": True, "message": "V2.14.14 solid menü bloğu temiz ve hazır."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
