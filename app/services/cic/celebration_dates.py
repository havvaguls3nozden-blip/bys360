"""Canonical CIC celebration date and special-day helpers."""

from __future__ import annotations

from datetime import date, datetime

from app.services.cic.config_context import (
    _CIC_V40_SPECIAL_DAY_DEFAULTS,
    _loads_json,
    _now,
    get_setting,
)
from app.services.cic.task_contract import BASE_KEY

__all__ = [
    "_cic_v40_bool",
    "_cic_v40_parse_date",
    "_cic_v40_user_date",
    "_cic_v40_today",
    "_cic_v40_mmdd",
    "_cic_v40_setting_bool",
    "_cic_v40_special_days",
    "_cic_v40_special_days_today",
]

def _cic_v40_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "on", "yes", "evet", "aktif", "checked"}


def _cic_v40_parse_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2033")
            pass
    return None


def _cic_v40_user_date(user: object, *names: str) -> date | None:
    for name in names:
        try:
            value = getattr(user, name, None)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2042")
            value = None
        parsed = _cic_v40_parse_date(value)
        if parsed:
            return parsed
    return None


def _cic_v40_today(now: object = None) -> date:
    if isinstance(now, datetime):
        return now.date()
    if isinstance(now, date):
        return now
    try:
        return _now().date()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2057")
        return date.today()


def _cic_v40_mmdd(d: date | None) -> str:
    return d.strftime("%m-%d") if d else ""


def _cic_v40_setting_bool(name: str, default: bool = True) -> bool:
    return _cic_v40_bool(get_setting(f"{BASE_KEY}.{name}", "true" if default else "false"), default)


def _cic_v40_special_days() -> list[dict[str, object]]:
    data = _loads_json(f"{BASE_KEY}.special_days", _CIC_V40_SPECIAL_DAY_DEFAULTS)
    if not isinstance(data, list):
        return list(_CIC_V40_SPECIAL_DAY_DEFAULTS)
    out: list[dict[str, object]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        date_value = str(item.get("date") or "").strip()
        name = str(item.get("name") or "").strip()
        if not date_value or not name:
            continue
        out.append({
            "date": date_value,
            "name": name,
            "enabled": _cic_v40_bool(item.get("enabled"), True),
            "target": str(item.get("target") or "all_staff"),
        })
    return out or list(_CIC_V40_SPECIAL_DAY_DEFAULTS)


def _cic_v40_special_days_today(now: object = None) -> list[dict[str, object]]:
    today_key = _cic_v40_mmdd(_cic_v40_today(now))
    return [d for d in _cic_v40_special_days() if d.get("enabled") and str(d.get("date")) == today_key]
