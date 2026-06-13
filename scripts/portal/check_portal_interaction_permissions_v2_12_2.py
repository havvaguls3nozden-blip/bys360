from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from app.models import RoleMenuDefault  # noqa: E402

REQUIRED = {
    "grup_baskani": ["portal_feed", "portal_post_interact", "portal_people", "portal_profiles"],
    "baskan": ["portal_feed", "portal_post_interact"],
    "baskan_yardimcisi": ["portal_feed", "portal_post_interact"],
    "mali_musavir": ["portal_feed", "portal_post_interact"],
    "koordinator": ["portal_feed", "portal_post_interact"],
}


def main() -> None:
    service_path = ROOT / "app" / "services" / "portal_permission_matrix.py"
    text = service_path.read_text(encoding="utf-8")
    required_markers = [
        "BYS360_PORTAL_ROLE_INTERACTION_FIX_V2_12_2",
        "PORTAL_ROLE_FIRST_KEYS",
        "PORTAL_ROLE_FIRST_ROLES",
        "portal_post_interact",
    ]
    missing = [m for m in required_markers if m not in text]
    if missing:
        raise SystemExit("Servis düzeltmesi eksik: " + ", ".join(missing))

    app = create_app()
    with app.app_context():
        for role, keys in REQUIRED.items():
            for key in keys:
                row = RoleMenuDefault.query.filter_by(role_name=role, menu_key=key).first()
                if row is None or not bool(row.is_visible):
                    raise SystemExit(f"Rol matrisi eksik/kapalı: {role} -> {key}")
    print("BYS360_PORTAL_ROLE_INTERACTION_FIX_V2_12_2_GATE_OK")


if __name__ == "__main__":
    main()
