from __future__ import annotations

from pathlib import Path
import py_compile
import sys

REQUIRED = {
    "app/live_scope.py": ["BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_LIVE_SCOPE_BEGIN", "portal_post_delete", "portal_wall_post"],
    "app/menu_registry_data_performance.py": ["BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROLE_DEFAULTS_BEGIN", "portal_post_create", "portal_group_create"],
    "app/main_handlers/account_communication_helpers.py": ["BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_POLICY_BEGIN", "Kurumsal Portal Rol Matrisi", "portal_people"],
    "app/main_handlers/account_settings_helpers.py": ["portal-role-policy", "Portal Rol Matrisi"],
    "app/services/settings/effective_menu.py": ["BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_EFFECTIVE_MENU_BEGIN", "PORTAL_ROLE_MATRIX_V2_12_KEYS"],
    "app/services/role_matrix_ui_service.py": ["BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROLE_MATRIX_CENTER_BEGIN", "Kurumsal Portal Rol Matrisi"],
    "app/services/portal_permission_matrix.py": ["portal_permission_allowed", "PORTAL_MATRIX_KEYS"],
    "app/portal/routes.py": ["portal_permission_allowed", "_portal_has_permission", "portal_post_delete", "portal_group_create"],
}


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    errors: list[str] = []
    for rel, needles in REQUIRED.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel} bulunamadı")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel}: {needle} yok")
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                errors.append(f"{rel}: compile hata: {exc}")
    routes_text = (root / "app" / "portal" / "routes.py").read_text(encoding="utf-8")
    for key in ["portal_post_create", "portal_wall_post", "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_people", "portal_group_create"]:
        if key not in routes_text:
            errors.append(f"routes.py içinde işlem yetkisi kullanılmıyor: {key}")
    if errors:
        print("BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_GATE_FAIL")
        for err in errors:
            print(f" - {err}")
        return 1
    print("BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_GATE_OK")
    print("BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
