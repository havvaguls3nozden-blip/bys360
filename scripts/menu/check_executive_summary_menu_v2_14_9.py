# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path
import sys

START_MARKER = "<!-- BYS360_EXECUTIVE_SUMMARY_MENU_START_V2_14_9 -->"
REQUIRED_TEXTS = [
    "Yönetici Özeti",
    "Yönetici Paneli",
    "Otomatik E-Postalar",
    "Mail Logları",
    "Zamanlanmış İşler",
    "Test Gönderimi",
    "/dashboard/yonetici-ozeti",
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
    templates = list((root / "app" / "templates").rglob("*.html")) if (root / "app" / "templates").exists() else []
    found = []
    for path in templates:
        text = read_text(path)
        if START_MARKER in text:
            missing = [t for t in REQUIRED_TEXTS if t not in text]
            found.append({"path": str(path), "missing": missing})

    if not found:
        print("FAIL: Yönetici Özeti bağımsız menü bloğu bulunamadı.")
        return 1

    bad = [x for x in found if x["missing"]]
    if bad:
        print({"ok": False, "problem": bad})
        return 2

    print({"ok": True, "found": found})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
