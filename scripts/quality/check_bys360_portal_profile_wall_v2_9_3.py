from __future__ import annotations

import sys
from pathlib import Path


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    service = project_root / "app" / "services" / "portal_service.py"
    routes = project_root / "app" / "portal" / "routes.py"
    post_card = project_root / "app" / "templates" / "portal" / "_post_card.html"
    people = project_root / "app" / "templates" / "portal" / "people.html"
    errors: list[str] = []
    for path in (service, routes, post_card, people):
        if not path.exists():
            errors.append(f"Eksik dosya: {path}")
    if service.exists():
        text = read_text(service)
        if "can_user_delete_post(current_user, post)" in text:
            errors.append("portal_service.py içinde current_user silme çağrısı kaldı")
        if "can_user_delete_post(viewer, post)" in text:
            errors.append("portal_service.py içinde viewer silme çağrısı kaldı")
        if "can_user_delete_post(user, post)" not in text:
            errors.append("portal_service.py içinde doğru user silme çağrısı yok")
        if "def can_user_delete_post" not in text:
            errors.append("can_user_delete_post fonksiyonu yok")
        if "def can_user_post_to_wall" not in text:
            errors.append("can_user_post_to_wall fonksiyonu yok")
    if routes.exists():
        rtext = read_text(routes)
        for needle in ("portal_people", "portal_delete_post", "wall_owner_id"):
            if needle not in rtext:
                errors.append(f"routes.py içinde {needle} yok")
    if post_card.exists():
        ptext = read_text(post_card)
        if "portal-wall-owner-line" not in ptext:
            errors.append("_post_card.html içinde portal-wall-owner-line yok")
        if "portal-delete-post" not in ptext:
            errors.append("_post_card.html içinde portal-delete-post yok")
    if people.exists() and "Personel Duvarları" not in read_text(people):
        errors.append("people.html Personel Duvarları başlığını içermiyor")
    if errors:
        print("BYS360_PORTAL_PROFILE_WALL_V2_9_3_GATE_FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("BYS360_PORTAL_PROFILE_WALL_V2_9_3_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
