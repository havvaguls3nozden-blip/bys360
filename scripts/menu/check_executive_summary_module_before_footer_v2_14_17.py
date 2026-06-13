# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = [
    "BYS360_EXECUTIVE_SUMMARY_BEFORE_FOOTER_MENU_START_V2_14_17",
    "BYS360_EXECUTIVE_SUMMARY_BEFORE_FOOTER_STYLE_START_V2_14_17",
    "Yönetici Özeti",
    "Yönetici Paneli",
    "Otomatik E-Postalar",
    "Mail Logları",
    "Zamanlanmış İşler",
    "Test Gönderimi",
    "/dashboard/yonetici-ozeti",
]

BAD = [
    "BYS360_EXECUTIVE_SUMMARY_BOTTOM_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_STATIC_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_SOLID_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_MENU_START_V2_14_9",
    "executive-summary-safe",
    "executive-summary-solid",
    "executive-summary-bottom",
]


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    base = root / "app" / "templates" / "base.html"

    if not base.exists():
        print({"ok": False, "message": "base.html bulunamadı"})
        return 1

    text = read_text(base)

    missing = [x for x in REQUIRED if x not in text]
    if missing:
        print({"ok": False, "missing": missing})
        return 2

    bad = [x for x in BAD if x in text]
    if bad:
        print({"ok": False, "bad_tokens": bad})
        return 3

    menu_pos = text.find("BYS360_EXECUTIVE_SUMMARY_BEFORE_FOOTER_MENU_START_V2_14_17")
    footer_candidates = [text.find("© 2026"), text.find("&copy; 2026"), text.find("Her hakkı saklıdır")]
    footer_candidates = [p for p in footer_candidates if p >= 0]
    before_footer = True
    if footer_candidates:
        before_footer = menu_pos < min(footer_candidates)

    if not before_footer:
        print({"ok": False, "message": "Yönetici Özeti footer/künye metninden sonra görünüyor olabilir."})
        return 4

    print({"ok": True, "message": "Yönetici Özeti menüsü footer/künye alanından önce yerleştirilmiş görünüyor."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
