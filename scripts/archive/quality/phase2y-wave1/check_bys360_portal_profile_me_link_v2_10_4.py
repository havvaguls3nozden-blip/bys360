from __future__ import annotations
import argparse
from pathlib import Path

MARKER = "BYS360_PORTAL_PROFILE_ME_LINK_V2_10_4"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    people = root / "app" / "templates" / "portal" / "people.html"
    routes = root / "app" / "portal" / "routes.py"
    errors = []
    if not people.exists(): errors.append("people.html yok")
    else:
        text = people.read_text(encoding="utf-8", errors="replace")
        if "portal_profile_me" in text: errors.append("people.html eski endpoint içeriyor")
        if "portal_my_profile" not in text and "/portal/profile/me" not in text: errors.append("kendi duvarım bağlantısı yok")
    if not routes.exists(): errors.append("routes.py yok")
    else:
        rt = routes.read_text(encoding="utf-8", errors="replace")
        if "def portal_my_profile" not in rt: errors.append("portal_my_profile route yok")
    if errors:
        print(f"{MARKER}_QUALITY_FAIL")
        for e in errors: print(" - " + e)
        return 1
    print(f"{MARKER}_QUALITY_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
