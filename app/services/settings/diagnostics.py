from __future__ import annotations

"""Ayarlar servisi tanılama ve sağlık özeti yardımcıları.

Bu modül yalnızca okuma/tanılama amacıyla kullanılır. Ayar kayıt davranışını,
commit/rollback zincirini veya canlı menü izinlerini değiştirmez.
"""

from collections.abc import Iterable
from typing import Any

from sqlalchemy import inspect

from app.config import is_removed_menu_key
from app.extensions import db
from app.menu_registry import ROLE_MENU_DEFAULTS, flatten_menu_definitions
from app.models import (
    ModuleSetting,
    RoleMenuDefault,
    SettingsChangeLog,
    SystemSetting,
    UnitMenuProfile,
    UserMenuPermission,
)

CORE_SETTINGS_TABLES: tuple[str, ...] = (
    "system_settings",
    "module_settings",
    "settings_change_logs",
    "user_menu_permissions",
    "role_menu_defaults",
    "unit_menu_profiles",
)

SETTINGS_DIAGNOSTIC_SCOPE = "settings_service_health"


def _safe_rollback() -> None:
    try:
        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/settings/diagnostics.py")
def _table_exists(table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        _safe_rollback()
        return False


def _safe_count(model: Any) -> int:
    try:
        return int(model.query.count())
    except Exception:
        _safe_rollback()
        return 0


def _safe_distinct_count(model: Any, column: Any) -> int:
    try:
        return int(model.query.with_entities(column).distinct().count())
    except Exception:
        _safe_rollback()
        return 0


def _normalize_menu_keys(keys: Iterable[Any]) -> list[str]:
    result: list[str] = []
    for key in keys:
        text = str(key or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def build_settings_table_health() -> dict[str, Any]:
    """Ayarlar omurgasındaki temel tabloların varlık ve kayıt özetini üretir."""
    model_map = {
        "system_settings": SystemSetting,
        "module_settings": ModuleSetting,
        "settings_change_logs": SettingsChangeLog,
        "user_menu_permissions": UserMenuPermission,
        "role_menu_defaults": RoleMenuDefault,
        "unit_menu_profiles": UnitMenuProfile,
    }
    tables: list[dict[str, Any]] = []
    missing: list[str] = []
    for table_name in CORE_SETTINGS_TABLES:
        exists = _table_exists(table_name)
        if not exists:
            missing.append(table_name)
        row_count = _safe_count(model_map[table_name]) if exists else 0
        tables.append({
            "table_name": table_name,
            "exists": exists,
            "row_count": row_count,
            "status": "ok" if exists else "missing",
        })
    return {
        "scope": SETTINGS_DIAGNOSTIC_SCOPE,
        "ready": len(missing) == 0,
        "missing_tables": missing,
        "tables": tables,
    }


def build_menu_registry_health() -> dict[str, Any]:
    """Canlı menü kayıt defteri ile ayar menü izin omurgasının kısa özetini üretir."""
    try:
        flat_items = flatten_menu_definitions()
    except Exception:
        flat_items = []

    all_keys = _normalize_menu_keys(item.get("key") for item in flat_items if isinstance(item, dict))
    removed_keys = [key for key in all_keys if is_removed_menu_key(key)]
    live_keys = [key for key in all_keys if key not in set(removed_keys)]

    role_profile_count = 0
    unit_profile_count = 0
    user_override_user_count = 0
    if _table_exists("role_menu_defaults"):
        role_profile_count = _safe_distinct_count(RoleMenuDefault, RoleMenuDefault.role_name)
    if _table_exists("unit_menu_profiles"):
        unit_profile_count = _safe_distinct_count(UnitMenuProfile, UnitMenuProfile.unit_name)
    if _table_exists("user_menu_permissions"):
        user_override_user_count = _safe_distinct_count(UserMenuPermission, UserMenuPermission.user_id)

    return {
        "menu_total": len(all_keys),
        "live_menu_total": len(live_keys),
        "removed_menu_total": len(removed_keys),
        "removed_menu_keys": removed_keys,
        "role_default_total": len(ROLE_MENU_DEFAULTS),
        "role_profile_count": role_profile_count,
        "unit_profile_count": unit_profile_count,
        "user_override_user_count": user_override_user_count,
        "core_menu_present": {
            "messages": "messages" in live_keys,
            "notifications": "notifications" in live_keys,
            "surveys": "surveys" in live_keys,
            "performance_reports": "performance_reports" in live_keys,
        },
    }


def _log_to_dict(row: SettingsChangeLog) -> dict[str, Any]:
    created_at = getattr(row, "created_at", None)
    return {
        "id": getattr(row, "id", None),
        "change_scope": getattr(row, "change_scope", None),
        "action_type": getattr(row, "action_type", None),
        "summary": getattr(row, "summary", None),
        "actor_user_id": getattr(row, "actor_user_id", None),
        "target_user_id": getattr(row, "target_user_id", None),
        "target_role_name": getattr(row, "target_role_name", None),
        "target_unit_name": getattr(row, "target_unit_name", None),
        "is_rollback": bool(getattr(row, "is_rollback", False)),
        "reverted_from_log_id": getattr(row, "reverted_from_log_id", None),
        "created_at": created_at.isoformat() if created_at else None,
    }


def list_settings_recent_activity(limit: int = 8) -> list[dict[str, Any]]:
    """Son ayar değişikliklerini route/template bağı olmadan okunabilir dict listesi yapar."""
    if not _table_exists("settings_change_logs"):
        return []
    safe_limit = max(1, min(int(limit or 8), 50))
    try:
        rows = SettingsChangeLog.query.order_by(SettingsChangeLog.id.desc()).limit(safe_limit).all()
    except Exception:
        _safe_rollback()
        return []
    return [_log_to_dict(row) for row in rows]


def build_settings_diagnostics_context(*, include_recent_logs: bool = True, recent_limit: int = 8) -> dict[str, Any]:
    """Ayarlar servisi için tek noktadan okunabilir sağlık/tanılama context'i."""
    table_health = build_settings_table_health()
    menu_health = build_menu_registry_health()
    recent_activity = list_settings_recent_activity(recent_limit) if include_recent_logs else []
    warning_codes: list[str] = []

    if not table_health.get("ready"):
        warning_codes.append("settings_tables_missing")
    if menu_health.get("live_menu_total", 0) <= 0:
        warning_codes.append("live_menu_registry_empty")
    if not menu_health.get("core_menu_present", {}).get("messages"):
        warning_codes.append("messages_menu_missing")
    if not menu_health.get("core_menu_present", {}).get("surveys"):
        warning_codes.append("surveys_menu_missing")

    return {
        "scope": SETTINGS_DIAGNOSTIC_SCOPE,
        "ready": not warning_codes,
        "warning_codes": warning_codes,
        "table_health": table_health,
        "menu_health": menu_health,
        "recent_activity": recent_activity,
        "stats": {
            "settings_table_total": len(CORE_SETTINGS_TABLES),
            "missing_table_total": len(table_health.get("missing_tables", [])),
            "live_menu_total": menu_health.get("live_menu_total", 0),
            "removed_menu_total": menu_health.get("removed_menu_total", 0),
            "recent_activity_total": len(recent_activity),
        },
    }
