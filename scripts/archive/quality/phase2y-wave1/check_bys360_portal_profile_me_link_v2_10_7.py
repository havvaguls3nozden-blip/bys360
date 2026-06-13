from __future__ import annotations

import pathlib
import sys

MARKER = "BYS360_PORTAL_PROFILE_ME_LINK_V2_10_7"
OLD = "portal_profile_me"
NEW = "portal_my_profile"


def main() -> int:
    project_root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems: list[str] = []
    for root in [project_root / "app" / "templates", project_root / "app" / "portal", project_root / "app" / "services"]:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".html", ".py", ".js", ".css"}:
                text = path.read_text(encoding="utf-8", errors="replace")
                if OLD in text:
                    problems.append(f"{path.relative_to(project_root)} içinde {OLD} kaldı")
    people = project_root / "app" / "templates" / "portal" / "people.html"
    if people.exists():
        text = people.read_text(encoding="utf-8", errors="replace")
        if NEW not in text:
            problems.append("people.html içinde portal_my_profile yok")
    else:
        problems.append("people.html bulunamadı")
    if problems:
        print(f"{MARKER}_QUALITY_FAIL")
        for p in problems:
            print(f" - {p}")
        return 1
    print(f"{MARKER}_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
