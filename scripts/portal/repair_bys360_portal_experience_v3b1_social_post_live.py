# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile, subprocess, sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_POST_LIVE"
VERSION = "V3B1"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def payload(root: Path, rel: str) -> str:
    return (root / "_bys360_overlay_payload" / "portal_v3b1" / rel).read_text(encoding="utf-8")


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
    if "portal_social_import_visible" not in text and "{% set portal_moderation_visible" in text:
        text = text.replace(
            "{% set portal_moderation_visible = menu_map.get('portal_moderation', can_top) %}",
            "{% set portal_moderation_visible = menu_map.get('portal_moderation', can_top) %}\n"
            "{% set portal_social_import_visible = menu_map.get('portal_social_import', portal_moderation_visible) and portal_moderation_visible %}",
            1,
        )
    before = "portal_feed_visible or portal_profiles_visible or portal_groups_visible or portal_moderation_visible or current_path.startswith('/portal')"
    after = "portal_feed_visible or portal_profiles_visible or portal_groups_visible or portal_social_import_visible or portal_moderation_visible or current_path.startswith('/portal')"
    if before in text and "portal_social_import_visible" in text:
        text = text.replace(before, after, 1)
    before2 = "portal_feed_visible or portal_profiles_visible or portal_groups_visible or portal_press_news_visible or portal_moderation_visible or current_path.startswith('/portal')"
    after2 = "portal_feed_visible or portal_profiles_visible or portal_groups_visible or portal_press_news_visible or portal_social_import_visible or portal_moderation_visible or current_path.startswith('/portal')"
    if before2 in text and "portal_social_import_visible" in text:
        text = text.replace(before2, after2, 1)
    if "BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_SIDEBAR" not in text:
        nav_line = """                            {# BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_SIDEBAR #}\n                            {% if portal_social_import_visible %}{{ nav_item(safe_url_for('main.portal_social_import', fallback='/portal/social-import'), 'fa-share-nodes', 'Sosyal Medya Gönderisi Ekle', current_ep == 'main.portal_social_import' or current_path.startswith('/portal/social-import'), none, 'data-nav-key="portal_social_import" data-menu-key="portal_social_import" data-screen-key="corporate_portal_social_import"') }}{% endif %}\n"""
        press_anchor = "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR"
        if press_anchor in text:
            idx = text.find(press_anchor)
            line_end = text.find("\n", idx)
            text = text[:line_end+1] + nav_line + text[line_end+1:]
        else:
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
    if "BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_TAB" not in text:
        tab = """  {# BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_TAB #}\n  <a class="portal-tab {{ 'active' if active_portal_tab == 'social_import' else '' }}" href="{{ safe_url_for('main.portal_social_import', fallback='/portal/social-import') }}"><i class="fa-solid fa-share-nodes"></i> Sosyal Medya Gönderisi</a>\n"""
        anchor = "  <a class=\"portal-tab {{ 'active' if active_portal_tab == 'press_news' else '' }}\""
        if anchor in text:
            text = text.replace(anchor, tab + anchor, 1)
        else:
            anchor2 = "  <a class=\"portal-tab {{ 'active' if active_portal_tab == 'moderation' else '' }}\""
            if anchor2 in text:
                text = text.replace(anchor2, tab + anchor2, 1)
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
    if '"key": "portal_social_import"' not in text:
        item = '''            {
                "key": "portal_social_import",
                "label": "Sosyal Medya Gönderisi Ekle",
                "icon": "fa-solid fa-share-nodes",
                "endpoint": "main.portal_social_import",
                "active_endpoints": ["main.portal_social_import"],
                "active_path_prefixes": ["/portal/social-import"],
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"],
            },
'''
        anchor = '            {\n                "key": "portal_press_news"'
        if anchor in text:
            text = text.replace(anchor, item + anchor, 1)
        else:
            anchor2 = '            {\n                "key": "portal_moderation"'
            if anchor2 in text:
                text = text.replace(anchor2, item + anchor2, 1)
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
    if "BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_ROLE_DEFAULTS" not in text:
        text += '''
# BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"):
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("portal_social_import")
except Exception:
    pass
# BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_ROLE_DEFAULTS_END
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
    if '"key": "portal_social_import"' not in text and "PORTAL_ROLE_MATRIX" in text:
        item = '    {"key": "portal_social_import", "label": "Sosyal Medya Gönderisi Ekleme", "icon": "fa-solid fa-share-nodes", "settings_key": "portal_social_import", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"]},\n'
        anchor = '    {"key": "portal_press_news"'
        if anchor in text:
            text = text.replace(anchor, item + anchor, 1)
        else:
            anchor2 = '    {"key": "portal_moderation", "label": "Portal Yönetimi / Moderasyon"'
            if anchor2 in text:
                text = text.replace(anchor2, item + anchor2, 1)
    if text != old:
        write_text(path, text)
        return True
    return False


def patch_routes(root: Path) -> bool:
    path = root / "app/portal/routes.py"
    if not path.exists():
        return False
    text = read_text(path)
    old = text
    text = text.replace('context.update(page_title="Sosyal Medya Paylaşımı", active_portal_tab="social_import", social_import=social_import_context())', 'context.update(page_title="Sosyal Medya Gönderisi Ekle", active_portal_tab="social_import", social_import=social_import_context())')
    text = text.replace('return safe_render("portal/social_import_v3b.html", "<h3>Sosyal Medya Paylaşımı</h3>", **context)', 'return safe_render("portal/social_import_v3b.html", "<h3>Sosyal Medya Gönderisi Ekle</h3>", **context)')
    if text != old:
        write_text(path, text)
        return True
    return False


def patch_service(root: Path) -> bool:
    path = root / "app/services/portal_social_embed_service.py"
    if not path.exists():
        return False
    text = read_text(path)
    old = text
    text = text.replace("title = 'X hesabından güncel paylaşım'", "title = 'X hesabından paylaşım'")
    text = text.replace("Tarihi Alan Başkanlığı X hesabında yayımlanan güncel paylaşım portal akışına eklenmiştir. Paylaşımı aşağıda görüntüleyebilir veya kaynak bağlantısından açabilirsiniz.", "Tarihi Alan Başkanlığı X hesabında yayımlanan paylaşım portal akışına eklenmiştir. Paylaşımı aşağıda görüntüleyebilir veya kaynak bağlantısından açabilirsiniz.")
    text = text.replace("title = 'Instagram hesabından güncel paylaşım'", "title = 'Instagram hesabından paylaşım'")
    text = text.replace("Tarihi Alan Başkanlığı ve bağlı hesaplara ait güncel Instagram paylaşımı portal akışına eklenmiştir. Paylaşımı aşağıda görüntüleyebilir veya kaynak bağlantısından açabilirsiniz.", "Tarihi Alan Başkanlığı ve bağlı hesaplara ait Instagram paylaşımı portal akışına eklenmiştir. Paylaşımı aşağıda görüntüleyebilir veya kaynak bağlantısından açabilirsiniz.")
    if text != old:
        write_text(path, text)
        return True
    return False


def patch(root: Path) -> dict:
    changed=[]
    if write_file(root, "app/templates/portal/social_import_v3b.html", payload(root, "app/templates/portal/social_import_v3b.html")):
        changed.append("app/templates/portal/social_import_v3b.html")
    if write_file(root, "app/static/css/bys360_portal_experience_v3b1_social_post_live.css", payload(root, "app/static/css/bys360_portal_experience_v3b1_social_post_live.css")):
        changed.append("app/static/css/bys360_portal_experience_v3b1_social_post_live.css")
    if write_file(root, "scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py", payload(root, "scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py")):
        changed.append("scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py")
    if patch_base_template(root): changed.append("app/templates/base.html")
    if patch_portal_tabs(root): changed.append("app/templates/portal/_tabs.html")
    if patch_menu_registry_sections(root): changed.append("app/menu_registry_data_sections.py")
    if patch_role_defaults(root): changed.append("app/menu_registry_data_performance.py")
    if patch_role_matrix(root): changed.append("app/main_handlers/account_communication_helpers.py")
    if patch_routes(root): changed.append("app/portal/routes.py")
    if patch_service(root): changed.append("app/services/portal_social_embed_service.py")
    return {"ok": True, "changed": changed}


def compile_files(root: Path) -> dict:
    errors=[]
    for rel in [
        "scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py",
        "scripts/portal/repair_bys360_portal_experience_v3b1_social_post_live.py",
        "app/menu_registry_data_sections.py",
        "app/menu_registry_data_performance.py",
        "app/main_handlers/account_communication_helpers.py",
        "app/portal/routes.py",
        "app/services/portal_social_embed_service.py",
    ]:
        path=root/rel
        if path.exists() and path.suffix == ".py":
            try: py_compile.compile(str(path), doraise=True)
            except Exception as exc: errors.append({"file": rel, "error": str(exc)})
    return {"ok": not errors, "errors": errors}


def run_check(root: Path) -> dict:
    script=root/"scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py"
    proc=subprocess.run([sys.executable, str(script), "--project-root", str(root)], cwd=str(root), text=True, capture_output=True)
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def write_report(root: Path, result: dict) -> dict:
    report_dir=root/"reports"/"portal"; report_dir.mkdir(parents=True, exist_ok=True)
    jp=report_dir/"BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_POST_LIVE_REPORT.json"
    mp=report_dir/"BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_POST_LIVE_REPORT.md"
    jp.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    mp.write_text("\n".join([
        "# BYS360 Portal V3B1 Sosyal Medya Normal Paylaşım Canlı Ekran Raporu",
        "",
        f"Paket: {PACKAGE}",
        f"Sürüm: {VERSION}",
        f"Durum: {'Başarılı' if result.get('ok') else 'Kontrol gerekli'}",
        "",
        "## Kapsam",
        "- Sosyal medya gönderisi ekleme ekranı canlı kullanım diline taşındı.",
        "- Sol şerit Kurumsal Portal altına Sosyal Medya Gönderisi Ekle bağlantısı eklendi.",
        "- Portal iç sekmelerine Sosyal Medya Gönderisi bağlantısı eklendi.",
        "- X/Instagram bağlantıları ayrı kart değil, normal portal gönderisi olarak yayın akışına düşer.",
        "- Veritabanına dokunulmadı ve yeni tablo açılmadı.",
    ]), encoding="utf-8")
    return {"ok": True, "markdown": str(mp), "json": str(jp)}


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--project-root", required=True); parser.add_argument("--mode", choices=["patch","compile","check","report","all"], default="all"); args=parser.parse_args()
    root=Path(args.project_root).resolve()
    result={"package": PACKAGE, "version": VERSION, "project_root": str(root), "mode": args.mode, "generated_at": datetime.now().isoformat(timespec="seconds")}
    ok=True
    if args.mode in {"patch","all"}: result["patch"] = patch(root)
    if args.mode in {"compile","all"}: result["compile"] = compile_files(root); ok = ok and result["compile"]["ok"]
    if args.mode in {"check","all"}: result["check"] = run_check(root); ok = ok and result["check"]["ok"]
    result["ok"] = ok
    if args.mode in {"report","all"}: result["report"] = write_report(root, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if ok: print("BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_POST_LIVE_OK")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
