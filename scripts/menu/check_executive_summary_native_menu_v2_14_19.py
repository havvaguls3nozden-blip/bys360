# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED = [
    "BYS360_EXECUTIVE_SUMMARY_NATIVE_MENU_START_V2_14_19",
    'class="accordion-nav bys360-executive-summary-native"',
    'class="bys-accordion"',
    'class="accordion-panel"',
    'class="nav-link-bys"',
    "Yönetici Özeti",
    "Yönetici Paneli",
    "Otomatik E-Postalar",
    "Mail Logları",
    "Zamanlanmış İşler",
    "Test Gönderimi",
    "/dashboard/yonetici-ozeti",
    "sidebar-footer",
]

BAD = [
    "BYS360_EXECUTIVE_SUMMARY_BEFORE_FOOTER",
    "BYS360_EXECUTIVE_SUMMARY_BOTTOM",
    "BYS360_EXECUTIVE_SUMMARY_STATIC",
    "BYS360_EXECUTIVE_SUMMARY_SOLID",
    "BYS360_EXECUTIVE_SUMMARY_SAFE",
    "BYS360_EXECUTIVE_SUMMARY_MENU_START_V2_14_9",
    "bys360-executive-summary-before-footer",
    "bys360-executive-summary-bottom",
    "bys360-executive-summary-static",
    "bys360-exec-solid",
    "bys360-exec-safe",
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

    menu_pos = text.find("BYS360_EXECUTIVE_SUMMARY_NATIVE_MENU_START_V2_14_19")
    footer_pos = text.find("sidebar-footer")
    html_end = text.rfind("</html>")

    if html_end >= 0 and menu_pos > html_end:
        print({"ok": False, "message": "Yönetici Özeti </html> sonrasına düşmüş."})
        return 4

    if footer_pos >= 0 and not (menu_pos < footer_pos):
        print({"ok": False, "message": "Yönetici Özeti sidebar-footer üstünde değil."})
        return 5

    print({"ok": True, "message": "Yönetici Özeti native accordion menüsü footer üstünde ve base.html içinde doğru görünüyor."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
