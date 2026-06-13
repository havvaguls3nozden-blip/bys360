from __future__ import annotations

import re
import sys
from pathlib import Path

VERSION = "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_4"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    project_root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    errors: list[str] = []

    auth_routes = project_root / "app" / "auth" / "routes.py"
    auth_handlers = project_root / "app" / "main_handlers" / "auth_handlers.py"
    routes = project_root / "app" / "routes.py"

    for path in [auth_routes, auth_handlers, routes]:
        require(path.exists(), f"Eksik dosya: {path}", errors)
    if errors:
        for e in errors:
            print(f"HATA: {e}")
        return 2

    route_text = read_text(auth_routes)
    handler_text = read_text(auth_handlers)
    routes_text = read_text(routes)

    logout_route_match = re.search(
        r'@main_bp\.route\(\s*["\']/logout["\'][^\n]*methods\s*=\s*\[[^\]]*["\']GET["\'][^\]]*["\']POST["\'][^\]]*\]',
        route_text,
    )
    require(bool(logout_route_match), "Logout route GET ve POST desteklemiyor.", errors)

    route_start = route_text.find('@main_bp.route("/logout"')
    if route_start == -1:
        route_start = route_text.find("@main_bp.route('/logout'")
    next_route = route_text.find("@main_bp.", route_start + 1) if route_start != -1 else -1
    logout_block = route_text[route_start: next_route if next_route != -1 else len(route_text)] if route_start != -1 else ""
    require("@login_required" not in logout_block, "Logout route üzerinde login_required kalmış; bozuk oturum temizlenemeyebilir.", errors)

    for token in [
        "make_response",
        "_bys360_delete_auth_cookies",
        "_bys360_no_store_response",
        "logout_user()",
        "session.clear()",
        "delete_cookie",
        "remember_token",
        "Clear-Site-Data",
        "X-BYS360-Logout-Fix",
        "V2.13.4",
    ]:
        require(token in handler_text, f"auth_handlers.py logout güçlendirme eksiği: {token}", errors)

    require("bys360_no_store_authenticated_pages" in routes_text, "Kimlikli HTML sayfaları için no-store header bloğu yok.", errors)
    for token in ["no-store", "current_user.is_authenticated", "/logout", "/login"]:
        require(token in routes_text, f"no-store kontrol eksiği: {token}", errors)

    sw_errors = []
    sw_seen = False
    for rel in [
        "app/static/pwa/bys360-sw.js",
        "app/static/pwa/service-worker.js",
        "app/static/pwa/sw.js",
        "app/static/service-worker.js",
    ]:
        p = project_root / rel
        if p.exists():
            sw_seen = True
            t = read_text(p)
            if "bys360-logout-force-clear-v2-13-4" not in t:
                sw_errors.append(rel)
    require(not sw_errors, "PWA service worker logout cache sürümü güncel değil: " + ", ".join(sw_errors), errors)
    if not sw_seen:
        print("UYARI: PWA service worker dosyası bulunmadı; web logout düzeltmesi yine uygulandı.")

    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print(f"HATA: {e}")
        return 1

    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
