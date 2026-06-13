# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_6_CHECK"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--project-root", default=".")
    args = p.parse_args()
    root = Path(args.project_root).resolve()

    base = read(root / "app/templates/base.html")
    routes = read(root / "app/communication/daily_weather_mail_routes.py")
    sections = read(root / "app/menu_registry_data_sections.py")
    template = read(root / "app/templates/communication/daily_weather_mail_settings.html")

    errors: list[str] = []
    warnings: list[str] = []

    forced_count = base.count("BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_FORCE_SECTION_BEGIN")
    item_count = base.count("BYS360_DAILY_WEATHER_MAIL_V1_0_6_EXEC_ITEM_BEGIN")
    exec_label_count = len(re.findall(r"<span>\s*(?:Yönetici Özeti|Yonetici Ozeti)\s*</span>", base, flags=re.I))

    if forced_count:
        errors.append("Eski V1.0.5 ayrı Yönetici Özeti section bloğu base.html içinde hâlâ duruyor.")
    if item_count > 1:
        errors.append(f"Günlük Personel Bilgilendirme base.html içinde {item_count} kez eklenmiş; tek olmalı.")
    if item_count < 1 and "daily_weather_mail" not in sections:
        errors.append("Günlük Personel Bilgilendirme ne base.html ne de menu_registry_data_sections.py içinde bulunamadı.")

    if "/executive-summary/daily-weather-mail" not in routes:
        errors.append("Yönetici Özeti günlük hava maili route aliası eksik.")
    if "Günlük Personel Bilgilendirme" not in (base + sections):
        errors.append("Menü etiketi bulunamadı: Günlük Personel Bilgilendirme")
    if "Mail gönderilecek seçili kişiler" not in template and "Seçili kişiler" not in template:
        warnings.append("Template içinde seçili kişiler kartı etiketi bulunamadı; premium template eski kalmış olabilir.")

    result = {
        "ok": not errors,
        "version": VERSION,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "executive_summary_label_count_in_base": exec_label_count,
            "old_forced_section_count": forced_count,
            "daily_weather_item_count_in_base": item_count,
            "daily_weather_item_count_in_registry_sections": sections.count("daily_weather_mail"),
        },
        "expected_menu_path": "Sol Menü > Yönetici Özeti > Günlük Personel Bilgilendirme",
        "expected_url": "/executive-summary/daily-weather-mail",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
