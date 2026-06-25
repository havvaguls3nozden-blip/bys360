from __future__ import annotations

import json
import py_compile
import re
import shutil
from pathlib import Path

VERSION = "BYS360_DAILY_WEATHER_MAIL_V1_0_5_PREMIUM_EXEC_MENU"
EXEC_URL = "/executive-summary/daily-weather-mail"
EXEC_TR_URL = "/yonetici-ozeti/gunluk-hava-maili"

ALLOWED_ROLES = [
    "admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan",
    "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator",
    "birim_sorumlusu", "performans_yetkilisi",
]

TEMPLATE_REL = "app/templates/communication/daily_weather_mail_settings.html"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup(path: Path, tag: str = "v105") -> str | None:
    if not path.exists():
        return None
    bdir = path.parent / f".backup_daily_weather_{tag}"
    bdir.mkdir(parents=True, exist_ok=True)
    dst = bdir / (path.name + ".bak")
    if not dst.exists():
        shutil.copy2(path, dst)
    return str(dst)


def overlay_root_from_script() -> Path:
    # scripts/communication/<this>.py -> project root after overlay extraction.
    return Path(__file__).resolve().parents[2]


def copy_premium_template(project_root: Path) -> dict[str, object]:
    src = overlay_root_from_script() / TEMPLATE_REL
    dst = project_root / TEMPLATE_REL
    if not src.exists():
        # If the template file was already copied by Expand-Archive, it may only exist at destination.
        return {"source_exists": False, "dest_exists": dst.exists(), "changed": False, "reason": "overlay template source not found"}
    new_text = read_text(src)
    old_text = read_text(dst) if dst.exists() else ""
    backup_path = backup(dst) if dst.exists() else None
    changed = new_text != old_text
    if changed:
        write_text(dst, new_text)
    return {"source_exists": True, "dest_exists": dst.exists(), "changed": changed, "backup": backup_path}


def patch_routes(project_root: Path) -> dict[str, object]:
    path = project_root / "app/communication/daily_weather_mail_routes.py"
    if not path.exists():
        return {"exists": False, "changed": False, "reason": "route file not found"}
    original = read_text(path)
    text = original
    backup_path = backup(path)

    if '@main_bp.get("/executive-summary/daily-weather-mail")' not in text:
        text = text.replace(
            '@main_bp.get("/communication/daily-weather-mail")\n@main_bp.get("/iletisim/gunluk-hava-maili")',
            '@main_bp.get("/executive-summary/daily-weather-mail")\n@main_bp.get("/yonetici-ozeti/gunluk-hava-maili")\n@main_bp.get("/communication/daily-weather-mail")\n@main_bp.get("/iletisim/gunluk-hava-maili")',
            1,
        )

    aliases = [
        (
            '@main_bp.post("/communication/daily-weather-mail/settings")\n@main_bp.post("/iletisim/gunluk-hava-maili/ayarlar")',
            '@main_bp.post("/executive-summary/daily-weather-mail/settings")\n@main_bp.post("/yonetici-ozeti/gunluk-hava-maili/ayarlar")\n@main_bp.post("/communication/daily-weather-mail/settings")\n@main_bp.post("/iletisim/gunluk-hava-maili/ayarlar")',
        ),
        (
            '@main_bp.post("/communication/daily-weather-mail/send-now")\n@main_bp.post("/iletisim/gunluk-hava-maili/simdi-gonder")',
            '@main_bp.post("/executive-summary/daily-weather-mail/send-now")\n@main_bp.post("/yonetici-ozeti/gunluk-hava-maili/simdi-gonder")\n@main_bp.post("/communication/daily-weather-mail/send-now")\n@main_bp.post("/iletisim/gunluk-hava-maili/simdi-gonder")',
        ),
        (
            '@main_bp.post("/communication/daily-weather-mail/dry-run")\n@main_bp.post("/iletisim/gunluk-hava-maili/kuru-calisma")',
            '@main_bp.post("/executive-summary/daily-weather-mail/dry-run")\n@main_bp.post("/yonetici-ozeti/gunluk-hava-maili/kuru-calisma")\n@main_bp.post("/communication/daily-weather-mail/dry-run")\n@main_bp.post("/iletisim/gunluk-hava-maili/kuru-calisma")',
        ),
    ]
    for old, new in aliases:
        if new not in text and old in text:
            text = text.replace(old, new, 1)

    # All save/send/dry-run actions should land back on the Yönetici Özeti page.
    text = text.replace('return redirect(url_for("main.daily_weather_mail_settings"))', f'return redirect("{EXEC_URL}")')

    changed = text != original
    if changed:
        write_text(path, text)
    return {"exists": True, "changed": changed, "backup": backup_path}


def remove_old_blocks(text: str) -> str:
    patterns = [
        r"\s*\{# BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM #\}.*?\{# /BYS360_DAILY_WEATHER_MAIL_V1_NAV_ITEM #\}\s*",
        r"\s*\{# BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_NAV_ITEM #\}.*?\{# /BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_NAV_ITEM #\}\s*",
        r"\s*\{# BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_SECTION_BEGIN #\}.*?\{# BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_SECTION_END #\}\s*",
        r"\s*\{# BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_FORCE_SECTION_BEGIN #\}.*?\{# BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_FORCE_SECTION_END #\}\s*",
    ]
    for pat in patterns:
        text = re.sub(pat, "\n", text, flags=re.S)
    return text


def forced_executive_section() -> str:
    roles = json.dumps(ALLOWED_ROLES, ensure_ascii=False)
    return f'''
                {{# BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_FORCE_SECTION_BEGIN #}}
                {{% set bys360_daily_weather_allowed_roles = {roles} %}}
                {{% set bys360_daily_weather_role = (current_user.role|default('', true)|string|lower) if current_user.is_authenticated else '' %}}
                {{% set bys360_daily_weather_visible = menu_map.get('daily_weather_mail', False) or menu_map.get('executive_summary', False) or current_user.is_admin|default(false) or current_user.is_superuser|default(false) or bys360_daily_weather_role in bys360_daily_weather_allowed_roles or current_path.startswith('/executive-summary') or current_path.startswith('/yonetici-ozeti') %}}
                {{% set bys360_daily_weather_open = current_ep.startswith('main.daily_weather_mail') or current_path.startswith('/executive-summary') or current_path.startswith('/yonetici-ozeti') %}}
                {{% if bys360_daily_weather_visible %}}
                <div class="accordion-nav bys360-executive-summary-nav" data-module-section="executive-summary">
                    <details class="bys-accordion {{% if bys360_daily_weather_open %}}has-active{{% endif %}}" data-accordion-key="executive-summary" data-has-active="{{{{ 'true' if bys360_daily_weather_open else 'false' }}}}" {{% if bys360_daily_weather_open %}}open{{% endif %}}>
                        <summary><div class="accordion-left"><i class="fa-solid fa-chart-pie"></i><span>Yönetici Özeti</span></div><div class="accordion-right"><span class="accordion-current-pill" data-accordion-current hidden></span><i class="fa-solid fa-chevron-down accordion-chevron"></i></div></summary>
                        <div class="accordion-panel">
                            {{{{ nav_item('{EXEC_URL}', 'fa-cloud-sun-rain', 'Günlük Personel Bilgilendirme', current_ep.startswith('main.daily_weather_mail') or current_path.startswith('{EXEC_URL}') or current_path.startswith('{EXEC_TR_URL}'), none, 'data-nav-key="daily_weather_mail" data-menu-key="daily_weather_mail" data-screen-key="executive_daily_weather_mail"') }}}}
                        </div>
                    </details>
                </div>
                {{% endif %}}
                {{# BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_FORCE_SECTION_END #}}
'''


def patch_base(project_root: Path) -> dict[str, object]:
    path = project_root / "app/templates/base.html"
    if not path.exists():
        return {"exists": False, "changed": False, "reason": "base.html not found"}
    original = read_text(path)
    text = remove_old_blocks(original)
    backup_path = backup(path)
    block = forced_executive_section()

    # Put the visible Yönetici Özeti block immediately before İletişim ve Anket Yönetimi.
    markers = [
        "{% if show_comms_section %}",
        "<span>İletişim ve Anket Yönetimi</span>",
        "<span>Iletisim ve Anket Yonetimi</span>",
        "{# BYS360_CORPORATE_PORTAL_MENU",
    ]
    inserted = False
    insert_mode = "append"
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            if marker.startswith("<span>"):
                # Move to the beginning of the containing section if possible.
                start = text.rfind("\n                {% if", 0, idx)
                idx = start if start != -1 else idx
            text = text[:idx] + block + "\n" + text[idx:]
            inserted = True
            insert_mode = f"before:{marker[:35]}"
            break
    if not inserted:
        text += "\n" + block

    changed = text != original
    if changed:
        write_text(path, text)
    return {"exists": True, "changed": changed, "backup": backup_path, "insert_mode": insert_mode}


def daily_weather_item() -> str:
    return '''            # BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_MENU_ITEM
            {
                "key": "daily_weather_mail",
                "label": "Günlük Personel Bilgilendirme",
                "icon": "fa-solid fa-cloud-sun-rain",
                "endpoint": "main.daily_weather_mail_settings",
                "active_endpoints": [
                    "main.daily_weather_mail_settings",
                    "main.daily_weather_mail_save_settings",
                    "main.daily_weather_mail_send_now",
                    "main.daily_weather_mail_dry_run",
                ],
                "active_path_prefixes": [
                    "/executive-summary/daily-weather-mail",
                    "/yonetici-ozeti/gunluk-hava-maili",
                    "/communication/daily-weather-mail",
                    "/iletisim/gunluk-hava-maili",
                ],
                "required_roles": [
                    "admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan",
                    "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator",
                    "birim_sorumlusu", "performans_yetkilisi",
                ],
            },
            # /BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_MENU_ITEM
'''


def patch_menu_registry_data_sections(project_root: Path) -> dict[str, object]:
    path = project_root / "app/menu_registry_data_sections.py"
    if not path.exists():
        return {"exists": False, "changed": False, "reason": "menu_registry_data_sections.py not found"}
    original = read_text(path)
    text = original
    backup_path = backup(path)

    # Remove older injected items if present.
    text = re.sub(r"\s*# BYS360_DAILY_WEATHER_MAIL_V1_MENU_REGISTRY_ITEM\s*\{.*?\},\s*# /BYS360_DAILY_WEATHER_MAIL_V1_MENU_REGISTRY_ITEM\s*", "\n", text, flags=re.S)
    text = re.sub(r"\s*# BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_MENU_ITEM\s*\{.*?\},\s*# /BYS360_DAILY_WEATHER_MAIL_V1_0_4_EXEC_MENU_ITEM\s*", "\n", text, flags=re.S)
    text = re.sub(r"\s*# BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_MENU_ITEM\s*\{.*?\},\s*# /BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_MENU_ITEM\s*", "\n", text, flags=re.S)

    item = daily_weather_item()
    inserted = False
    insert_mode = "none"
    # Existing executive_summary section with items list.
    m = re.search(r"(\{\s*['\"]key['\"]\s*:\s*['\"]executive_summary['\"].*?['\"]items['\"]\s*:\s*\[)", text, flags=re.S)
    if m:
        text = text[:m.end()] + "\n" + item + text[m.end():]
        inserted = True
        insert_mode = "existing_executive_summary"
    else:
        # Insert a full section before İletişim if possible.
        section = '''    # BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_SECTION
    {
        "key": "executive_summary",
        "label": "Yönetici Özeti",
        "icon": "fa-solid fa-chart-pie",
        "items": [
''' + item + '''        ],
    },
    # /BYS360_DAILY_WEATHER_MAIL_V1_0_5_EXEC_SECTION
'''
        m = re.search(r"(\s*\{\s*['\"]key['\"]\s*:\s*['\"](?:iletisim|communication|comms)['\"]\s*,)", text)
        if m:
            text = text[:m.start()] + section + text[m.start():]
            inserted = True
            insert_mode = "new_section_before_comms"
        else:
            idx = text.rfind("\n]")
            if idx != -1:
                text = text[:idx] + "\n" + section + text[idx:]
                inserted = True
                insert_mode = "append_before_list_end"

    changed = text != original
    if changed:
        write_text(path, text)
    return {"exists": True, "changed": changed, "backup": backup_path, "inserted": inserted, "insert_mode": insert_mode}


def append_policy_block(path: Path, block: str, marker: str) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "changed": False, "reason": f"{path.name} not found"}
    original = read_text(path)
    text = original
    backup_path = backup(path)
    # Remove older blocks and rewrite latest one.
    text = re.sub(r"\n# BYS360_DAILY_WEATHER_MAIL_EXEC_ROLE_DEFAULTS_V1_0_4_BEGIN.*?# BYS360_DAILY_WEATHER_MAIL_EXEC_ROLE_DEFAULTS_V1_0_4_END\s*", "\n", text, flags=re.S)
    text = re.sub(r"\n# BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_4_BEGIN.*?# BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_4_END\s*", "\n", text, flags=re.S)
    text = re.sub(rf"\n# {re.escape(marker)}_BEGIN.*?# {re.escape(marker)}_END\s*", "\n", text, flags=re.S)
    text += "\n" + block
    changed = text != original
    if changed:
        write_text(path, text)
    return {"exists": True, "changed": changed, "backup": backup_path}


def patch_menu_registry(project_root: Path) -> dict[str, object]:
    marker = "BYS360_DAILY_WEATHER_MAIL_EXEC_ROLE_DEFAULTS_V1_0_5"
    block = f'''
# {marker}_BEGIN
try:
    _BYS360_DAILY_WEATHER_EXEC_ROLES = {set(ALLOWED_ROLES)!r}
    for _role in _BYS360_DAILY_WEATHER_EXEC_ROLES:
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("daily_weather_mail")
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("executive_summary")
except Exception:
    pass
# {marker}_END
'''
    return append_policy_block(project_root / "app/menu_registry.py", block, marker)


def patch_effective_menu(project_root: Path) -> dict[str, object]:
    marker = "BYS360_DAILY_WEATHER_MAIL_EXEC_EFFECTIVE_MENU_V1_0_5"
    block = f'''
# {marker}_BEGIN
try:
    _BYS360_DAILY_WEATHER_EXEC_ALLOWED_ROLES = {set(ALLOWED_ROLES)!r}
    for _policy_name in [
        "PHASE3_PERFORMANCE_MENU_POLICY",
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "PERFORMANCE_MENU_POLICY",
        "ROLE_MENU_POLICY",
        "ROLE_MATRIX_POLICY",
    ]:
        _policy = globals().get(_policy_name)
        if isinstance(_policy, dict):
            for _key in ["daily_weather_mail", "executive_summary"]:
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_BYS360_DAILY_WEATHER_EXEC_ALLOWED_ROLES)
                elif isinstance(_current, list):
                    _current.extend([_r for _r in _BYS360_DAILY_WEATHER_EXEC_ALLOWED_ROLES if _r not in _current])
    for _set_name in [
        "PHASE3_2_MANAGER_VISIBLE_KEYS",
        "PHASE3_2_GENERAL_VISIBLE_KEYS",
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
        "PERFORMANCE_ROLE_MATRIX_KEYS",
    ]:
        _target = globals().get(_set_name)
        if isinstance(_target, set):
            _target.add("daily_weather_mail")
            _target.add("executive_summary")
except Exception:
    pass
# {marker}_END
'''
    return append_policy_block(project_root / "app/services/settings/effective_menu.py", block, marker)


def compile_targets(project_root: Path) -> list[str]:
    errors: list[str] = []
    for rel in [
        "app/communication/daily_weather_mail_routes.py",
        "app/menu_registry_data_sections.py",
        "app/menu_registry.py",
        "app/services/settings/effective_menu.py",
        "app/services/daily_weather_mail.py",
        "scripts/communication/send_daily_weather_personnel_mail.py",
    ]:
        path = project_root / rel
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append(f"{rel}: {exc}")
    return errors


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=None)
    args = parser.parse_args()
    project_root = Path(args.project_root or Path.cwd()).resolve()
    result = {
        "version": VERSION,
        "project_root": str(project_root),
        "routes": patch_routes(project_root),
        "template": copy_premium_template(project_root),
        "base": patch_base(project_root),
        "menu_registry_data_sections": patch_menu_registry_data_sections(project_root),
        "menu_registry": patch_menu_registry(project_root),
        "effective_menu": patch_effective_menu(project_root),
    }
    result["compile_errors"] = compile_targets(project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["compile_errors"]:
        print(f"{VERSION}_COMPILE_FAIL")
        return 2
    print(f"{VERSION}_APPLY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
