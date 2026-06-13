# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile, subprocess, sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR"
VERSION = "V3A1"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def payload(root: Path, rel: str) -> str:
    return (root / "_bys360_overlay_payload" / "portal_v3a1" / rel).read_text(encoding="utf-8")


def write_file(root: Path, rel: str, content: str) -> bool:
    path = root / rel
    old = read_text(path) if path.exists() else None
    if old == content:
        return False
    write_text(path, content)
    return True


def patch_base_template(root: Path) -> bool:
    path = root / "app/templates/base.html"
    if not path.exists():
        return False
    text = read_text(path)
    old = text

    if "portal_press_news_visible" not in text and "{% set portal_moderation_visible" in text:
        text = text.replace(
            "{% set portal_moderation_visible = menu_map.get('portal_moderation', can_top) %}",
            "{% set portal_moderation_visible = menu_map.get('portal_moderation', can_top) %}\n"
            "{% set portal_press_news_visible = menu_map.get('portal_press_news', portal_moderation_visible) and portal_moderation_visible %}",
            1,
        )

    before = "portal_feed_visible or portal_profiles_visible or portal_groups_visible or portal_moderation_visible or current_path.startswith('/portal')"
    after = "portal_feed_visible or portal_profiles_visible or portal_groups_visible or portal_press_news_visible or portal_moderation_visible or current_path.startswith('/portal')"
    if before in text and "portal_press_news_visible" in text:
        text = text.replace(before, after, 1)

    if "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR" not in text:
        nav_line = '''                            {# BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR #}\n                            {% if portal_press_news_visible %}{{ nav_item(safe_url_for('main.portal_press_news_review', fallback='/portal/press-news'), 'fa-radio', 'Basında Tarihi Alan', current_ep == 'main.portal_press_news_review' or current_path.startswith('/portal/press-news'), none, 'data-nav-key="portal_press_news" data-menu-key="portal_press_news" data-screen-key="corporate_portal_press_news"') }}{% endif %}\n'''
        anchor = "                            {% if portal_moderation_visible %}{{ nav_item(safe_url_for('main.portal_moderation', fallback='/portal/moderation')"
        if anchor in text:
            text = text.replace(anchor, nav_line + anchor, 1)
        else:
            groups_line = "                            {% if portal_groups_visible %}{{ nav_item(safe_url_for('main.portal_groups', fallback='/portal/groups'), 'fa-user-group', 'Portal Grupları'"
            idx = text.find(groups_line)
            if idx >= 0:
                end = text.find("\n", idx)
                text = text[:end+1] + nav_line + text[end+1:]

    if text != old:
        write_text(path, text)
        return True
    return False


def patch_portal_tabs(root: Path) -> bool:
    path = root / "app/templates/portal/_tabs.html"
    if not path.exists():
        return False
    text = read_text(path)
    old = text
    if "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_TAB" not in text:
        tab = '''  {# BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_TAB #}\n  <a class="portal-tab {{ 'active' if active_portal_tab == 'press_news' else '' }}" href="{{ safe_url_for('main.portal_press_news_review', fallback='/portal/press-news') }}"><i class="fa-regular fa-newspaper"></i> Basında Tarihi Alan</a>\n'''
        anchor = "  <a class=\"portal-tab {{ 'active' if active_portal_tab == 'moderation' else '' }}\" href=\"{{ safe_url_for('main.portal_moderation', fallback='/portal/moderation') }}\"><i class=\"fa-solid fa-shield-halved\"></i> Portal Yönetimi</a>"
        if anchor in text:
            text = text.replace(anchor, tab + anchor, 1)
        elif "{% if portal_can_manage %}" in text:
            text = text.replace("{% if portal_can_manage %}\n", "{% if portal_can_manage %}\n" + tab, 1)
    if text != old:
        write_text(path, text)
        return True
    return False


def patch_menu_registry_sections(root: Path) -> bool:
    path = root / "app/menu_registry_data_sections.py"
    if not path.exists():
        return False
    text = read_text(path)
    old = text
    if '"key": "portal_press_news"' not in text:
        item = '''            {
                "key": "portal_press_news",
                "label": "Basında Tarihi Alan",
                "icon": "fa-regular fa-newspaper",
                "endpoint": "main.portal_press_news_review",
                "active_endpoints": ["main.portal_press_news_review"],
                "active_path_prefixes": ["/portal/press-news"],
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"],
            },
'''
        anchor = '            {\n                "key": "portal_moderation"'
        if anchor in text:
            text = text.replace(anchor, item + anchor, 1)
    if text != old:
        write_text(path, text)
        return True
    return False


def patch_role_defaults(root: Path) -> bool:
    path = root / "app/menu_registry_data_performance.py"
    if not path.exists():
        return False
    text = read_text(path)
    old = text
    target = '_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MODERATORS = set(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGERS) | {"portal_moderation"}'
    if target in text:
        text = text.replace(target, '_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MODERATORS = set(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGERS) | {"portal_moderation", "portal_press_news"}', 1)
    if 'BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_ROLE_DEFAULTS' not in text:
        text += '''
# BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"):
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("portal_press_news")
except Exception:
    pass
# BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_ROLE_DEFAULTS_END
'''
    if text != old:
        write_text(path, text)
        return True
    return False


def patch_role_matrix(root: Path) -> bool:
    path = root / "app/main_handlers/account_communication_helpers.py"
    if not path.exists():
        return False
    text = read_text(path)
    old = text
    if '"key": "portal_press_news"' not in text and "PORTAL_ROLE_MATRIX_V2_12_ITEMS" in text:
        item = '    {"key": "portal_press_news", "label": "Basında Tarihi Alan Haber Onayı", "icon": "fa-regular fa-newspaper", "settings_key": "portal_press_news", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"]},\n'
        anchor = '    {"key": "portal_moderation", "label": "Portal Yönetimi / Moderasyon"'
        if anchor in text:
            text = text.replace(anchor, item + anchor, 1)
    if text != old:
        write_text(path, text)
        return True
    return False


def patch(root: Path) -> dict:
    changed = []
    if write_file(root, "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py", payload(root, "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py")):
        changed.append("scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py")
    if patch_base_template(root):
        changed.append("app/templates/base.html")
    if patch_portal_tabs(root):
        changed.append("app/templates/portal/_tabs.html")
    if patch_menu_registry_sections(root):
        changed.append("app/menu_registry_data_sections.py")
    if patch_role_defaults(root):
        changed.append("app/menu_registry_data_performance.py")
    if patch_role_matrix(root):
        changed.append("app/main_handlers/account_communication_helpers.py")
    return {"ok": True, "changed": changed}


def compile_files(root: Path) -> dict:
    errors = []
    for rel in [
        "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py",
        "scripts/portal/repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
        "app/menu_registry_data_sections.py",
        "app/menu_registry_data_performance.py",
        "app/main_handlers/account_communication_helpers.py",
    ]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                errors.append({"file": rel, "error": str(exc)})
    return {"ok": not errors, "errors": errors}


def run_check(root: Path) -> dict:
    script = root / "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py"
    proc = subprocess.run([sys.executable, str(script), "--project-root", str(root)], cwd=str(root), text=True, capture_output=True)
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def write_report(root: Path, result: dict) -> dict:
    report_dir = root / "reports" / "portal"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR_REPORT.json"
    md_path = report_dir / "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR_REPORT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text("\n".join([
        "# BYS360 Portal Deneyimi V3A1 Raporu",
        "",
        f"Paket: {PACKAGE}",
        f"Sürüm: {VERSION}",
        f"Durum: {'Başarılı' if result.get('ok') else 'Kontrol gerekli'}",
        "",
        "## Yapılan düzenleme",
        "- Basında Tarihi Alan ekranı sol şeritte Kurumsal Portal menüsü altına eklendi.",
        "- Portal iç sekmelerine de Basında Tarihi Alan bağlantısı eklendi.",
        "- Menü görünürlüğü portal yönetimi/üst yetki kapsamına bağlandı.",
        "- Rol matrisi ve statik menü varsayılanlarına portal_press_news anahtarı eklendi.",
        "- Veritabanına dokunulmadı ve yeni tablo açılmadı.",
    ]), encoding="utf-8")
    return {"ok": True, "markdown": str(md_path), "json": str(json_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["patch", "compile", "check", "report", "all"], default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    result = {"package": PACKAGE, "version": VERSION, "project_root": str(root), "mode": args.mode, "generated_at": datetime.now().isoformat(timespec="seconds")}
    ok = True
    if args.mode in {"patch", "all"}:
        result["patch"] = patch(root)
    if args.mode in {"compile", "all"}:
        result["compile"] = compile_files(root); ok = ok and result["compile"]["ok"]
    if args.mode in {"check", "all"}:
        result["check"] = run_check(root); ok = ok and result["check"]["ok"]
    result["ok"] = ok
    if args.mode in {"report", "all"}:
        result["report"] = write_report(root, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if ok:
        print("BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR_OK")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
