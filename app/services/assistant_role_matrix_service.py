"""BYS360 canonical assistant role-matrix service (TD-CAND-002 closure).

Single source of truth for the assistant module's per-role visibility matrix,
replacing two independently-drifting duplicate implementations that used to
live in app/main_handlers/account_settings_helpers.py (BYS360_ASSISTANT_ROLE_MATRIX_V12_FIX)
and app/main_handlers/account_communication_helpers.py
(BYS360_ASSISTANT_ROLE_MATRIX_SETTINGS_V11).

Canonical behavior decisions locked by this consolidation (see
tests/behavior/test_assistant_role_matrix_behavior_contract.py):
  - Missing or empty-string stored visible_roles configuration (including a
    settings-fetch failure) falls back to ASSISTANT_DEFAULT_VISIBLE_ROLES --
    matches the confirmed-live settings-side behavior and the shared
    assistant-settings service's own default-role intent.
  - An explicit "__none__" sentinel (what this module itself persists when a
    save action selects zero roles) always resolves to an empty role set,
    distinct from "never configured".
  - The settings-row lookup step (an optional/recoverable read) tolerates a
    query failure by falling through to "create a new row" -- it does not
    swallow a real persistence (commit) failure, which always propagates.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

ASSISTANT_POLICY_ROLE_OPTIONS = [
    ("admin", "Admin"),
    ("baskan", "Başkan"),
    ("baskan_yardimcisi", "Başkan Yardımcısı"),
    ("grup_baskani", "Grup Başkanı"),
    ("mali_musavir", "Mali Müşavir"),
    ("koordinator", "Koordinatör"),
    ("birim_sorumlusu", "Birim Sorumlusu"),
    ("personel", "Personel"),
    ("kullanici", "Rolsüz/Kullanıcı"),
]

ASSISTANT_DEFAULT_VISIBLE_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
}

ASSISTANT_ROLE_MATRIX_ROWS = [
    {
        "key": "assistant_module",
        "label": "Sanal Asistan Modülü",
        "icon": "fa-solid fa-sparkles",
        "description": "Ana anahtar. Kapalı rolde asistan menüsü, asistan penceresi ve içindeki tüm kısa yollar görünmez.",
    },
]


def _normalize_role_token(value: Any) -> str:
    raw = "" if value is None else str(value)
    return raw.strip().lower().replace("ı", "i").replace("İ", "i").replace(" ", "_").replace("-", "_")


def _assistant_visible_roles_from_settings() -> set[str]:
    try:
        from app.services.assistant_settings_service import get_assistant_settings
        data = get_assistant_settings() or {}
    except Exception:
        logger.exception("BYS360 assistant role-matrix: get_assistant_settings() failed, falling back to recommended defaults")
        data = {}

    raw = str(data.get("visible_roles") or "").strip()
    if not raw:
        raw = ",".join(sorted(ASSISTANT_DEFAULT_VISIBLE_ROLES))

    roles = {
        _normalize_role_token(item)
        for item in raw.replace(";", ",").replace("\n", ",").split(",")
        if str(item or "").strip()
    }
    return {role for role in roles if role and role != "__none__"}


def build_assistant_role_matrix() -> dict[str, Any]:
    visible_roles = _assistant_visible_roles_from_settings()

    role_rows = []
    item_rows = []

    for role_key, role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
        role_rows.append({
            "role_key": role_key,
            "role_label": role_label,
            "visible_count": 1 if role_key in visible_roles else 0,
            "recommended_count": 1 if role_key in ASSISTANT_DEFAULT_VISIBLE_ROLES else 0,
        })

    for item in ASSISTANT_ROLE_MATRIX_ROWS:
        states = []
        visible_count = 0
        recommended_roles = []

        for role_key, role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
            is_visible = role_key in visible_roles
            is_recommended = role_key in ASSISTANT_DEFAULT_VISIBLE_ROLES

            if is_visible:
                visible_count += 1
            if is_recommended:
                recommended_roles.append(role_label)

            states.append({
                "role_key": role_key,
                "role_label": role_label,
                "is_visible": is_visible,
                "is_recommended": is_recommended,
            })

        item_rows.append({
            "key": item["key"],
            "label": item["label"],
            "icon": item["icon"],
            "description": item["description"],
            "visible_count": visible_count,
            "states": states,
            "recommended_roles": recommended_roles,
        })

    return {
        "roles": role_rows,
        "rows": item_rows,
        "items": item_rows,
        "item_count": len(item_rows),
        "visible_roles": sorted(visible_roles),
    }


def _upsert_assistant_module_setting(setting_key, label, value_text, value_type="string", description="", updated_by_user_id=None):
    from app.extensions import db
    from app.models import ModuleSetting

    try:
        row = ModuleSetting.query.filter_by(module_key="assistant", setting_key=setting_key).first()
    except Exception:
        logger.exception("BYS360 assistant role-matrix: existing module_settings lookup failed, treating as not-found")
        row = None

    if row is None:
        row = ModuleSetting(module_key="assistant", setting_key=setting_key)
        db.session.add(row)

    row.label = label
    row.value_text = str(value_text)
    row.value_type = value_type
    row.description = description
    row.is_active = True
    row.updated_by_user_id = updated_by_user_id
    return row


def save_assistant_role_matrix_from_form(form, *, updated_by_user_id=None):
    from app.extensions import db

    selected_roles = []
    for role_key, _role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
        field_name = f"assistant_role_policy__{role_key}__assistant_module"
        if form.get(field_name):
            selected_roles.append(role_key)

    visible_roles_value = ",".join(selected_roles) if selected_roles else "__none__"

    _upsert_assistant_module_setting(
        "enabled",
        "Sanal Asistan Aktif",
        "true",
        "bool",
        "Sanal Asistan genel aktiflik bayrağı. Rol bazlı görünürlük visible_roles ile yönetilir.",
        updated_by_user_id=updated_by_user_id,
    )
    _upsert_assistant_module_setting(
        "visible_roles",
        "Sanal Asistan Görünür Rolleri",
        visible_roles_value,
        "string",
        "Sanal Asistan ana menüsü, penceresi ve tüm kısa yolları hangi rollerde görünecek.",
        updated_by_user_id=updated_by_user_id,
    )
    db.session.commit()
    return len(selected_roles)


def reset_assistant_role_matrix_defaults(*, updated_by_user_id=None):
    from app.extensions import db

    visible_roles_value = ",".join(sorted(ASSISTANT_DEFAULT_VISIBLE_ROLES))

    _upsert_assistant_module_setting(
        "enabled",
        "Sanal Asistan Aktif",
        "true",
        "bool",
        "Sanal Asistan genel aktiflik bayrağı.",
        updated_by_user_id=updated_by_user_id,
    )
    _upsert_assistant_module_setting(
        "visible_roles",
        "Sanal Asistan Görünür Rolleri",
        visible_roles_value,
        "string",
        "Önerilen rol politikası: yönetici rolleri açık, personel/kullanıcı kapalı.",
        updated_by_user_id=updated_by_user_id,
    )
    db.session.commit()
    return len(ASSISTANT_DEFAULT_VISIBLE_ROLES)
