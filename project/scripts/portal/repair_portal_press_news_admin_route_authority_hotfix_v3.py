from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PACKAGE = "BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3"
PRESS_KEY = "portal_press_news"
ADMIN_ROLES = {"admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"}
NON_ADMIN_ROLES = {
    "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı",
    "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir",
    "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_role_expr() -> str:
    return (
        "def _portal_press_news_normalize_role(value) -> str:\n"
        "    text = str(value or '').strip().lower().replace('-', '_').replace(' ', '_')\n"
        "    return (text.replace('İ', 'i').replace('I', 'i').replace('ı', 'i')\n"
        "                .replace('Ş', 's').replace('ş', 's')\n"
        "                .replace('Ğ', 'g').replace('ğ', 'g')\n"
        "                .replace('Ü', 'u').replace('ü', 'u')\n"
        "                .replace('Ö', 'o').replace('ö', 'o')\n"
        "                .replace('Ç', 'c').replace('ç', 'c'))\n\n"
    )


def patch_portal_routes(root: Path) -> dict:
    path = root / "app" / "portal" / "routes.py"
    text = read_text(path)
    original = text

    helper_marker = "# BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_HELPER"
    if helper_marker not in text:
        helper = (
            "\n\n"
            f"{helper_marker}\n"
            "def _portal_press_news_admin_only(user) -> bool:\n"
            "    if not user or not getattr(user, 'is_authenticated', False):\n"
            "        return False\n"
            "    if bool(getattr(user, 'is_admin', False)) or bool(getattr(user, 'is_superuser', False)):\n"
            "        return True\n"
            "    role = str(getattr(user, 'role', '') or '').strip().lower().replace('-', '_').replace(' ', '_')\n"
            "    role = (role.replace('İ', 'i').replace('I', 'i').replace('ı', 'i')\n"
            "                 .replace('Ş', 's').replace('ş', 's')\n"
            "                 .replace('Ğ', 'g').replace('ğ', 'g')\n"
            "                 .replace('Ü', 'u').replace('ü', 'u')\n"
            "                 .replace('Ö', 'o').replace('ö', 'o')\n"
            "                 .replace('Ç', 'c').replace('ç', 'c'))\n"
            "    return role in {'admin', 'super_admin', 'system_admin', 'sistem_yoneticisi', 'administrator'}\n"
        )
        # Insert helper immediately before press-news route block when possible.
        anchor = "# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_BEGIN"
        if anchor in text:
            text = text.replace(anchor, helper + "\n" + anchor, 1)
        else:
            text += helper

    begin = "# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_BEGIN"
    end = "# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_END"
    if begin in text and end in text:
        pre, rest = text.split(begin, 1)
        block, post = rest.split(end, 1)
        block = re.sub(r'@menu_key_required\(["\']([^"\']+)["\']\)', '@menu_key_required("portal_press_news")', block)
        block = block.replace("if not can_manage_portal(current_user):", "if not _portal_press_news_admin_only(current_user):")
        text = pre + begin + block + end + post
    else:
        # Fallback: only patch decorated press-news functions.
        names = [
            "portal_press_news_review",
            "portal_press_news_scan_now",
            "portal_press_news_publish",
            "portal_press_news_archive",
        ]
        for name in names:
            pattern = rf'(@main_bp\.(?:get|post)\([^\n]+\)\s*\n@login_required\s*\n)@menu_key_required\(["\'][^"\']+["\']\)(\s*\ndef {name}\()'
            text = re.sub(pattern, rf'\1@menu_key_required("portal_press_news")\2', text)
        text = text.replace("if not can_manage_portal(current_user):", "if not _portal_press_news_admin_only(current_user):")

    changed = text != original
    if changed:
        write_text(path, text)
    return {"file": str(path.relative_to(root)), "changed": changed, "markers": [helper_marker]}


def replace_roles_list_in_item_block(item_block: str) -> str:
    admin_list = '["admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"]'
    # Restrict keys used by both menu registry and settings role-matrix helpers.
    item_block = re.sub(r'"roles"\s*:\s*\[[^\]]*\]', f'"roles": {admin_list}', item_block, flags=re.S)
    item_block = re.sub(r'"required_roles"\s*:\s*\[[^\]]*\]', f'"required_roles": {admin_list}', item_block, flags=re.S)
    # For static gate helpers that only understand required_roles.
    if '"required_roles"' not in item_block:
        item_block = item_block.rstrip()
        if item_block.endswith("}"):
            item_block = item_block[:-1].rstrip()
            if not item_block.endswith(","):
                item_block += ","
            item_block += f'\n                "required_roles": {admin_list},\n            }}'
    return item_block


def patch_menu_registry_sections(root: Path) -> dict:
    path = root / "app" / "menu_registry_data_sections.py"
    text = read_text(path)
    original = text

    # Locate the dictionary containing key portal_press_news and restrict to admin roles.
    m = re.search(r'\{\s*"key"\s*:\s*"portal_press_news"(?P<body>.*?)\n\s*\}', text, flags=re.S)
    if m:
        start, end = m.span()
        text = text[:start] + replace_roles_list_in_item_block(text[start:end]) + text[end:]

    changed = text != original
    if changed:
        write_text(path, text)
    return {"file": str(path.relative_to(root)), "changed": changed}


def patch_account_helpers(root: Path) -> dict:
    path = root / "app" / "main_handlers" / "account_communication_helpers.py"
    if not path.exists():
        return {"file": str(path.relative_to(root)), "changed": False, "missing": True}
    text = read_text(path)
    original = text
    # Restrict the role matrix metadata row for portal_press_news.
    pattern = r'\{[^{}]*"key"\s*:\s*"portal_press_news"[^{}]*\}'
    def repl(match: re.Match) -> str:
        return replace_roles_list_in_item_block(match.group(0))
    text = re.sub(pattern, repl, text, flags=re.S)
    changed = text != original
    if changed:
        write_text(path, text)
    return {"file": str(path.relative_to(root)), "changed": changed}


def patch_menu_registry_performance(root: Path) -> dict:
    path = root / "app" / "menu_registry_data_performance.py"
    text = read_text(path)
    original = text
    marker = "# BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_ROLE_DEFAULTS"
    if marker not in text:
        addition = f'''
{marker}
try:
    for _role in ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"]:
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("portal_press_news")
    for _role in ["baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"]:
        _target = ROLE_MENU_DEFAULTS.setdefault(_role, set())
        try:
            _target.discard("portal_press_news")
        except AttributeError:
            while "portal_press_news" in _target:
                _target.remove("portal_press_news")
except Exception:
    pass
# BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_ROLE_DEFAULTS_END
'''
        text += addition
    changed = text != original
    if changed:
        write_text(path, text)
    return {"file": str(path.relative_to(root)), "changed": changed}


def patch_effective_menu(root: Path) -> dict:
    path = root / "app" / "services" / "settings" / "effective_menu.py"
    text = read_text(path)
    original = text

    marker = "# BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_EFFECTIVE"
    if marker not in text:
        helper = f'''
{marker}
def _bys360_press_news_role(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return (text.replace("İ", "i").replace("I", "i").replace("ı", "i")
                .replace("Ş", "s").replace("ş", "s")
                .replace("Ğ", "g").replace("ğ", "g")
                .replace("Ü", "u").replace("ü", "u")
                .replace("Ö", "o").replace("ö", "o")
                .replace("Ç", "c").replace("ç", "c"))


def _apply_bys360_press_news_admin_only_policy(visibility: dict[str, bool], user: Any) -> dict[str, bool]:
    """Basında Tarihi Alan runtime son kararı: yalnız admin/sistem yöneticisi."""
    if "portal_press_news" not in visibility:
        return visibility
    is_admin_like = bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False))
    role = _bys360_press_news_role(getattr(user, "role", ""))
    visibility["portal_press_news"] = bool(is_admin_like or role in {{"admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"}})
    return visibility
# BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_EFFECTIVE_END
'''
        # Put helper before build_menu_visibility_map.
        text = text.replace("def build_menu_visibility_map(\n", helper + "\ndef build_menu_visibility_map(\n", 1)

    call = "    visibility = _apply_bys360_press_news_admin_only_policy(visibility, user)  # BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_APPLIED\n"
    if "BYS360_PORTAL_PRESS_NEWS_ADMIN_ROUTE_AUTHORITY_HOTFIX_V3_APPLIED" not in text:
        # Insert just before final return visibility in build_menu_visibility_map.
        idx = text.find("# BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU_BEGIN")
        if idx != -1:
            before = text[:idx]
            after = text[idx:]
            last_return = before.rfind("    return visibility")
            if last_return != -1:
                before = before[:last_return] + call + before[last_return:]
                text = before + after
        else:
            text = re.sub(r'(\n\s*return visibility\n)', "\n" + call + r'\1', text, count=1)

    # Ensure runtime authority includes key for visible/closed tracking in settings UI.
    if '"portal_press_news"' not in text[text.find("ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"): text.find("def _get_role_matrix_closed_keys_for_role")]:
        text = text.replace('    "feedback_admin",\n', '    "feedback_admin",\n    "portal_press_news",\n', 1)

    changed = text != original
    if changed:
        write_text(path, text)
    return {"file": str(path.relative_to(root)), "changed": changed}


def patch_all(root: Path) -> dict:
    return {
        "package": PACKAGE,
        "project_root": str(root),
        "patches": [
            patch_portal_routes(root),
            patch_menu_registry_sections(root),
            patch_account_helpers(root),
            patch_menu_registry_performance(root),
            patch_effective_menu(root),
        ],
    }


def repair_db(root: Path) -> dict:
    # Import project app after setting cwd/sys.path.
    os.chdir(root)
    sys.path.insert(0, str(root))
    from app import create_app
    from app.extensions import db
    from app.models import RoleMenuDefault, User, UserMenuPermission, UnitMenuProfile

    app = create_app()
    result = {
        "role_rows_upserted": 0,
        "admin_user_overrides_fixed": 0,
        "non_admin_user_overrides_closed": 0,
        "unit_overrides_removed": 0,
        "admin_user_count": 0,
    }
    with app.app_context():
        def norm(value):
            return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

        all_roles = sorted(ADMIN_ROLES | NON_ADMIN_ROLES)
        for role in all_roles:
            visible = role in ADMIN_ROLES
            row = RoleMenuDefault.query.filter_by(role_name=role, menu_key=PRESS_KEY).first()
            if row is None:
                row = RoleMenuDefault(role_name=role, menu_key=PRESS_KEY)
                db.session.add(row)
            row.is_visible = bool(visible)
            row.source_type = "hotfix_v3_admin_only"
            row.note = "Basında Tarihi Alan yalnız admin/sistem yöneticisi görünür."
            result["role_rows_upserted"] += 1

        # Unit profile must not close admin after role matrix opened this menu.
        unit_rows = UnitMenuProfile.query.filter_by(menu_key=PRESS_KEY).all()
        for row in unit_rows:
            db.session.delete(row)
            result["unit_overrides_removed"] += 1

        users = User.query.all()
        for user in users:
            role = norm(getattr(user, "role", ""))
            is_admin_like = bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)) or role in ADMIN_ROLES
            row = UserMenuPermission.query.filter_by(user_id=user.id, menu_key=PRESS_KEY).first()
            if is_admin_like:
                result["admin_user_count"] += 1
                if row is None:
                    row = UserMenuPermission(user_id=user.id, menu_key=PRESS_KEY)
                    db.session.add(row)
                row.is_visible = True
                row.source_type = "hotfix_v3_admin_allow"
                result["admin_user_overrides_fixed"] += 1
            else:
                if row is not None:
                    row.is_visible = False
                    row.source_type = "hotfix_v3_admin_only_close"
                    result["non_admin_user_overrides_closed"] += 1
        db.session.commit()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="all", choices=["all", "patch", "db"])
    parser.add_argument("--repair-db", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not (root / "app").exists():
        print(json.dumps({"ok": False, "error": "app klasoru bulunamadi", "project_root": str(root)}, ensure_ascii=False))
        return 2

    output: dict = {"ok": True, "package": PACKAGE, "project_root": str(root)}
    if args.mode in {"all", "patch"}:
        output["patch"] = patch_all(root)
    if args.repair_db or args.mode == "db":
        output["db"] = repair_db(root)

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
