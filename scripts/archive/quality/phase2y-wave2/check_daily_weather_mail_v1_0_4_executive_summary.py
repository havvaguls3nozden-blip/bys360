from __future__ import annotations

import json
import py_compile
from pathlib import Path

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXECUTIVE_SUMMARY_LINK_CHECK"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def main() -> int:
    root = Path.cwd()
    checks = []
    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    routes = read(root / "app/communication/daily_weather_mail_routes.py")
    base = read(root / "app/templates/base.html")
    menu_sections = read(root / "app/menu_registry_data_sections.py")
    template = read(root / "app/templates/communication/daily_weather_mail_settings.html")

    add("executive_get_route", "/executive-summary/daily-weather-mail" in routes)
    add("executive_post_settings_route", "/executive-summary/daily-weather-mail/settings" in routes)
    add("executive_post_send_now_route", "/executive-summary/daily-weather-mail/send-now" in routes)
    add("executive_post_dry_run_route", "/executive-summary/daily-weather-mail/dry-run" in routes)
    add("redirects_to_executive_url", 'redirect("/executive-summary/daily-weather-mail")' in routes)
    add("base_has_executive_nav", "BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC" in base and "/executive-summary/daily-weather-mail" in base)
    add("base_old_comms_nav_removed", "BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM" not in base)
    add("registry_has_executive_item", "BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_MENU_ITEM" in menu_sections)
    add("template_posts_to_executive", "/executive-summary/daily-weather-mail/send-now" in template and "/executive-summary/daily-weather-mail/settings" in template)

    compile_errors = []
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
                compile_errors.append(f"{rel}: {exc}")
    add("compile_target_files", not compile_errors, "; ".join(compile_errors))

    ok = all(c["ok"] for c in checks)
    print(json.dumps({"version": VERSION, "ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    if ok:
        print("BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXECUTIVE_SUMMARY_LINK_CHECK_OK")
        return 0
    print("BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXECUTIVE_SUMMARY_LINK_CHECK_FAIL")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
