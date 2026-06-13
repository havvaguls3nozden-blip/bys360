# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

START = "<!-- BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_START_V2_14_11 -->"
OLD = "BYS360_EXECUTIVE_SUMMARY_MENU_START_V2_14_9"


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
        print("FAIL: base.html bulunamadı.")
        return 1

    text = read_text(base)
    missing = []
    for token in [
        START,
        "Yönetici Özeti",
        "Yönetici Paneli",
        "Otomatik E-Postalar",
        "Mail Logları",
        "Zamanlanmış İşler",
        "Test Gönderimi",
        "/dashboard/yonetici-ozeti",
    ]:
        if token not in text:
            missing.append(token)

    if missing:
        print({"ok": False, "missing": missing})
        return 2

    offenders = []
    troot = root / "app" / "templates"
    if troot.exists():
        for p in troot.rglob("*.html"):
            t = read_text(p)
            if OLD in t:
                offenders.append(str(p))

    if offenders:
        print({"ok": False, "old_v2149_blocks_found": offenders})
        return 3

    print({"ok": True, "message": "Güvenli Yönetici Özeti menü bloğu base.html içinde aktif görünüyor."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
