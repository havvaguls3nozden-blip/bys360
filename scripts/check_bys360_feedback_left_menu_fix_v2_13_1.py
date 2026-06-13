from __future__ import annotations

import argparse
from pathlib import Path

VERSION = "BYS360_GERI_BILDIRIM_SOL_MENU_FIX_V2_13_1"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{VERSION} gate")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    errors: list[str] = []

    base = root / "app" / "templates" / "base.html"
    route = root / "app" / "communication" / "user_feedback_routes.py"
    routes = root / "app" / "routes.py"
    for path in [base, route, routes, root / "app" / "templates" / "feedback" / "quick_feedback.html"]:
        if not path.exists():
            errors.append(f"Eksik dosya: {path}")

    if base.exists():
        b = read_text(base)
        required_base = [
            "BYS360_FEEDBACK_LEFT_MENU_V2_13_1_BEGIN",
            "feedback_quick_visible",
            "Geri Bildirim Gönder",
            "main.bys360_feedback_new",
            "/feedback/gonder",
            "data-menu-key=\"feedback_quick\"",
        ]
        for item in required_base:
            if item not in b:
                errors.append(f"base.html içinde bulunamadı: {item}")

    if route.exists():
        r = read_text(route)
        if '@menu_key_required("feedback_dashboard")\ndef bys360_feedback_new' in r:
            errors.append("Yeni geri bildirim ekranı hâlâ feedback_dashboard menü yetkisine bağlı.")
        if "def bys360_feedback_new" not in r or "def bys360_feedback_success" not in r:
            errors.append("Geri bildirim route fonksiyonları bulunamadı.")

    if routes.exists():
        rr = read_text(routes)
        if "user_feedback_routes" not in rr:
            errors.append("app/routes.py içinde user_feedback_routes importu yok.")

    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"{VERSION}_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
