# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path

VERSION = "BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_PROFESSIONAL_CHECK"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    errors: list[str] = []
    info: dict = {"version": VERSION, "project_root": str(root)}

    base_path = root / "app/templates/base.html"
    if not base_path.exists():
        errors.append("base.html bulunamadı")
    else:
        base = read(base_path)
        label_count = len(re.findall(r"<span>\s*(?:Yönetici Özeti|Yonetici Ozeti)\s*</span>", base, flags=re.I))
        info["yonetici_ozeti_label_count"] = label_count
        if label_count != 1:
            errors.append(f"base.html içinde Yönetici Özeti başlığı 1 olmalı; bulunan: {label_count}")
        if "BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_MENU_BEGIN" not in base:
            errors.append("base.html admin-only Yönetici Özeti menü bloğu yok")
        if "bys360_exec_admin_visible" not in base or "sistem_yoneticisi" not in base:
            errors.append("base.html sistem yöneticisi görünürlük kapısı eksik")
        for old_marker in ["V1_0_5_EXEC_FORCE_SECTION_BEGIN", "V1_0_6_EXEC_ITEM_BEGIN", "V1_0_7_SYSTEM_ADMIN_ITEM_BEGIN"]:
            if old_marker in base:
                errors.append(f"base.html eski menü marker kalıntısı var: {old_marker}")

    route_path = root / "app/dashboard/routes.py"
    if not route_path.exists():
        errors.append("app/dashboard/routes.py bulunamadı")
    else:
        routes = read(route_path)
        for token in ["/dashboard/yonetici-ozeti", "_bys360_exec_is_system_admin", "executive_summary_admin_panel.html", "summary_recipient_user_ids"]:
            if token not in routes:
                errors.append(f"dashboard route token eksik: {token}")

    template_path = root / "app/templates/dashboard/executive_summary_admin_panel.html"
    if not template_path.exists():
        errors.append("executive_summary_admin_panel.html bulunamadı")
    else:
        tpl = read(template_path)
        for anchor in ["otomatik-epostalar", "mail-loglari", "zamanlanmis-isler", "test-gonderimi", "ozet-alicilari"]:
            if f'id="{anchor}"' not in tpl:
                errors.append(f"template anchor eksik: {anchor}")
        if "Yönetici özeti gönderilecek kişiler" not in tpl:
            errors.append("template alıcı kartı eksik")

    registry = root / "app/menu_registry_data_sections.py"
    if registry.exists():
        reg = read(registry)
        block = re.search(r"BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_SECTION(.*?)#\s*/BYS360_EXECUTIVE_SUMMARY_V1_0_8_ADMIN_SECTION", reg, flags=re.S)
        if not block:
            errors.append("menu_registry_data_sections V1.0.8 admin section yok")
        else:
            b = block.group(1)
            for role in ["admin", "super_admin", "system_admin", "sistem_yoneticisi"]:
                if role not in b:
                    errors.append(f"registry admin role eksik: {role}")
            for role in ["baskan", "koordinator", "personel", "performans_yetkilisi"]:
                if role in b:
                    errors.append(f"registry içinde yetkisiz rol kalmış: {role}")

    for rel in [
        "app/dashboard/routes.py",
        "app/menu_registry.py",
        "app/menu_registry_data_sections.py",
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
