
"""BYS360 CIC facade slice.

This module is intentionally facade-only in P5.
The legacy implementation remains in app.services.corporate_information_center.
Routes, template names, endpoint contracts and public function names are not changed.
"""
from __future__ import annotations

from typing import Any

from app.services import corporate_information_center as _legacy

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

def _cic_auto_last_run_key(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_auto_last_run_key``."""
    return _legacy._cic_auto_last_run_key(*args, **kwargs)

def _cic_phase3_actor_label(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase3_actor_label``."""
    return _legacy._cic_phase3_actor_label(*args, **kwargs)

def _cic_phase3_last_result(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase3_last_result``."""
    return _legacy._cic_phase3_last_result(*args, **kwargs)

def _cic_phase3_make_result(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase3_make_result``."""
    return _legacy._cic_phase3_make_result(*args, **kwargs)

def _cic_phase3_public_error(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase3_public_error``."""
    return _legacy._cic_phase3_public_error(*args, **kwargs)

def _cic_phase3_store_result(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase3_store_result``."""
    return _legacy._cic_phase3_store_result(*args, **kwargs)

def _cic_phase5_actor(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_actor``."""
    return _legacy._cic_phase5_actor(*args, **kwargs)

def _cic_phase5_audit_list(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_audit_list``."""
    return _legacy._cic_phase5_audit_list(*args, **kwargs)

def _cic_phase5_last_result(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_last_result``."""
    return _legacy._cic_phase5_last_result(*args, **kwargs)

def _cic_phase5_log_metrics(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_log_metrics``."""
    return _legacy._cic_phase5_log_metrics(*args, **kwargs)

def _cic_phase5_now_label(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_now_label``."""
    return _legacy._cic_phase5_now_label(*args, **kwargs)

def _cic_phase5_readiness(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_readiness``."""
    return _legacy._cic_phase5_readiness(*args, **kwargs)

def _cic_phase5_safe_int(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_safe_int``."""
    return _legacy._cic_phase5_safe_int(*args, **kwargs)

def _cic_phase5_store_audit(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_store_audit``."""
    return _legacy._cic_phase5_store_audit(*args, **kwargs)

def _cic_phase6_bool(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase6_bool``."""
    return _legacy._cic_phase6_bool(*args, **kwargs)

def _cic_phase6_build(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase6_build``."""
    return _legacy._cic_phase6_build(*args, **kwargs)


def _cic_phase6_log_quality(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase6_log_quality``."""
    return _legacy._cic_phase6_log_quality(*args, **kwargs)


def _cic_v40_create_system_notifications(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_create_system_notifications``."""
    return _legacy._cic_v40_create_system_notifications(*args, **kwargs)

def _cic_v40_date_input(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_date_input``."""
    return _legacy._cic_v40_date_input(*args, **kwargs)

def _cic_v40_setting_bool(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_setting_bool``."""
    return _legacy._cic_v40_setting_bool(*args, **kwargs)

def _cic_v40_special_days(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_special_days``."""
    return _legacy._cic_v40_special_days(*args, **kwargs)

def _cic_v40_special_days_today(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_special_days_today``."""
    return _legacy._cic_v40_special_days_today(*args, **kwargs)

def _cic_v40_upcoming_special_days(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_upcoming_special_days``."""
    return _legacy._cic_v40_upcoming_special_days(*args, **kwargs)

def _cic_v40_user_date(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v40_user_date``."""
    return _legacy._cic_v40_user_date(*args, **kwargs)

def _cic_v45_build_user_indexes(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v45_build_user_indexes``."""
    return _legacy._cic_v45_build_user_indexes(*args, **kwargs)

def _cic_v45_ensure_schema(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v45_ensure_schema``."""
    return _legacy._cic_v45_ensure_schema(*args, **kwargs)

def _cic_v45_existing_user_rows(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v45_existing_user_rows``."""
    return _legacy._cic_v45_existing_user_rows(*args, **kwargs)

def _clothing(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_clothing``."""
    return _legacy._clothing(*args, **kwargs)


def _tomorrow_note(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_tomorrow_note``."""
    return _legacy._tomorrow_note(*args, **kwargs)


def can_manage(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``can_manage``."""
    return _legacy.can_manage(*args, **kwargs)

def context(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``context``."""
    return _legacy.context(*args, **kwargs)

def get_recent_logs(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``get_recent_logs``."""
    return _legacy.get_recent_logs(*args, **kwargs)


# --- BYS360 P6 migrated low-risk helpers: start ---
# These helpers were migrated from app.services.corporate_information_center.
# The legacy module keeps import aliases for backwards compatibility.
import json
import logging
import re as _cic_v45_re
import unicodedata as _cic_v45_unicodedata
from datetime import date as _cic_v40_date
from datetime import date as _cic_v45_date
from datetime import datetime
from datetime import datetime as _cic_dt_datetime
from datetime import datetime as _cic_v40_datetime
from datetime import datetime as _cic_v45_datetime
from datetime import timedelta as _cic_v45_timedelta

def _now() -> datetime:
    return datetime.now()

def _dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)

def _clean_ids(values: Any) -> list[int]:
    out: list[int] = []
    for v in values or []:
        try:
            iv = int(v)
            if iv not in out:
                out.append(iv)
        except Exception:
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/corporate_information_center.py:284")
    return out

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

def _cic_auto_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "on", "yes", "aktif", "evet", "checked"}

def _cic_is_weekend(dt: _cic_dt_datetime) -> bool:
    # Python weekday: Monday=0 ... Sunday=6
    return dt.weekday() >= 5

def _cic_weekday_name_tr(dt: _cic_dt_datetime) -> str:
    names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    try:
        return names[dt.weekday()]
    except Exception:
        return "Bilinmiyor"

def _cic_v40_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "on", "yes", "evet", "aktif", "checked"}

def _cic_v40_parse_date(value: object) -> _cic_v40_date | None:
    if value is None:
        return None
    if isinstance(value, _cic_v40_datetime):
        return value.date()
    if isinstance(value, _cic_v40_date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return _cic_v40_datetime.strptime(text, fmt).date()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
    return None

def _cic_v40_today(now: object = None) -> _cic_v40_date:
    if isinstance(now, _cic_v40_datetime):
        return now.date()
    if isinstance(now, _cic_v40_date):
        return now
    try:
        return _now().date()
    except Exception:
        return _cic_v40_date.today()

def _cic_v40_mmdd(d: _cic_v40_date | None) -> str:
    return d.strftime("%m-%d") if d else ""

def _cic_v40_days_until(month_day: str, today: _cic_v40_date | None = None) -> int | None:
    today = today or _cic_v40_today()
    try:
        month, day = [int(x) for x in month_day.split("-", 1)]
        target = _cic_v40_date(today.year, month, day)
        if target < today:
            target = _cic_v40_date(today.year + 1, month, day)
        return (target - today).days
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None

def _cic_v45_text(value: object) -> str:
    return "" if value is None else str(value).strip()

def _cic_v45_norm(value: object) -> str:
    text = _cic_v45_text(value).lower()
    repl = str.maketrans({"ı":"i","İ":"i","ğ":"g","Ğ":"g","ü":"u","Ü":"u","ş":"s","Ş":"s","ö":"o","Ö":"o","ç":"c","Ç":"c"})
    text = text.translate(repl)
    text = _cic_v45_unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not _cic_v45_unicodedata.combining(ch))
    return _cic_v45_re.sub(r"[^a-z0-9]+", "", text)

def _cic_v45_norm_name(value: object) -> str:
    text = _cic_v45_text(value).lower()
    repl = str.maketrans({"ı":"i","İ":"i","ğ":"g","Ğ":"g","ü":"u","Ü":"u","ş":"s","Ş":"s","ö":"o","Ö":"o","ç":"c","Ç":"c"})
    text = text.translate(repl)
    return _cic_v45_re.sub(r"\s+", " ", _cic_v45_re.sub(r"[^a-z0-9 ]+", " ", text)).strip()

def _cic_v45_bool(value: object) -> bool | None:
    raw = _cic_v45_text(value)
    if not raw:
        return None
    text = _cic_v45_norm(raw)
    if text in {"1","true","evet","e","yes","y","aktif","pasifdegil","kutlamadisi","harictut"}:
        return True
    if text in {"0","false","hayir","h","no","n","pasif","yok"}:
        return False
    return None

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

def _cic_v45_header_key(value: object) -> str | None:
    h = _cic_v45_norm(value)
    mapping = {
        "sicilno":"sicil_no", "sicil":"sicil_no", "personelsicilno":"sicil_no", "kurumsicilno":"sicil_no",
        "adsoyad":"ad_soyad", "adisoyadi":"ad_soyad", "adsoyadi":"ad_soyad", "personel":"ad_soyad", "ad":"ad", "soyad":"soyad",
        "eposta":"email", "email":"email", "mail":"email", "kurummail":"email", "kurumeposta":"email",
        "dogumtarihi":"birth_date", "dogumgunu":"birth_date", "birthdate":"birth_date", "birthday":"birth_date",
        "isebaslamatarihi":"hire_date", "gorevebaslamatarihi":"hire_date", "baslamatarihi":"hire_date", "hizmetbaslangic":"hire_date", "hiredate":"hire_date",
        "kutlamadisi":"celebration_opt_out", "kutlamaharic":"celebration_opt_out", "kutlamaistemiyor":"celebration_opt_out", "optout":"celebration_opt_out",
        "not":"note", "aciklama":"note",
    }
    return mapping.get(h)

# --- BYS360 P6 migrated low-risk helpers: end ---


# --- BYS360 P7 migrated CIC settings repository helpers: start ---
# These settings repository helpers were migrated from app.services.corporate_information_center.
# The legacy module keeps import aliases for backwards compatibility.

from sqlalchemy import inspect as sa_inspect

from app.extensions import db
from app.models import SystemSetting

GROUP_KEY = "corporate_information_center"

def _has_settings_table() -> bool:
    try:
        return bool(sa_inspect(db.engine).has_table("system_settings"))
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False

def get_setting(key: str, default: str = "") -> str:
    if not _has_settings_table():
        return default
    row = SystemSetting.query.filter_by(setting_key=key).first()
    if not row:
        return default
    return row.value_text if row.value_text is not None else default

def set_setting(key: str, value: str, *, label: str | None = None, description: str | None = None, value_type: str = "string", actor_user_id: int | None = None) -> None:
    if not _has_settings_table():
        return
    row = SystemSetting.query.filter_by(setting_key=key).first()
    if not row:
        row = SystemSetting(setting_key=key, group_key=GROUP_KEY, label=label or key, value_type=value_type, description=description or "")
        db.session.add(row)
    row.value_text = value
    row.group_key = GROUP_KEY
    row.label = label or row.label or key
    row.value_type = value_type or row.value_type or "string"
    if description is not None:
        row.description = description
    if actor_user_id is not None:
        row.updated_by_user_id = actor_user_id

def _loads_json(key: str, default: Any) -> Any:
    raw = get_setting(key, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default

# --- BYS360 P7 migrated CIC settings repository helpers: end ---
