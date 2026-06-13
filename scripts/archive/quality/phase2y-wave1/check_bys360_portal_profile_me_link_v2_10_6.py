from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    project_root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd().resolve()
    people = project_root / "app" / "templates" / "portal" / "people.html"
    routes = project_root / "app" / "portal" / "routes.py"
    errors: list[str] = []

    if not people.exists():
        errors.append("people.html bulunamadı")
    else:
        text = people.read_text(encoding="utf-8", errors="replace")
        if "portal_profile_me" in text:
            errors.append("people.html içinde portal_profile_me kaldı")
        if "portal_my_profile" not in text:
            errors.append("people.html içinde portal_my_profile yok")

    if not routes.exists():
        errors.append("routes.py bulunamadı")
    else:
        rt = routes.read_text(encoding="utf-8", errors="replace")
        if "def portal_my_profile" not in rt or "/portal/profile/me" not in rt:
            errors.append("portal_my_profile route'u doğrulanamadı")

    if errors:
        print("BYS360_PORTAL_PROFILE_ME_LINK_V2_10_6_GATE_FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    print("BYS360_PORTAL_PROFILE_ME_LINK_V2_10_6_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
