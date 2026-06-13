# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

BAD = [
    "BYS360_EXECUTIVE_SUMMARY",
    "bys360-executive-summary-before-footer",
    "bys360-executive-summary-bottom",
    "bys360-executive-summary-static",
    "bys360-exec-solid",
    "bys360-exec-safe",
    "executive-summary-before-footer",
    "executive-summary-bottom",
    "executive-summary-static",
    "executive-summary-solid",
    "executive-summary-safe",
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
    bad = [x for x in BAD if x in text]
    if bad:
        print({"ok": False, "bad_tokens": bad})
        return 2

    # Very basic sanity checks.
    required_any = ["Performans", "AI Karar", "Sistem Ayar", "Personel"]
    present = [x for x in required_any if x in text]
    if len(present) < 2:
        print({"ok": False, "message": "base.html içinde temel menü ifadeleri az görünüyor", "present": present})
        return 3

    print({"ok": True, "message": "Yönetici Özeti deneme blokları temiz. base.html temel menü ifadelerini içeriyor.", "present": present})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
