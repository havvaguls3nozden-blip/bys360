from __future__ import annotations

"""BYS360 Portal Grup Başkanı beğeni/yorum yetki seed düzeltmesi."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import RoleMenuDefault  # noqa: E402

PORTAL_KEYS = [
    "portal_feed",
    "portal_people",
    "portal_profiles",
    "portal_post_create",
    "portal_wall_post",
    "portal_post_interact",
    "portal_post_report",
    "portal_post_delete",
    "portal_groups",
    "portal_group_create",
    "portal_moderation",
]

ROLE_KEY_MAP = {
    "admin": set(PORTAL_KEYS),
    "sistem_yoneticisi": set(PORTAL_KEYS),
    "baskan": set(PORTAL_KEYS),
    "baskan_yardimcisi": set(PORTAL_KEYS),
    "grup_baskani": set(PORTAL_KEYS),
    "mali_musavir": set(PORTAL_KEYS),
    "koordinator": set(PORTAL_KEYS) - {"portal_moderation"},
    "birim_sorumlusu": set(PORTAL_KEYS) - {"portal_moderation"},
    "personel": set(PORTAL_KEYS) - {"portal_group_create", "portal_moderation"},
}


def upsert_role_default(role_name: str, menu_key: str, is_visible: bool) -> None:
    row = RoleMenuDefault.query.filter_by(role_name=role_name, menu_key=menu_key).first()
    if row is None:
        row = RoleMenuDefault(
            role_name=role_name,
            menu_key=menu_key,
            is_visible=is_visible,
            source_type="seed_v2_12_2",
            note="Portal etkileşim ve rol matrisi canlı düzeltmesi",
        )
        db.session.add(row)
        return
    row.is_visible = is_visible
    row.source_type = "seed_v2_12_2"
    row.note = "Portal etkileşim ve rol matrisi canlı düzeltmesi"


def main() -> None:
    app = create_app()
    with app.app_context():
        for role_name, allowed_keys in ROLE_KEY_MAP.items():
            for key in PORTAL_KEYS:
                upsert_role_default(role_name, key, key in allowed_keys)
        db.session.commit()
        print("BYS360_PORTAL_ROLE_INTERACTION_FIX_V2_12_2_SEED_OK")


if __name__ == "__main__":
    main()
