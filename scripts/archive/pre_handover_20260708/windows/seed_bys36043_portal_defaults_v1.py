from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

VERSION = "BYS36043_PORTAL_DEFAULTS_V1"

PORTAL_MATRIX_KEYS = {
    "portal_feed", "portal_people", "portal_profiles", "portal_post_create", "portal_wall_post",
    "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_groups",
    "portal_group_create", "portal_moderation",
}
PORTAL_DEFAULTS = {
    "admin": set(PORTAL_MATRIX_KEYS),
    "baskan": set(PORTAL_MATRIX_KEYS),
    "baskan_yardimcisi": set(PORTAL_MATRIX_KEYS),
    "grup_baskani": set(PORTAL_MATRIX_KEYS),
    "mali_musavir": set(PORTAL_MATRIX_KEYS),
    "koordinator": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "birim_sorumlusu": set(PORTAL_MATRIX_KEYS) - {"portal_moderation"},
    "personel": set(PORTAL_MATRIX_KEYS) - {"portal_group_create", "portal_moderation"},
}
PORTAL_CORE_USER_KEYS = {"portal_feed", "portal_profiles", "portal_people", "portal_groups"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--force-user-core", action="store_true", default=False)
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from app import create_app
    from app.extensions import db
    from app.models import RoleMenuDefault, User, UserMenuPermission

    app = create_app()
    changes = {"role_inserted": 0, "role_updated": 0, "user_inserted": 0, "user_updated": 0}
    with app.app_context():
        for role, allowed_keys in PORTAL_DEFAULTS.items():
            for key in sorted(PORTAL_MATRIX_KEYS):
                should_show = key in allowed_keys
                row = RoleMenuDefault.query.filter_by(role_name=role, menu_key=key).first()
                if row is None:
                    db.session.add(RoleMenuDefault(
                        role_name=role,
                        menu_key=key,
                        is_visible=should_show,
                        source_type="bys36043_portal_seed",
                        note="BYS360 43 canlı portal restore varsayılanı",
                    ))
                    changes["role_inserted"] += 1
                elif bool(row.is_visible) != bool(should_show):
                    # Portalın canlıda erişim yetkiniz yok döngüsüne düşmemesi için rol varsayılanını güncelliyoruz.
                    row.is_visible = should_show
                    row.source_type = "bys36043_portal_seed"
                    row.note = "BYS360 43 canlı portal restore varsayılanı"
                    changes["role_updated"] += 1

        if args.force_user_core:
            active_users = User.query.filter_by(is_active=True).all()
            for user in active_users:
                for key in sorted(PORTAL_CORE_USER_KEYS):
                    row = UserMenuPermission.query.filter_by(user_id=user.id, menu_key=key).first()
                    if row is None:
                        db.session.add(UserMenuPermission(
                            user_id=user.id,
                            menu_key=key,
                            is_visible=True,
                            source_type="bys36043_portal_recovery",
                        ))
                        changes["user_inserted"] += 1
                    elif not bool(row.is_visible):
                        row.is_visible = True
                        row.source_type = "bys36043_portal_recovery"
                        changes["user_updated"] += 1
        db.session.commit()

    print(json.dumps({"version": VERSION, **changes}, ensure_ascii=False, indent=2))
    print(f"{VERSION}_OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"{VERSION}_FAIL")
        print(str(exc))
        raise
