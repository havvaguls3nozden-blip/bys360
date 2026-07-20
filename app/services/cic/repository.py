
"""BYS360 CIC facade slice.

This module temporarily preserves the historical repository import surface.
Legacy forwarding wrappers are removed; every imported name resolves to its canonical owner.
Routes, template names, endpoint contracts and public function names are not changed.
"""
from __future__ import annotations

from datetime import date as _cic_v45_date
from datetime import datetime as _cic_v45_datetime
from datetime import timedelta as _cic_v45_timedelta

from app.services.cic.access_policy import can_manage
from app.services.cic.celebration_dates import (
    _cic_v40_bool,
    _cic_v40_days_until,
    _cic_v40_mmdd,
    _cic_v40_parse_date,
    _cic_v40_setting_bool,
    _cic_v40_special_days,
    _cic_v40_special_days_today,
    _cic_v40_today,
    _cic_v40_user_date,
)
from app.services.cic.cic_context import (
    _cic_auto_last_run_key,
    _cic_is_weekend,
    _cic_phase3_actor_label,
    _cic_phase3_last_result,
    _cic_phase3_make_result,
    _cic_phase3_public_error,
    _cic_phase3_store_result,
    _cic_phase5_actor,
    _cic_phase5_now_label,
    _cic_phase5_store_audit,
    _cic_phase6_bool,
    _cic_v40_create_system_notifications,
    _cic_v40_date_input,
    _cic_v40_upcoming_special_days,
    _cic_v45_bool,
    _cic_v45_build_user_indexes,
    _cic_v45_ensure_schema,
    _cic_v45_existing_user_rows,
    _cic_v45_header_key,
    _cic_v45_norm,
    _cic_v45_norm_name,
    _cic_v45_text,
    _cic_weekday_name_tr,
)
from app.services.cic.config_context import (
    _clean_ids,
    _clothing,
    _dumps_json,
    _has_settings_table,
    _loads_json,
    _now,
    _tomorrow_note,
    get_setting,  # noqa: F401 - historical repository compatibility attribute
)
from app.services.cic.misc_context import (
    _cic_auto_bool,
    _cic_phase5_audit_list,
    _cic_phase5_last_result,
    _cic_phase5_log_metrics,
    _cic_phase5_readiness,
    _cic_phase5_safe_int,
    _cic_phase6_build,
    _cic_phase6_log_quality,
    context,
    get_recent_logs,
)

__all__ = [
    "_cic_auto_bool",
    "_cic_auto_last_run_key",
    "_cic_is_weekend",
    "_cic_phase3_actor_label",
    "_cic_phase3_last_result",
    "_cic_phase3_make_result",
    "_cic_phase3_public_error",
    "_cic_phase3_store_result",
    "_cic_phase5_actor",
    "_cic_phase5_audit_list",
    "_cic_phase5_last_result",
    "_cic_phase5_log_metrics",
    "_cic_phase5_now_label",
    "_cic_phase5_readiness",
    "_cic_phase5_safe_int",
    "_cic_phase5_store_audit",
    "_cic_phase6_bool",
    "_cic_phase6_build",
    "_cic_phase6_log_quality",
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v40_bool",
    "_cic_v40_create_system_notifications",
    "_cic_v40_date_input",
    "_cic_v40_days_until",
    "_cic_v40_mmdd",
    "_cic_v40_parse_date",
    "_cic_v40_setting_bool",
    "_cic_v40_special_days",
    "_cic_v40_special_days_today",
    "_cic_v40_today",
    "_cic_v40_upcoming_special_days",
    "_cic_v40_user_date",
    "_cic_v45_bool",
    "_cic_v45_build_user_indexes",
    "_cic_v45_ensure_schema",
    "_cic_v45_existing_user_rows",
    "_cic_v45_header_key",
    "_cic_v45_norm",
    "_cic_v45_norm_name",
    "_cic_v45_parse_date",
    "_cic_v45_text",
    "_cic_weekday_name_tr",
    "_clean_ids",
    "_clothing",
    "_dumps_json",
    "_has_settings_table",
    "_loads_json",
    "_now",
    "_tomorrow_note",
    "can_manage",
    "context",
    "get_recent_logs",
]

# --- BYS360 P6 migrated low-risk helpers: start ---
# These helpers were migrated from app.services.corporate_information_center.
# The legacy module keeps import aliases for backwards compatibility.



def _cic_v11_bool(value, default=False):
    if value is None or value == "":
        return bool(default)
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "on", "yes", "evet", "tls", "ssl"}:
        return True
    if normalized in {"0", "false", "off", "no", "hayir", "hayır", "none", "null"}:
        return False
    return bool(default)

def _cic_v11_clean_header(value):
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()

def _cic_v11_normalize_email(value):
    email = _cic_v11_clean_header(value).strip().strip(",;")
    if not email or "@" not in email or " " in email:
        return ""
    return email



def _cic_v45_parse_date(value: object) -> _cic_v45_date | None:
    if value is None:
        return None
    if isinstance(value, _cic_v45_datetime):
        return value.date()
    if isinstance(value, _cic_v45_date):
        return value
    if isinstance(value, (int, float)):
        try:
            if value > 20000:
                return (_cic_v45_datetime(1899, 12, 30) + _cic_v45_timedelta(days=float(value))).date()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
    text = _cic_v45_text(value)
    if not text:
        return None
    text = text.replace("-", ".").replace("/", ".")
    for fmt in ("%d.%m.%Y", "%Y.%m.%d", "%d.%m.%y"):
        try:
            return _cic_v45_datetime.strptime(text, fmt).date()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
    return None


# --- BYS360 P6 migrated low-risk helpers: end ---
