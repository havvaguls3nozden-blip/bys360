from __future__ import annotations

"""BYS360 Portal rol matrisi V2.12.3 gate kontrolü."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.models import RoleMenuDefault  # noqa: E402

REQUIRED_TRUE = {
    "admin": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "sistem_yoneticisi": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "baskan": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "baskan_yardimcisi": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "grup_baskani": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "mali_musavir": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "koordinator": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "birim_sorumlusu": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
    "personel": ["portal_feed", "portal_post_interact", "portal_post_like", "portal_post_comment", "portal_comment_reply", "portal_comment_mention"],
}

REQUIRED_FALSE = {
    "personel": ["portal_group_create", "portal_moderation", "portal_post_delete"],
    "koordinator": ["portal_moderation"],
    "birim_sorumlusu": ["portal_moderation"],
}


def must_find(role: str, key: str):
    row = RoleMenuDefault.query.filter_by(role_name=role, menu_key=key).first()
    if row is None:
        raise AssertionError(f"Eksik rol matrisi kaydı: role={role} key={key}")
    return row


def main() -> None:
    app = create_app()
    with app.app_context():
        errors = []
        for role, keys in REQUIRED_TRUE.items():
            for key in keys:
                try:
                    row = must_find(role, key)
                    if row.is_visible is not True:
                        errors.append(f"Açık olmalı: role={role} key={key}")
                except Exception as exc:
                    errors.append(str(exc))
        for role, keys in REQUIRED_FALSE.items():
            for key in keys:
                try:
                    row = must_find(role, key)
                    if row.is_visible is not False:
                        errors.append(f"Kapalı olmalı: role={role} key={key}")
                except Exception as exc:
                    errors.append(str(exc))
        if errors:
            print("BYS360_PORTAL_ROLE_MATRIX_DEEP_V2_12_3_GATE_FAIL")
            for e in errors:
                print(" - " + e)
            raise SystemExit(1)
        print("BYS360_PORTAL_ROLE_MATRIX_DEEP_V2_12_3_GATE_OK")


if __name__ == "__main__":
    main()
