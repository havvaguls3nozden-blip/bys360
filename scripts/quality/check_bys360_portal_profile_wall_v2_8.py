from __future__ import annotations
from pathlib import Path
import sys

REQUIRED = [
    ("app/models/portal_models.py", "wall_owner_user_id"),
    ("app/models/portal_models.py", "wall_owner = db.relationship"),
    ("app/services/portal_service.py", "BYS360_PORTAL_PROFILE_WALL_V2_8_CAN_POST_TO_WALL"),
    ("app/services/portal_service.py", "wall_owner_id: int | None = None"),
    ("app/services/portal_service.py", "BYS360_PORTAL_PROFILE_WALL_V2_8_WALL_FILTER"),
    ("app/portal/routes.py", "BYS360_PORTAL_PROFILE_WALL_V2_8_WALL_HELPER"),
    ("app/portal/routes.py", "wall_owner_user_id=wall_owner_user_id"),
    ("app/portal/routes.py", "wall_owner_id=user_id"),
    ("app/templates/portal/profile.html", "BYS360_PORTAL_PROFILE_WALL_V2_8_PROFILE_COMPOSER"),
    ("app/templates/portal/_composer.html", "target_wall_user_id"),
    ("app/templates/portal/_post_card.html", "portal-wall-owner-line"),
    ("app/static/css/bys360_portal.css", "BYS360_PORTAL_PROFILE_WALL_V2_8_CSS_BEGIN"),
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
        print("BYS360_PORTAL_PROFILE_WALL_V2_8_GATE_FAIL")
        for item in missing:
            print(" - " + item)
        return 1
    print("BYS360_PORTAL_PROFILE_WALL_V2_8_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
