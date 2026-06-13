from __future__ import annotations

import argparse
import json
import py_compile
from pathlib import Path

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_5_CHECK"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=None)
    args = parser.parse_args()
    root = Path(args.project_root or Path.cwd()).resolve()
    routes = read(root / "app/communication/daily_weather_mail_routes.py")
    base = read(root / "app/templates/base.html")
    template = read(root / "app/templates/communication/daily_weather_mail_settings.html")
    sections = read(root / "app/menu_registry_data_sections.py")

    checks: list[dict[str, object]] = []
    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("executive_get_route", "/executive-summary/daily-weather-mail" in routes)
    add("executive_settings_post", "/executive-summary/daily-weather-mail/settings" in routes)
    add("executive_send_now_post", "/executive-summary/daily-weather-mail/send-now" in routes)
    add("executive_dry_run_post", "/executive-summary/daily-weather-mail/dry-run" in routes)
    add("redirects_to_exec_url", 'redirect("/executive-summary/daily-weather-mail")' in routes)
    add("base_forced_exec_section", "BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_FORCE_SECTION_BEGIN" in base)
    add("base_exec_link", "/executive-summary/daily-weather-mail" in base and "Günlük Personel Bilgilendirme" in base)
    add("old_comms_nav_removed", "BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM" not in base)
    add("premium_template_title", "Yönetici Özeti | Günlük Personel Bilgilendirme" in template)
    add("selected_people_card", "Mail gönderilecek seçili kişiler" in template and "selectedPeopleCard" in template)
    add("template_posts_to_exec", "/executive-summary/daily-weather-mail/settings" in template and "/executive-summary/daily-weather-mail/send-now" in template)
    add("menu_registry_item", "daily_weather_mail" in sections and "Günlük Personel Bilgilendirme" in sections)

    compile_errors: list[str] = []
    for rel in [
        "app/communication/daily_weather_mail_routes.py",
        "app/menu_registry_data_sections.py",
        "app/menu_registry.py",
        "app/services/settings/effective_menu.py",
        "app/services/daily_weather_mail.py",
        "scripts/communication/repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
    ]:
        path = root / rel
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            compile_errors.append(f"{rel}: {exc}")
    add("compile_targets", not compile_errors, "; ".join(compile_errors))

    ok = all(item["ok"] for item in checks)
    payload = {"ok": ok, "version": VERSION, "checks": checks, "project_root": str(root)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if ok:
        print("BYS360_DAILY_WEATHER_MAIL_V1_0_5_CHECK_OK")
        return 0
    print("BYS360_DAILY_WEATHER_MAIL_V1_0_5_CHECK_FAIL")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
