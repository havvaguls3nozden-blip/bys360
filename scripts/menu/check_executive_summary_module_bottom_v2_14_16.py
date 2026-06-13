# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = [
    "BYS360_EXECUTIVE_SUMMARY_BOTTOM_MENU_START_V2_14_16",
    "BYS360_EXECUTIVE_SUMMARY_BOTTOM_STYLE_START_V2_14_16",
    "Yönetici Özeti",
    "Yönetici Paneli",
    "Otomatik E-Postalar",
    "Mail Logları",
    "Zamanlanmış İşler",
    "Test Gönderimi",
    "/dashboard/yonetici-ozeti",
]

BAD = [
    "BYS360_EXECUTIVE_SUMMARY_STATIC_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_SOLID_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_MENU_START_V2_14_9",
    "executive-summary-safe",
    "executive-summary-solid",
    "bys360-exec-solid",
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

    # This version intentionally does not require position before/after AI.
    print({"ok": True, "message": "Yönetici Özeti bottom menü bloğu hazır. AI/Performans hedef alınmadı."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
