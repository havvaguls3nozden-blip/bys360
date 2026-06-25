from __future__ import annotations

import json
import shutil
from pathlib import Path

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0"

COPY_FILES = [
    "app/services/daily_weather_mail.py",
    "app/communication/daily_weather_mail_routes.py",
    "app/templates/communication/daily_weather_mail_settings.html",
    "scripts/communication/send_daily_weather_personnel_mail.py",
    "scripts/windows/install_bys360_daily_weather_mail_task.ps1",
    "scripts/quality/check_daily_weather_mail_v1_0.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def copy_overlay_files(overlay_root: Path, project_root: Path) -> list[str]:
    copied: list[str] = []
    for rel in COPY_FILES:
        src = overlay_root / rel
        dst = project_root / rel
        if not src.exists():
            raise FileNotFoundError(f"Overlay dosyası bulunamadı: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
            copied.append(rel)
    return copied


def patch_routes(project_root: Path) -> bool:
    path = project_root / "app/routes.py"
    text = read_text(path)
    marker = "# BYS360_DAILY_WEATHER_MAIL_V1_ROUTE_IMPORT"
    if marker in text:
        return False
    import_line = "from app.communication import daily_weather_mail_routes as _daily_weather_mail_routes  # noqa: E402,F401\n"
    anchor = "from app.communication import user_feedback_routes as _bys360_user_feedback_routes  # noqa: E402,F401\n"
    if anchor in text:
        text = text.replace(anchor, anchor + marker + "\n" + import_line + "# /BYS360_DAILY_WEATHER_MAIL_V1_ROUTE_IMPORT\n", 1)
    else:
        text += "\n" + marker + "\n" + import_line + "# /BYS360_DAILY_WEATHER_MAIL_V1_ROUTE_IMPORT\n"
    write_text(path, text)
    return True


def patch_base(project_root: Path) -> dict[str, bool]:
    path = project_root / "app/templates/base.html"
    text = read_text(path)
    changed = {"section": False, "open": False, "nav": False}

    old = "{% set show_comms_section = menu_map.get('messages', False) or menu_map.get('surveys', False) or menu_map.get('survey_manage', False) or menu_map.get('survey_results', False) or menu_map.get('feedback_dashboard', False) or menu_map.get('feedback_pulse', False) or menu_map.get('feedback_campaigns', False) or menu_map.get('feedback_results', False) or menu_map.get('feedback_actions', False) or menu_map.get('feedback_manager', False) or menu_map.get('feedback_admin', False) or menu_map.get('announcements', False) %}"
    new = "{% set show_comms_section = menu_map.get('messages', False) or menu_map.get('surveys', False) or menu_map.get('survey_manage', False) or menu_map.get('survey_results', False) or menu_map.get('feedback_dashboard', False) or menu_map.get('feedback_pulse', False) or menu_map.get('feedback_campaigns', False) or menu_map.get('feedback_results', False) or menu_map.get('feedback_actions', False) or menu_map.get('feedback_manager', False) or menu_map.get('feedback_admin', False) or menu_map.get('announcements', False) or menu_map.get('daily_weather_mail', False) or current_path.startswith('/communication/daily-weather-mail') or current_path.startswith('/iletisim/gunluk-hava-maili') %}"
    if old in text and "menu_map.get('daily_weather_mail'" not in text:
        text = text.replace(old, new, 1)
        changed["section"] = True

    old_open = "{% set is_comms_open = current_ep.startswith('main.messages_') or current_ep.startswith('main.survey_') or current_ep == 'main.surveys_list' or current_ep.startswith('main.announcements_') or current_ep == 'main.announcements_list' or current_path.startswith('/announcements') or current_path.startswith('/messages') or current_path.startswith('/survey') or current_path.startswith('/feedback') %}"
    new_open = "{% set is_comms_open = current_ep.startswith('main.messages_') or current_ep.startswith('main.survey_') or current_ep == 'main.surveys_list' or current_ep.startswith('main.announcements_') or current_ep == 'main.announcements_list' or current_ep.startswith('main.daily_weather_mail') or current_path.startswith('/announcements') or current_path.startswith('/messages') or current_path.startswith('/survey') or current_path.startswith('/feedback') or current_path.startswith('/communication/daily-weather-mail') or current_path.startswith('/iletisim/gunluk-hava-maili') %}"
    if old_open in text and "main.daily_weather_mail" not in text:
        text = text.replace(old_open, new_open, 1)
        changed["open"] = True

    nav_marker = "BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM"
    if nav_marker not in text:
        anchor = "{% if menu_map.get('announcements', False) %}{{ nav_item('/announcements', 'fa-bullhorn', 'Duyurular', current_path == '/announcements' or current_ep == 'main.announcements_list') }}{{ nav_item('/announcements/new', 'fa-paper-plane', 'Duyuru Gönder', current_path == '/announcements/new' or current_ep == 'main.announcements_new') }}{% endif %}"
        nav = """{# BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM #}\n                            {% if menu_map.get('daily_weather_mail', False) %}{{ nav_item(safe_url_for('main.daily_weather_mail_settings', fallback='/communication/daily-weather-mail'), 'fa-cloud-sun', 'Günlük Bilgilendirme', current_ep.startswith('main.daily_weather_mail') or current_path.startswith('/communication/daily-weather-mail') or current_path.startswith('/iletisim/gunluk-hava-maili')) }}{% endif %}\n                            {# /BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM #}"""
        if anchor in text:
            text = text.replace(anchor, nav + "\n                            " + anchor, 1)
        else:
            panel_anchor = "{% if menu_map.get('feedback_admin', False) %}{{ nav_item(safe_url_for('main.feedback_campaign_manage'), 'fa-sliders', 'Kampanya Yönetimi', current_path.startswith('/feedback/admin/campaigns')) }}{% endif %}"
            text = text.replace(panel_anchor, panel_anchor + "\n                            " + nav, 1)
        changed["nav"] = True

    write_text(path, text)
    return changed


def patch_menu_registry_sections(project_root: Path) -> bool:
    path = project_root / "app/menu_registry_data_sections.py"
    text = read_text(path)
    marker = "BYS360_DAILY_WEATHER_MAIL_V1_MENU_REGISTRY_ITEM"
    if marker in text:
        return False
    item = '''            # BYS360_DAILY_WEATHER_MAIL_V1_MENU_REGISTRY_ITEM
            {
                "key": "daily_weather_mail",
                "label": "Günlük Bilgilendirme Maili",
                "icon": "fa-solid fa-cloud-sun",
                "endpoint": "main.daily_weather_mail_settings",
                "active_endpoints": [
                    "main.daily_weather_mail_settings",
                    "main.daily_weather_mail_save_settings",
                    "main.daily_weather_mail_send_now",
                    "main.daily_weather_mail_dry_run",
                ],
                "active_path_prefixes": ["/communication/daily-weather-mail", "/iletisim/gunluk-hava-maili"],
                "required_roles": [
                    "admin",
                    "super_admin",
                    "system_admin",
                    "sistem_yoneticisi",
                    "baskan",
                    "baskan_yardimcisi",
                    "grup_baskani",
                    "mali_musavir",
                    "koordinator",
                    "birim_sorumlusu",
                    "performans_yetkilisi",
                ],
            },
            # /BYS360_DAILY_WEATHER_MAIL_V1_MENU_REGISTRY_ITEM
'''
    anchor = '''            {
                "key": "announcements",
                "label": "Duyurular",
                "icon": "fa-solid fa-bullhorn",
                "href": "/announcements",
                "active_endpoints": ["main.announcements_list"],
                "active_path_prefixes": ["/announcements"],
            },
'''
    if anchor in text:
        text = text.replace(anchor, item + anchor, 1)
    else:
        # güvenli yedek: iletişim items bloğunun sonuna yakın ekle
        close_anchor = '''            {
                "key": "announcements_create",
                "settings_key": "announcements",
'''
        text = text.replace(close_anchor, item + close_anchor, 1)
    write_text(path, text)
    return True


def patch_effective_menu(project_root: Path) -> bool:
    path = project_root / "app/services/settings/effective_menu.py"
    text = read_text(path)
    marker = "BYS360_DAILY_WEATHER_MAIL_EFFECTIVE_MENU_V1"
    if marker in text:
        return False
    block = r'''
# BYS360_DAILY_WEATHER_MAIL_EFFECTIVE_MENU_V1_BEGIN
_BYS360_DAILY_WEATHER_MAIL_MENU_KEY = "daily_weather_mail"
_BYS360_DAILY_WEATHER_MAIL_ALLOWED_ROLES = set([
    "admin",
    "super_admin",
    "system_admin",
    "sistem_yoneticisi",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
    "performans_yetkilisi",
])
for _policy_name in [
    "PHASE3_PERFORMANCE_MENU_POLICY",
    "PHASE3_2_PERFORMANCE_MENU_POLICY",
    "PERFORMANCE_MENU_POLICY",
    "ROLE_MENU_POLICY",
    "ROLE_MATRIX_POLICY",
]:
    _policy = globals().get(_policy_name)
    if isinstance(_policy, dict):
        _current = _policy.setdefault(_BYS360_DAILY_WEATHER_MAIL_MENU_KEY, set())
        if isinstance(_current, set):
            _current.update(_BYS360_DAILY_WEATHER_MAIL_ALLOWED_ROLES)
        elif isinstance(_current, list):
            _current.extend([_r for _r in _BYS360_DAILY_WEATHER_MAIL_ALLOWED_ROLES if _r not in _current])
for _set_name in [
    "PHASE3_2_MANAGER_VISIBLE_KEYS",
    "PHASE3_2_GENERAL_VISIBLE_KEYS",
    "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
    "PERFORMANCE_ROLE_MATRIX_KEYS",
]:
    _target = globals().get(_set_name)
    if isinstance(_target, set):
        _target.add(_BYS360_DAILY_WEATHER_MAIL_MENU_KEY)
    elif isinstance(_target, list) and _BYS360_DAILY_WEATHER_MAIL_MENU_KEY not in _target:
        _target.append(_BYS360_DAILY_WEATHER_MAIL_MENU_KEY)
# BYS360_DAILY_WEATHER_MAIL_EFFECTIVE_MENU_V1_END
'''
    text += "\n" + block + "\n"
    write_text(path, text)
    return True


def patch_role_defaults(project_root: Path) -> bool:
    path = project_root / "app/menu_registry.py"
    if not path.exists():
        return False
    text = read_text(path)
    marker = "BYS360_DAILY_WEATHER_MAIL_ROLE_DEFAULTS_V1"
    if marker in text:
        return False
    block = r'''
# BYS360_DAILY_WEATHER_MAIL_ROLE_DEFAULTS_V1_BEGIN
try:
    _BYS360_DAILY_WEATHER_ROLES = {
        "admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan",
        "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator",
        "birim_sorumlusu", "performans_yetkilisi",
    }
    for _role in _BYS360_DAILY_WEATHER_ROLES:
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("daily_weather_mail")
except Exception:
    pass
# BYS360_DAILY_WEATHER_MAIL_ROLE_DEFAULTS_V1_END
'''
    insert_after = "FORCE_VISIBLE_MENU_ROLES.setdefault(\"performance_president_approvals\", {\"admin\", \"baskan\"})\n# /BYS360_PRESIDENT_APPROVALS_FORCE_VISIBLE_MENU\n"
    if insert_after in text:
        text = text.replace(insert_after, insert_after + block, 1)
    else:
        text += "\n" + block
    write_text(path, text)
    return True


def main() -> int:
    overlay_root = Path(__file__).resolve().parents[2]
    project_root = Path.cwd()
    copied = copy_overlay_files(overlay_root, project_root)
    result = {
        "version": VERSION,
        "project_root": str(project_root),
        "copied": copied,
        "patch_routes": patch_routes(project_root),
        "patch_base": patch_base(project_root),
        "patch_menu_registry_sections": patch_menu_registry_sections(project_root),
        "patch_effective_menu": patch_effective_menu(project_root),
        "patch_role_defaults": patch_role_defaults(project_root),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"{VERSION}_APPLY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
