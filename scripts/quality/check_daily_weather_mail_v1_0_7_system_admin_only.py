# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path
from typing import Any

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_ONLY_CHECK"
SYSTEM_ADMIN_ROLES = {"admin", "super_admin", "system_admin", "sistem_yoneticisi"}
DISALLOWED = {"baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "performans_yetkilisi"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    errors: list[str] = []
    info: dict[str, Any] = {"version": VERSION, "project_root": str(root)}

    route = root / "app/communication/daily_weather_mail_routes.py"
    if not route.exists():
        errors.append("daily_weather_mail_routes.py bulunamadı")
    else:
        text = read(route)
        for role in SYSTEM_ADMIN_ROLES:
            if f'"{role}"' not in text and f"'{role}'" not in text:
                errors.append(f"route allowed role eksik: {role}")
        for role in DISALLOWED:
            # Sadece _ALLOWED_ROLES bloğunda görünürse hata sayılır.
            m = re.search(r"_ALLOWED_ROLES\s*=\s*\{(.*?)\}", text, flags=re.S)
            if m and (f'"{role}"' in m.group(1) or f"'{role}'" in m.group(1)):
                errors.append(f"route disallowed role hâlâ açık: {role}")
        if "return _role_name() in _ALLOWED_ROLES" not in text:
            errors.append("route guard rol bazlı sistem yöneticisi kontrolüne dönmemiş")

    registry = root / "app/menu_registry_data_sections.py"
    if registry.exists():
        text = read(registry)
        m = re.search(r"BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_MENU_ITEM(.*?)#\s*/BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_MENU_ITEM", text, flags=re.S)
        if not m:
            errors.append("V1.0.7 menu item bulunamadı")
        else:
            block = m.group(1)
            for role in DISALLOWED:
                if role in block:
                    errors.append(f"menu item disallowed role içeriyor: {role}")
            for role in SYSTEM_ADMIN_ROLES:
                if role not in block:
                    errors.append(f"menu item allowed role eksik: {role}")

    base = root / "app/templates/base.html"
    if base.exists():
        text = read(base)
        if "BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_ITEM_BEGIN" not in text:
            errors.append("base.html V1.0.7 sistem yöneticisi gate item bulunamadı")
        if "_daily_weather_role in" not in text:
            errors.append("base.html rol kapısı bulunamadı")

    for rel in [
        "app/communication/daily_weather_mail_routes.py",
        "app/menu_registry_data_sections.py",
        "app/menu_registry.py",
        "app/services/settings/effective_menu.py",
    ]:
        p = root / rel
        if p.exists():
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as exc:
                errors.append(f"compile hata {rel}: {exc}")

    info["ok"] = not errors
    info["errors"] = errors
    print(json.dumps(info, ensure_ascii=False, indent=2))
    if errors:
        print(f"{VERSION}_FAIL")
        return 2
    print(f"{VERSION}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
