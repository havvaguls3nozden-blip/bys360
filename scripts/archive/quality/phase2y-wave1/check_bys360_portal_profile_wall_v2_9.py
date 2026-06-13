from __future__ import annotations
from pathlib import Path
import sys

REQUIRED = [
    ("app/models/portal_models.py", "wall_owner_user_id"),
    ("app/models/portal_models.py", "wall_owner = db.relationship"),
    ("app/services/portal_service.py", "BYS360_PORTAL_PROFILE_WALL_V2_9_WALL_PERMISSIONS"),
    ("app/services/portal_service.py", "def can_user_delete_post"),
    ("app/services/portal_service.py", "wall_owner_id: int | None = None"),
    ("app/portal/routes.py", "BYS360_PORTAL_PROFILE_WALL_V2_9_PEOPLE_ROUTE"),
    ("app/portal/routes.py", "BYS360_PORTAL_PROFILE_WALL_V2_9_DELETE_ROUTE"),
    ("app/portal/routes.py", "wall_owner_user_id=wall_owner_user_id"),
    ("app/portal/routes.py", "wall_owner_id=user_id"),
    ("app/templates/portal/_tabs.html", "active_portal_tab == 'people'"),
    ("app/templates/portal/_composer.html", "target_wall_user_id"),
    ("app/templates/portal/profile.html", "BYS360_PORTAL_PROFILE_WALL_V2_9_PROFILE_SEARCH"),
    ("app/templates/portal/people.html", "Personel duvarı ara"),
    ("app/templates/portal/_post_card.html", "portal_post_delete"),
    ("app/static/css/bys360_portal.css", "BYS360_PORTAL_PROFILE_WALL_V2_9_CSS"),
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing = []
    for rel, marker in REQUIRED:
        path = root / rel
        if not path.exists():
            missing.append(f"{rel}: dosya yok")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if marker not in text:
            missing.append(f"{rel}: {marker}")
    if missing:
        print("BYS360_PORTAL_PROFILE_WALL_V2_9_GATE_FAIL")
        for item in missing:
            print(" - " + item)
        return 1
    print("BYS360_PORTAL_PROFILE_WALL_V2_9_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
