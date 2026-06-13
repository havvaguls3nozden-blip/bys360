from __future__ import annotations
import logging


logger = logging.getLogger(__name__)

# BYS360 P19B normalized CIC task-contract dependencies.
try:
    from app import db  # type: ignore
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=7")
    db = None  # type: ignore

try:
    from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS  # type: ignore
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=12")
    BASE_KEY = "corporate_information_center"
    TASK_DEFINITIONS = {}

try:
    from app.services.cic.repository import _clean_ids, _dumps_json, _now, set_setting  # type: ignore
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=18")
    pass


"""BYS360 CIC facade slice.

This module is intentionally facade-only in P5.
The legacy implementation remains in app.services.corporate_information_center.
Routes, template names, endpoint contracts and public function names are not changed.
"""

from typing import Any

from app.services import corporate_information_center as _legacy

__all__ = [
    "_cic_phase3_task_label",
    "_cic_phase5_mail_health",
    "_cic_phase5_task_preview",
    "_cic_phase6_missing_email_count",
    "_cic_v11_get_setting_value",
    "_cic_v11_mail_settings",
    "_cic_v11_normalize_email",
    "_cic_v11_send_email_direct",
    "_format_weather",
    "_recipients_for_task",
    "_weather",
    "ensure_defaults",
    "get_auto_scheduler_config",
    "get_config",
    "get_recipients",
    "get_setting",
    "run_due_tasks",
    "save_recipients",
    "save_system",
    "save_tasks",
    "send_task",
    "set_auto_scheduler_config",
    "set_setting",
]

def _cic_phase5_task_preview(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_phase5_task_preview``."""
    return _legacy._cic_phase5_task_preview(*args, **kwargs)

def _cic_v11_send_email_direct(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_cic_v11_send_email_direct``."""
    return _legacy._cic_v11_send_email_direct(*args, **kwargs)

def _recipients_for_task(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_recipients_for_task``."""
    return _legacy._recipients_for_task(*args, **kwargs)

def _weather(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``_weather``."""
    return _legacy._weather(*args, **kwargs)

def run_due_tasks(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``run_due_tasks``."""
    return _legacy.run_due_tasks(*args, **kwargs)

def save_system(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``save_system``."""
    return _legacy.save_system(*args, **kwargs)

def send_task(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``send_task``."""
    return _legacy.send_task(*args, **kwargs)

def set_auto_scheduler_config(*args: Any, **kwargs: Any) -> Any:
    """Facade wrapper for legacy ``set_auto_scheduler_config``."""
    return _legacy.set_auto_scheduler_config(*args, **kwargs)

# --- BYS360 P11 migrated CIC mail scheduler helpers: start ---
# Bu blok P11'de düşük riskli mail scheduler yardımcılarını legacy wrapper yerine
# gerçek CIC servis katmanına alır. Gönderim, scheduler ve DB yazma akışları bilinçli
# olarak bu fazda taşınmamıştır.
try:
    from flask import current_app as _p11_current_app
except Exception:  # pragma: no cover - Flask context optional in tooling
    logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=98")
    _p11_current_app = None  # type: ignore

from app.services.cic.repository import (
    get_setting,
    set_setting,
    _cic_v11_bool,
    _cic_v11_normalize_email,
)

try:
    from app.services.mail_core import send_email as _p11_send_email
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=110")
    _p11_send_email = None  # type: ignore

_p11_logger = logging.getLogger(__name__)
TASK_DEFINITIONS = TASK_DEFINITIONS or {}


def _p11_app_config() -> Any:
    try:
        return getattr(_p11_current_app, "config", {}) if _p11_current_app is not None else {}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=120")
        return {}


def _cic_phase3_task_label(task_key: str) -> str:
    meta = TASK_DEFINITIONS.get(task_key) or {}
    return meta.get("label") or task_key


def _cic_phase5_mail_health() -> dict[str, Any]:
    cfg = _p11_app_config()
    server = (cfg.get("MAIL_SERVER") or cfg.get("SMTP_SERVER") or "").strip() if hasattr(cfg, "get") else ""
    sender = (cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("DEFAULT_MAIL_SENDER") or cfg.get("MAIL_USERNAME") or "").strip() if hasattr(cfg, "get") else ""
    username = (cfg.get("MAIL_USERNAME") or "").strip() if hasattr(cfg, "get") else ""
    suppressed = bool(cfg.get("MAIL_SUPPRESS_SEND", False)) if hasattr(cfg, "get") else False
    problems: list[str] = []
    if not server:
        problems.append("Mail sunucusu tanımlı değil")
    if not sender:
        problems.append("Gönderici e-posta tanımlı değil")
    if suppressed:
        problems.append("Mail gönderimi bastırılmış durumda")
    if _p11_send_email is None:
        problems.append("Mail gönderim servisi yüklenemedi")
    status = "ok" if not problems else ("warn" if server or sender else "danger")
    return {
        "status": status,
        "server_defined": bool(server),
        "sender_defined": bool(sender),
        "username_defined": bool(username),
        "suppressed": suppressed,
        "service_loaded": _p11_send_email is not None,
        "label": "Hazır" if status == "ok" else "Kontrol gerekli",
        "problems": problems,
    }


def _cic_phase6_missing_email_count(users: list[Any]) -> int:
    total = 0
    for user in users or []:
        try:
            if not (getattr(user, "email", "") or "").strip():
                total += 1
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=163")
            total += 1
    return total


def _cic_v11_get_setting_value(keys: Any, default: Any = "") -> Any:
    cfg = _p11_app_config()
    for key in keys or []:
        try:
            value = cfg.get(key) if hasattr(cfg, "get") else None
            if value is not None and str(value).strip() != "":
                return value
        except Exception as exc:
            _p11_logger.debug("CIC config read skipped for %s: %s", key, exc)

    for key in keys or []:
        try:
            value = get_setting(str(key), "")
            if value is not None and str(value).strip() != "":
                return value
        except Exception as exc:
            _p11_logger.debug("CIC setting read skipped for %s: %s", key, exc)

    aliases: list[str] = []
    for key in keys or []:
        text = str(key).lower()
        aliases.extend([text, text.replace("_", "."), text.replace("_", "-")])
    for key in aliases:
        try:
            value = get_setting(key, "")
            if value is not None and str(value).strip() != "":
                return value
        except Exception as exc:
            _p11_logger.debug("CIC alias setting read skipped for %s: %s", key, exc)
    return default


def _cic_v11_mail_settings() -> dict[str, Any]:
    server = _cic_v11_get_setting_value(["MAIL_SERVER", "SMTP_SERVER", "mail_server", "smtp_server", "corporate_information_center.mail_server", "corporate_information_center.smtp_server"], "")
    port = _cic_v11_get_setting_value(["MAIL_PORT", "SMTP_PORT", "mail_port", "smtp_port", "corporate_information_center.mail_port", "corporate_information_center.smtp_port"], 587)
    username = _cic_v11_get_setting_value(["MAIL_USERNAME", "SMTP_USERNAME", "mail_username", "smtp_username", "corporate_information_center.mail_username", "corporate_information_center.smtp_username"], "")
    password = _cic_v11_get_setting_value(["MAIL_PASSWORD", "SMTP_PASSWORD", "mail_password", "smtp_password", "corporate_information_center.mail_password", "corporate_information_center.smtp_password"], "")
    sender = _cic_v11_get_setting_value(["MAIL_DEFAULT_SENDER", "SMTP_SENDER", "MAIL_SENDER", "mail_default_sender", "mail_sender", "smtp_sender", "corporate_information_center.mail_sender", "corporate_information_center.smtp_sender"], "") or username
    use_tls = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_USE_TLS", "SMTP_USE_TLS", "mail_use_tls", "smtp_use_tls", "corporate_information_center.mail_use_tls"], True), True)
    use_ssl = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_USE_SSL", "SMTP_USE_SSL", "mail_use_ssl", "smtp_use_ssl", "corporate_information_center.mail_use_ssl"], False), False)
    suppress = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_SUPPRESS_SEND", "mail_suppress_send", "corporate_information_center.mail_suppress_send"], False), False)
    try:
        port = int(str(port).strip())
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=211")
        port = 587
    return {
        "server": str(server or "").strip(),
        "port": port,
        "username": str(username or "").strip(),
        "password": password or "",
        "sender": str(sender or "").strip(),
        "use_tls": bool(use_tls),
        "use_ssl": bool(use_ssl),
        "suppress_send": bool(suppress),
    }


def _format_weather(current_temp: Any, daily: dict[str, Any], idx: int) -> str:
    mins = daily.get("temperature_2m_min") or []
    maxs = daily.get("temperature_2m_max") or []
    probs = daily.get("precipitation_probability_max") or []
    parts: list[str] = []
    if current_temp is not None:
        parts.append(f"Anlık sıcaklık: {current_temp}°C")
    if idx < len(mins) and idx < len(maxs):
        parts.append(f"Beklenen aralık: {mins[idx]}°C / {maxs[idx]}°C")
    if idx < len(probs):
        parts.append(f"Yağış olasılığı: %{probs[idx]}")
    return "\n".join(parts) if parts else "Hava durumu verisi sınırlı olarak alınabildi."

# --- BYS360 P11 migrated CIC mail scheduler helpers: end ---

# --- BYS360 P13A migrated CIC mail scheduler read/config helpers: start ---
# Bu blok yalnızca okuma/hazırlık fonksiyonlarını taşır. Mail gönderimi,
# otomatik scheduler çalıştırma ve form kaydetme fonksiyonları P13A kapsamı dışındadır.
from app import db as _p13_db
from app.services.cic.repository import (
    get_setting as _p13_get_setting,
    set_setting as _p13_set_setting,
    _loads_json as _p13_loads_json,
    _dumps_json as _p13_dumps_json,
    _clean_ids as _p13_clean_ids,
    _cic_auto_bool as _p13_auto_bool,
)
from app.services.cic.query_service import (
    _users_by_ids as _p13_users_by_ids,
    _active_staff_users as _p13_active_staff_users,
)

_p13_BASE_KEY = BASE_KEY
_p13_TASK_DEFINITIONS = TASK_DEFINITIONS or {} or {}
_p13_SPECIAL_DAY_DEFAULTS = getattr(_legacy, "_CIC_V40_SPECIAL_DAY_DEFAULTS", []) or []


def _p13_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        out = int(value)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=265")
        out = default
    return max(minimum, min(maximum, out))


def ensure_defaults(actor_user_id: int | None = None) -> None:
    tasks = _p13_loads_json(f"{_p13_BASE_KEY}.tasks", None)
    if not isinstance(tasks, dict):
        tasks = {}
    changed = False

    for key, meta in _p13_TASK_DEFINITIONS.items():
        if not isinstance(meta, dict):
            continue
        if key not in tasks or not isinstance(tasks.get(key), dict):
            tasks[key] = {
                "enabled": True,
                "hour": meta.get("default_hour", 9),
                "minute": meta.get("default_minute", 0),
                "recipient_group": meta.get("recipient_group", "staff"),
                "last_status": "Henüz çalışmadı",
                "last_run_at": "",
            }
            changed = True
        else:
            for field, default in (
                ("enabled", True),
                ("hour", meta.get("default_hour", 9)),
                ("minute", meta.get("default_minute", 0)),
                ("recipient_group", meta.get("recipient_group", "staff")),
            ):
                if field not in tasks[key]:
                    tasks[key][field] = default
                    changed = True
    if changed:
        _p13_set_setting(
            f"{_p13_BASE_KEY}.tasks",
            _p13_dumps_json(tasks),
            label="Kurumsal bilgilendirme görevleri",
            value_type="json",
            actor_user_id=actor_user_id,
        )

    scalar_defaults: list[tuple[str, str, str, str]] = [
        ("staff_recipient_mode", "manual", "Personel alıcı modu", "string"),
        ("manager_recipient_ids", "[]", "Yönetici alıcıları", "json"),
        ("staff_recipient_ids", "[]", "Personel alıcıları", "json"),
        ("location_name", "Çanakkale", "Hava durumu konumu", "string"),
        ("latitude", "40.1553", "Enlem", "string"),
        ("longitude", "26.4142", "Boylam", "string"),
        ("auto_scheduler_enabled", "false", "Otomatik mail zamanlayıcı", "boolean"),
        ("auto_scheduler_weekdays_only", "true", "Otomatik mail yalnızca hafta içi", "boolean"),
        ("auto_scheduler_late_window_minutes", "20", "Otomatik mail gecikme toleransı", "integer"),
        ("celebrations_enabled", "true", "Akıllı kutlama motoru", "boolean"),
        ("birthday_enabled", "true", "Doğum günü kutlamaları", "boolean"),
        ("work_anniversary_enabled", "true", "Göreve başlama yıl dönümü kutlamaları", "boolean"),
        ("special_day_enabled", "true", "Özel gün bilgilendirmeleri", "boolean"),
        ("celebration_system_notifications_enabled", "true", "Kutlamaları sistem içi bildirim olarak da oluştur", "boolean"),
        ("celebrations_include_weekend", "false", "Hafta sonu kutlamaları otomatik çalışsın", "boolean"),
        ("special_day_recipient_mode", "all_active", "Özel gün hedef kitlesi", "string"),
    ]
    for key, value, label, value_type in scalar_defaults:
        full_key = f"{_p13_BASE_KEY}.{key}"
        if _p13_get_setting(full_key, "") == "":
            _p13_set_setting(full_key, value, label=label, value_type=value_type, actor_user_id=actor_user_id)
            changed = True

    special_days_key = f"{_p13_BASE_KEY}.special_days"
    if _p13_get_setting(special_days_key, "") == "":
        _p13_set_setting(
            special_days_key,
            _p13_dumps_json(_p13_SPECIAL_DAY_DEFAULTS),
            label="Özel gün takvimi",
            value_type="json",
            actor_user_id=actor_user_id,
        )
        changed = True

    for key, meta in _p13_TASK_DEFINITIONS.items():
        if not isinstance(meta, dict):
            continue
        label = meta.get("label") or key
        subject_key = f"{_p13_BASE_KEY}.template.{key}.subject"
        body_key = f"{_p13_BASE_KEY}.template.{key}.body"
        if _p13_get_setting(subject_key, "") == "":
            _p13_set_setting(subject_key, str(meta.get("subject") or ""), label=f"{label} konusu", actor_user_id=actor_user_id)
            changed = True
        if _p13_get_setting(body_key, "") == "":
            _p13_set_setting(body_key, str(meta.get("body") or ""), label=f"{label} metni", value_type="text", actor_user_id=actor_user_id)
            changed = True

    if changed:
        try:
            _p13_db.session.commit()
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=359")
            _p13_db.session.rollback()


def get_auto_scheduler_config() -> dict[str, object]:
    enabled_raw = _p13_get_setting(f"{_p13_BASE_KEY}.auto_scheduler_enabled", "false") or "false"
    weekdays_raw = _p13_get_setting(f"{_p13_BASE_KEY}.auto_scheduler_weekdays_only", "true") or "true"
    late_window = _p13_int(
        _p13_get_setting(f"{_p13_BASE_KEY}.auto_scheduler_late_window_minutes", "20") or "20",
        default=20,
        minimum=1,
        maximum=120,
    )
    return {
        "enabled": _p13_auto_bool(enabled_raw, default=False),
        "weekdays_only": _p13_auto_bool(weekdays_raw, default=True),
        "late_window_minutes": late_window,
        "windows_task_name": "BYS360 CIC Auto Mail Scheduler",
        "poll_interval_minutes": 5,
        "description": "Windows görevi yalnızca yoklama yapar; hangi mailin aktif/pasif olduğu, saati ve hafta içi kuralı BYS360 ekranlarından yönetilir.",
        "weekend_policy": "Cumartesi ve pazar günleri otomatik mail gönderilmez.",
    }


def get_config() -> dict[str, Any]:
    ensure_defaults()
    return {
        "tasks": _p13_loads_json(f"{_p13_BASE_KEY}.tasks", {}),
        "staff_recipient_mode": _p13_get_setting(f"{_p13_BASE_KEY}.staff_recipient_mode", "manual") or "manual",
        "manager_recipient_ids": _p13_clean_ids(_p13_loads_json(f"{_p13_BASE_KEY}.manager_recipient_ids", [])),
        "staff_recipient_ids": _p13_clean_ids(_p13_loads_json(f"{_p13_BASE_KEY}.staff_recipient_ids", [])),
        "location_name": _p13_get_setting(f"{_p13_BASE_KEY}.location_name", "Çanakkale") or "Çanakkale",
        "latitude": _p13_get_setting(f"{_p13_BASE_KEY}.latitude", "40.1553") or "40.1553",
        "longitude": _p13_get_setting(f"{_p13_BASE_KEY}.longitude", "26.4142") or "26.4142",
        "auto_scheduler": get_auto_scheduler_config(),
    }


def get_recipients() -> dict[str, Any]:
    cfg = get_config()
    managers = _p13_users_by_ids(cfg.get("manager_recipient_ids", []))
    if cfg.get("staff_recipient_mode") == "all_active":
        staff = _p13_active_staff_users()
    else:
        staff = _p13_users_by_ids(cfg.get("staff_recipient_ids", []))
    return {"managers": managers, "staff": staff, "staff_mode": cfg.get("staff_recipient_mode", "manual")}

# --- BYS360 P13A migrated CIC mail scheduler read/config helpers: end ---

# BYS360_REPO_HYGIENE_P13B_FORM_SAVE_MIGRATION_APPLIED
def save_tasks(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    cfg = get_config()
    tasks = cfg["tasks"]
    for key, meta in TASK_DEFINITIONS.items():
        t = tasks.setdefault(key, {})
        t["enabled"] = str(payload.get(f"enabled_{key}", "")).lower() in {"1", "true", "on", "yes"}
        try:
            t["hour"] = max(0, min(23, int(payload.get(f"hour_{key}", meta["default_hour"]))))
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=417")
            t["hour"] = meta["default_hour"]
        try:
            t["minute"] = max(0, min(59, int(payload.get(f"minute_{key}", meta["default_minute"]))))
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=421")
            t["minute"] = meta["default_minute"]
        t["recipient_group"] = meta["recipient_group"]
    set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
    db.session.commit()

def save_recipients(payload: dict[str, Any], actor_user_id: int | None = None) -> None:  # noqa: F811
    def getlist_all(*names: str) -> list[Any]:
        values: list[Any] = []
        for name in names:
            try:
                if hasattr(payload, "getlist"):
                    part = payload.getlist(name)
                else:
                    raw = payload.get(name, []) if hasattr(payload, "get") else []
                    part = raw if isinstance(raw, list) else ([raw] if raw else [])
            except Exception:
                logger.exception("BYS360 V6C guarded exception | file=app/services/cic/mail_scheduler_service.py | line=437")
                part = []
            for item in part or []:
                if item not in values:
                    values.append(item)
        return values

    manager_ids = _clean_ids(getlist_all("manager_ids", "manager_user_ids", "manager_recipient_ids", "selected_manager_ids"))
    staff_ids = _clean_ids(getlist_all("staff_ids", "staff_user_ids", "staff_recipient_ids", "selected_staff_ids"))
    mode = str(payload.get("staff_recipient_mode") or "manual").strip() if hasattr(payload, "get") else "manual"
    if mode not in {"manual", "all_active"}:
        mode = "manual"

    set_setting(f"{BASE_KEY}.manager_recipient_ids", _dumps_json(manager_ids), label="Yönetici alıcıları", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.staff_recipient_ids", _dumps_json(staff_ids), label="Personel alıcıları", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.staff_recipient_mode", mode, label="Personel alıcı modu", value_type="string", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_recipient_save_summary", _dumps_json({"manager_count": len(manager_ids), "staff_count": len(staff_ids), "mode": mode}), label="Son alıcı kayıt özeti", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_recipient_save_at", _now().isoformat(timespec="seconds"), label="Son alıcı kayıt zamanı", value_type="string", actor_user_id=actor_user_id)
    db.session.commit()
