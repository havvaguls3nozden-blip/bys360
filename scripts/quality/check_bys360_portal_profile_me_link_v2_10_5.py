from __future__ import annotations

import argparse
import sys
from pathlib import Path

MARKER = "BYS360_PORTAL_PROFILE_ME_LINK_V2_10_5"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    people = root / "app" / "templates" / "portal" / "people.html"
    routes = root / "app" / "portal" / "routes.py"
    errors: list[str] = []

    if not people.exists():
        errors.append("people.html bulunamadı")
    else:
        text = read_text(people)
        if "portal_profile_me" in text:
            errors.append("people.html içinde portal_profile_me kaldı")
        if "main.portal_my_profile" not in text:
            errors.append("people.html içinde main.portal_my_profile yok")
        if "Kendi Duvarım" not in text:
            errors.append("people.html içinde Kendi Duvarım bağlantısı yok")

    if not routes.exists():
        errors.append("routes.py bulunamadı")
    else:
        rtext = read_text(routes)
        if "def portal_my_profile" not in rtext:
            errors.append("routes.py içinde portal_my_profile yok")
        if "/portal/profile/me" not in rtext:
            errors.append("routes.py içinde /portal/profile/me yok")

    if errors:
        print(f"{MARKER}_QUALITY_FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"{MARKER}_QUALITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
