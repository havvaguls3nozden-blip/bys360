# -*- coding: utf-8 -*-
"""BYS360 Basında Tarihi Alan Admin Unlock + Role Matrix Hotfix V2.

Amaç:
- Basında Tarihi Alan sekmesini kesin olarak yalnızca admin/admin-benzeri teknik rollerde göstermek.
- Adminin erişimini canlı Rol Matrisi / kişi override kayıtlarındaki hatalı false değerlerine taktırmamak.
- Ayarlar > Rol Matrisi satırını korumak/güncellemek.
- DB onarımı ile admin rol ve admin kullanıcı override kayıtlarını true, non-admin kayıtlarını false yapmak.

Not: Bu paket V1 sonrası da, V1 uygulanmamış kaynak üzerinde de güvenli/idempotent çalışacak şekilde yazıldı.
"""
from __future__ import annotations

import argparse
import compileall
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2"
VERSION = "V2"
ADMIN_ROLES = {"admin", "super_admin", "system_admin", "sistem_yoneticisi"}
KNOWN_ROLES = [
    "admin", "super_admin", "system_admin", "sistem_yoneticisi",
    "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir",
    "koordinator", "birim_sorumlusu", "personel", "rolsuz",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def backup_file(project_root: Path, path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    rel = path.relative_to(project_root)
    dst = backup_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(path, dst)


def replace_once_if_present(text: str, old: str, new: str, label: str, changes: list[str]) -> str:
    if old in text:
        changes.append(label)
        return text.replace(old, new, 1)
    if new in text:
        changes.append(label + " (zaten uygulanmış)")
    return text


def ensure_route_imports(text: str, changes: list[str]) -> str:
    # V1 can_access_menu kullanmış olabilir; V2 görünürlükte bunu kullanmaz.
    patterns = [
        "from app.route_support import can_access_menu, menu_key_required, normalize_role_name, render_access_denied, safe_render, sanitize_free_text",
        "from app.route_support import menu_key_required, normalize_role_name, render_access_denied, safe_render, sanitize_free_text",
        "from app.route_support import menu_key_required, render_access_denied, safe_render, sanitize_free_text",
    ]
    desired = "from app.route_support import menu_key_required, normalize_role_name, render_access_denied, safe_render, sanitize_free_text"
    for p in patterns:
        if p in text:
            if p != desired:
                text = text.replace(p, desired, 1)
                changes.append("portal/routes import normalize_role_name sadeleştirildi")
            else:
                changes.append("portal/routes import zaten uygun")
            return text
    raise RuntimeError("portal/routes route_support import satırı bulunamadı")


def ensure_admin_helper(text: str, changes: list[str]) -> str:
    helper_v2 = '''\n\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN\n_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLES = {"admin", "super_admin", "system_admin", "sistem_yoneticisi"}\n\ndef _portal_press_news_admin_only_allowed(user) -> bool:\n    if not user or not getattr(user, "is_authenticated", False):\n        return False\n    return normalize_role_name(getattr(user, "role", "")) in _PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLES\n\ndef _portal_press_news_visible_for_user(user) -> bool:\n    # Admin sekmesi stale/yanlış kişi override kayıtlarına takılmasın.\n    return _portal_press_news_admin_only_allowed(user)\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_END\n'''

    # V1 helper varsa tamamını V2 helper ile değiştir.
    v1_re = re.compile(
        r"\n\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_BEGIN.*?# BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_END\n",
        flags=re.DOTALL,
    )
    text2, count = v1_re.subn(helper_v2, text, count=1)
    if count:
        changes.append("V1 press-news helper V2 admin-unlock helper ile değiştirildi")
        return text2

    if "BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN" in text:
        changes.append("V2 press-news helper zaten var")
        return text

    marker = "\ndef _slugify(value: str) -> str:\n"
    if marker not in text:
        raise RuntimeError("_slugify marker bulunamadı; press-news helper eklenemedi")
    changes.append("V2 press-news admin-unlock helper eklendi")
    return text.replace(marker, helper_v2 + marker, 1)


def ensure_common_context(text: str, changes: list[str]) -> str:
    # V1 eklendiyse bırakılır; helper davranışı V2'de admin-only oldu.
    line = '        "portal_press_news_visible": _portal_press_news_visible_for_user(current_user),\n'
    if line in text:
        changes.append("portal_common_context press_news_visible zaten var")
        return text
    anchor = '        "portal_can_manage": can_manage_portal(current_user),\n'
    if anchor not in text:
        raise RuntimeError("portal_common_context portal_can_manage anchor bulunamadı")
    changes.append("portal_common_context press_news_visible eklendi")
    return text.replace(anchor, anchor + line, 1)


def patch_press_news_route_block(text: str, changes: list[str]) -> str:
    begin = text.find("# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_BEGIN")
    end = text.find("# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_END")
    if begin == -1 or end == -1 or end <= begin:
        raise RuntimeError("Basında Tarihi Alan route bloğu bulunamadı")
    block = text[begin:end]
    original = block

    # Admin yanlışlıkla menü map/rol matrisi false'a düştüyse route engellenmesin.
    block = re.sub(r"\n@menu_key_required\(\"portal_(?:feed|press_news)\"\)", "", block)
    block = block.replace("if not can_manage_portal(current_user):", "if not _portal_press_news_admin_only_allowed(current_user):")

    if block != original:
        changes.append("press-news route bloğu admin-only iç kontrol + decorator unlock yapıldı")
    else:
        changes.append("press-news route bloğu zaten V2 uyumlu")
    return text[:begin] + block + text[end:]


def patch_portal_routes(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "portal" / "routes.py"
    backup_file(project_root, path, backup_root)
    text = read_text(path)
    text = ensure_route_imports(text, changes)
    text = ensure_admin_helper(text, changes)
    text = ensure_common_context(text, changes)
    text = patch_press_news_route_block(text, changes)
    write_text(path, text)


def patch_base_template(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "templates" / "base.html"
    backup_file(project_root, path, backup_root)
    text = read_text(path)

    v1 = """{% set portal_press_news_admin_role = current_user.is_authenticated and role_name in ['admin','super_admin','system_admin','sistem_yoneticisi'] %}\n{% set portal_press_news_visible = portal_press_news_admin_role and menu_map.get('portal_press_news', portal_press_news_admin_role) %}"""
    v2 = """{% set portal_press_news_admin_role = current_user.is_authenticated and role_name in ['admin','super_admin','system_admin','sistem_yoneticisi'] %}\n{% set portal_press_news_visible = portal_press_news_admin_role %}"""
    legacy = """{% set portal_press_news_visible = menu_map.get('portal_press_news', portal_feed_visible) or portal_feed_visible or current_path.startswith('/portal/press-news') %}"""

    if v1 in text:
        text = text.replace(v1, v2, 1)
        changes.append("base.html V1 matrix false bağı kaldırıldı; admin görünürlük kesinleşti")
    elif legacy in text:
        text = text.replace(legacy, v2, 1)
        changes.append("base.html legacy görünürlük admin-only kesin görünürlüğe alındı")
    elif v2 in text:
        changes.append("base.html V2 görünürlük zaten uygun")
    else:
        raise RuntimeError("base.html portal_press_news görünürlük satırı bulunamadı")
    write_text(path, text)


def patch_portal_tabs(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "templates" / "portal" / "_tabs.html"
    backup_file(project_root, path, backup_root)
    text = read_text(path)
    old = "{% set _portal_press_news_visible = portal_press_news_visible|default(true) %}"
    new = "{% set _portal_press_news_visible = portal_press_news_visible|default(false) %}"
    text = replace_once_if_present(text, old, new, "portal/_tabs default false yapıldı", changes)
    if new not in text:
        raise RuntimeError("portal/_tabs press_news default satırı bulunamadı")
    write_text(path, text)


def patch_menu_registry_sections(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "menu_registry_data_sections.py"
    if not path.exists():
        changes.append("menu_registry_data_sections yok; atlandı")
        return
    backup_file(project_root, path, backup_root)
    text = read_text(path)
    pattern = re.compile(r'(\{\s*"key":\s*"portal_press_news",.*?"roles":\s*)\[[^\]]*\](\s*,\s*\})', flags=re.DOTALL)
    text2, count = pattern.subn(r'\1["admin"]\2', text, count=1)
    if count:
        text = text2
        changes.append("menu_registry_data_sections portal_press_news roles admin-only")
    elif '"key": "portal_press_news"' in text and '"roles": ["admin"]' in text:
        changes.append("menu_registry_data_sections zaten admin-only")
    else:
        raise RuntimeError("menu_registry_data_sections portal_press_news roles güncellenemedi")
    write_text(path, text)


def patch_account_helpers(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "main_handlers" / "account_communication_helpers.py"
    if not path.exists():
        changes.append("account_communication_helpers yok; atlandı")
        return
    backup_file(project_root, path, backup_root)
    text = read_text(path)
    # portal_press_news kaydında required_roles değerini yalnız admin yap.
    line_re = re.compile(r'(\{[^\n]*"key":\s*"portal_press_news"[^\n]*"required_roles":\s*)\[[^\]]*\]([^\n]*\},?)')
    text2, count = line_re.subn(r'\1["admin"]\2', text, count=1)
    if count:
        text = text2
        changes.append("account_communication_helpers rol matrisi required_roles admin-only")
    elif '"key": "portal_press_news"' in text and '"required_roles": ["admin"]' in text:
        changes.append("account_communication_helpers zaten admin-only")
    else:
        raise RuntimeError("account_communication_helpers portal_press_news satırı güncellenemedi")
    write_text(path, text)


def patch_role_defaults(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "menu_registry_data_performance.py"
    if not path.exists():
        changes.append("menu_registry_data_performance yok; atlandı")
        return
    backup_file(project_root, path, backup_root)
    text = read_text(path)
    marker_begin_v2 = "# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN"
    marker_begin_v1 = "# BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_BEGIN"
    block_v2 = '''\n\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN\n# Basında Tarihi Alan varsayılan menü yetkisi yalnızca admin/admin-benzeri teknik roldedir.\ntry:\n    _bys360_press_news_admin_roles_v2 = {"admin", "super_admin", "system_admin", "sistem_yoneticisi"}\n    for _role, _keys in list(ROLE_MENU_DEFAULTS.items()):\n        try:\n            if _role in _bys360_press_news_admin_roles_v2:\n                _keys.add("portal_press_news")\n            else:\n                _keys.discard("portal_press_news")\n        except AttributeError:\n            if _role in _bys360_press_news_admin_roles_v2:\n                if "portal_press_news" not in _keys:\n                    _keys.append("portal_press_news")\n            else:\n                while "portal_press_news" in _keys:\n                    _keys.remove("portal_press_news")\nexcept Exception:\n    pass\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_END\n'''
    if marker_begin_v2 in text:
        changes.append("ROLE_MENU_DEFAULTS V2 override zaten var")
    elif marker_begin_v1 in text:
        text = re.sub(
            r"\n\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_BEGIN.*?# BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_END\n",
            block_v2,
            text,
            count=1,
            flags=re.DOTALL,
        )
        changes.append("ROLE_MENU_DEFAULTS V1 override V2 ile değiştirildi")
    else:
        text = text.rstrip() + block_v2 + "\n"
        changes.append("ROLE_MENU_DEFAULTS V2 admin-only override eklendi")
    write_text(path, text)


def patch_role_matrix_service(project_root: Path, backup_root: Path, changes: list[str]) -> None:
    path = project_root / "app" / "services" / "role_matrix_ui_service.py"
    if not path.exists():
        changes.append("role_matrix_ui_service yok; atlandı")
        return
    backup_file(project_root, path, backup_root)
    text = read_text(path)
    if "BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN" in text:
        changes.append("role_matrix_ui_service V2 satırı zaten var")
        write_text(path, text)
        return

    # V1 bloğu varsa marka adını V2'ye çevirip bırakabiliriz; MatrixRow içeriği uygundur.
    if "BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_BEGIN" in text:
        text = text.replace("BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_BEGIN", "BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN")
        text = text.replace("BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROLE_MATRIX_HOTFIX_V1_END", "BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_END")
        changes.append("role_matrix_ui_service V1 marker V2 marker'a çevrildi")
        write_text(path, text)
        return

    block = '''\n\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN\n# Ayarlar > Rol Matrisi ekranında Basında Tarihi Alan satırı görünür; varsayılan politika admin-only.\ntry:\n    _BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW = MatrixRow(\n        "portal_press_news",\n        "Basında Tarihi Alan",\n        "portal_press_news",\n        "fa-regular fa-newspaper",\n        ADMIN_ONLY,\n        "Basında Tarihi Alan haber adayları ve yayın/onay ekranı. Varsayılan olarak yalnızca Admin rolüne açıktır.",\n    )\n    _patched_groups = []\n    _portal_group_found = False\n    for _group in GROUPS:\n        if getattr(_group, "key", "") == "portal":\n            _portal_group_found = True\n            _rows = []\n            _seen = set()\n            for _row in getattr(_group, "rows", ()):\n                if getattr(_row, "key", "") == "portal_press_news" or getattr(_row, "subtitle", "") == "portal_press_news":\n                    if "portal_press_news" not in _seen:\n                        _rows.append(_BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW)\n                        _seen.add("portal_press_news")\n                else:\n                    _rows.append(_row)\n                    _seen.add(getattr(_row, "key", ""))\n            if "portal_press_news" not in _seen:\n                _insert_at = len(_rows)\n                for _idx, _row in enumerate(_rows):\n                    if getattr(_row, "key", "") == "portal_moderation":\n                        _insert_at = _idx\n                        break\n                _rows.insert(_insert_at, _BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW)\n            _group = MatrixGroup(\n                key=_group.key,\n                title=_group.title,\n                subtitle="Yayın akışı, personel duvarları, paylaşım, grup ve Basında Tarihi Alan yetkileri.",\n                icon=_group.icon,\n                badges=tuple(dict.fromkeys(tuple(_group.badges) + ("Basında Tarihi Alan: Admin",))),\n                rows=tuple(_rows),\n            )\n        _patched_groups.append(_group)\n    if not _portal_group_found:\n        _patched_groups.append(MatrixGroup(\n            key="portal",\n            title="Kurumsal Portal Rol Matrisi",\n            subtitle="Kurumsal Portal görünürlük ve yetki matrisi.",\n            icon="fa-solid fa-stream",\n            badges=("Basında Tarihi Alan: Admin",),\n            rows=(_BYS360_PORTAL_PRESS_NEWS_ADMIN_ONLY_ROW,),\n        ))\n    GROUPS = tuple(_patched_groups)\nexcept Exception:\n    __import__("logging").getLogger(__name__).exception("Basında Tarihi Alan admin-only rol matrisi satırı uygulanamadı")\n# BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_END\n'''
    text = text.rstrip() + block + "\n"
    changes.append("role_matrix_ui_service V2 portal_press_news satırı eklendi")
    write_text(path, text)


def patch_files(project_root: Path) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / "backups" / f"{PACKAGE}_{stamp}"
    changes: list[str] = []
    patch_portal_routes(project_root, backup_root, changes)
    patch_base_template(project_root, backup_root, changes)
    patch_portal_tabs(project_root, backup_root, changes)
    patch_menu_registry_sections(project_root, backup_root, changes)
    patch_account_helpers(project_root, backup_root, changes)
    patch_role_defaults(project_root, backup_root, changes)
    patch_role_matrix_service(project_root, backup_root, changes)
    return {"changed": changes, "backup_root": str(backup_root)}


def repair_db(project_root: Path) -> dict:
    """DB'de Basında Tarihi Alan menü yetkisini admin true / non-admin false olacak şekilde düzeltir."""
    sys.path.insert(0, str(project_root))
    from app import create_app  # type: ignore
    from app.extensions import db  # type: ignore
    from app.models import RoleMenuDefault, User, UserMenuPermission  # type: ignore

    app = create_app()
    changed_role_defaults = 0
    changed_user_overrides = 0
    with app.app_context():
        existing_defaults = {
            (str(row.role_name or "").strip().lower(), str(row.menu_key or "").strip()): row
            for row in RoleMenuDefault.query.filter_by(menu_key="portal_press_news").all()
        }
        for role in KNOWN_ROLES:
            desired = role in ADMIN_ROLES
            key = (role, "portal_press_news")
            row = existing_defaults.get(key)
            if row is None:
                row = RoleMenuDefault(role_name=role, menu_key="portal_press_news", is_visible=desired)
                db.session.add(row)
                changed_role_defaults += 1
            elif bool(row.is_visible) != desired:
                row.is_visible = desired
                changed_role_defaults += 1

        users = User.query.all()
        for user in users:
            user_id = getattr(user, "id", None)
            if user_id is None:
                continue
            role = str(getattr(user, "role", "") or "").strip().lower()
            desired = role in ADMIN_ROLES
            row = UserMenuPermission.query.filter_by(user_id=int(user_id), menu_key="portal_press_news").first()
            if row is None:
                # Adminlerde açık kaydı garanti et; non-adminlerde gerekmedikçe satır üretme.
                if desired:
                    row = UserMenuPermission(user_id=int(user_id), menu_key="portal_press_news", is_visible=True)
                    db.session.add(row)
                    changed_user_overrides += 1
            elif bool(row.is_visible) != desired:
                row.is_visible = desired
                changed_user_overrides += 1
        db.session.commit()
    return {"role_defaults_changed": changed_role_defaults, "user_overrides_changed": changed_user_overrides}


def run_compile(project_root: Path) -> bool:
    targets = [project_root / p for p in ("app", "config.py", "run.py", "run_server.py", "wsgi.py", "scripts") if (project_root / p).exists()]
    ok = True
    for target in targets:
        if target.is_dir():
            ok = compileall.compile_dir(str(target), quiet=1) and ok
        else:
            ok = compileall.compile_file(str(target), quiet=1) and ok
    return ok


def check_files(project_root: Path) -> dict:
    routes = read_text(project_root / "app/portal/routes.py")
    base = read_text(project_root / "app/templates/base.html")
    tabs = read_text(project_root / "app/templates/portal/_tabs.html")
    begin = routes.find("# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_BEGIN")
    end = routes.find("# BYS360_PORTAL_EXPERIENCE_V3A_PRESS_NEWS_ROUTES_END")
    block = routes[begin:end] if begin != -1 and end != -1 else ""
    return {
        "routes_has_v2_helper": "BYS360_PORTAL_PRESS_NEWS_ADMIN_UNLOCK_ROLE_MATRIX_HOTFIX_V2_BEGIN" in routes,
        "routes_press_news_decorator_removed": "@menu_key_required" not in block,
        "routes_press_news_admin_check": "_portal_press_news_admin_only_allowed(current_user)" in block,
        "context_sets_press_news_visible": '"portal_press_news_visible": _portal_press_news_visible_for_user(current_user)' in routes,
        "base_admin_visible_without_menu_map": "{% set portal_press_news_visible = portal_press_news_admin_role %}" in base,
        "tabs_default_false": "portal_press_news_visible|default(false)" in tabs,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=["all", "check", "files"], default="all")
    parser.add_argument("--repair-db", action="store_true")
    parser.add_argument("--run-compile", action="store_true")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    result: dict = {"package": PACKAGE, "version": VERSION, "project_root": str(project_root), "ok": False}
    try:
        if args.mode in {"all", "files"}:
            result["files"] = patch_files(project_root)
        if args.repair_db:
            result["db"] = repair_db(project_root)
        result["checks"] = check_files(project_root)
        if args.run_compile:
            result["compile_ok"] = run_compile(project_root)
            if not result["compile_ok"]:
                raise RuntimeError("compileall başarısız oldu")
        result["ok"] = True
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        result["error"] = str(exc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
