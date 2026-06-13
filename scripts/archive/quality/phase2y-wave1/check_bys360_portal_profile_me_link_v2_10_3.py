from __future__ import annotations

import sys
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    errors: list[str] = []
    routes = project_root / "app" / "portal" / "routes.py"
    people = project_root / "app" / "templates" / "portal" / "people.html"

    if not routes.exists():
        errors.append("app/portal/routes.py bulunamadı")
    else:
        rt = read_text(routes)
        if 'def portal_my_profile' not in rt:
            errors.append("portal_my_profile route fonksiyonu yok")
        if 'def portal_post_delete' not in rt:
            errors.append("portal_post_delete route fonksiyonu yok")

    if not people.exists():
        errors.append("app/templates/portal/people.html bulunamadı")
    else:
        pt = read_text(people)
        if 'portal_profile_me' in pt:
            errors.append("people.html eski portal_profile_me endpoint adını içeriyor")
        if 'main.portal_my_profile' not in pt and '/portal/profile/me' not in pt:
            errors.append("people.html kendi duvarım bağlantısı yok")

    template_root = project_root / "app" / "templates"
    if template_root.exists():
        for path in template_root.rglob('*.html'):
            if 'portal_profile_me' in read_text(path):
                errors.append(f"{path.relative_to(project_root)} içinde portal_profile_me kaldı")

    if errors:
        print('BYS360_PORTAL_PROFILE_ME_LINK_V2_10_3_GATE_FAIL')
        for e in errors:
            print(' - ' + e)
        return 1
    print('BYS360_PORTAL_PROFILE_ME_LINK_V2_10_3_GATE_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
