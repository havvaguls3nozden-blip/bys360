from __future__ import annotations

import json
import py_compile
from pathlib import Path

REQUIRED_FILES = [
    "app/services/daily_weather_mail.py",
    "app/communication/daily_weather_mail_routes.py",
    "app/templates/communication/daily_weather_mail_settings.html",
    "scripts/communication/send_daily_weather_personnel_mail.py",
    "scripts/windows/install_bys360_daily_weather_mail_task.ps1",
]

REQUIRED_TEXT = {
    "app/routes.py": ["daily_weather_mail_routes"],
    "app/templates/base.html": ["daily_weather_mail", "Günlük Bilgilendirme"],
    "app/menu_registry_data_sections.py": ["daily_weather_mail", "Günlük Bilgilendirme Maili"],
    "app/services/settings/effective_menu.py": ["BYS360_DAILY_WEATHER_MAIL_EFFECTIVE_MENU_V1"],
}


def main() -> int:
    root = Path.cwd()
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            errors.append(f"Eksik dosya: {rel}")
        elif path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                errors.append(f"Python derleme hatası: {rel}: {exc}")
    for rel, markers in REQUIRED_TEXT.items():
        path = root / rel
        if not path.exists():
            errors.append(f"Eksik hedef dosya: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in markers:
            if marker not in text:
                errors.append(f"Marker bulunamadı: {rel} -> {marker}")
    result = {"ok": not errors, "errors": errors, "version": "BYS360_DAILY_WEATHER_MAIL_V1_0"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
