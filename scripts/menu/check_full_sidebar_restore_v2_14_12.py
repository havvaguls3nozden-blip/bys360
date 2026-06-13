# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

BAD_TOKENS = [
    "BYS360_EXECUTIVE_SUMMARY_SAFE_MENU_START",
    "BYS360_EXECUTIVE_SUMMARY_MENU_START",
    "bys360-exec-safe-group",
    "bys360-executive-summary-menu",
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    base = root / "app" / "templates" / "base.html"
    if not base.exists():
        print({"ok": False, "message": "base.html bulunamadı"})
        return 1

    text = read_text(base)
    offenders = [tok for tok in BAD_TOKENS if tok in text]
    if offenders:
        print({"ok": False, "bad_tokens": offenders})
        return 2

    required_any = ["Performans Yönetimi", "AI Karar Destek", "Sistem Ayarları"]
    present = [tok for tok in required_any if tok in text]
    if len(present) < 2:
        print({"ok": False, "message": "base.html içinde temel menü metinleri beklenen düzeyde görünmüyor", "present": present})
        return 3

    print({"ok": True, "message": "Kötü Yönetici Özeti enjeksiyonları temiz. Temel sol menü metinleri base.html içinde mevcut.", "present": present})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
