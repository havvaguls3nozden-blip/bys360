
"""BYS360 performans puanlama zaman penceresi kuralı.

Kural:
- Performans dönemi devam ederken puanlama başlamaz.
- Puanlama başlangıcı dönem bitiş tarihinden sonra otomatik oluşur.
- Varsayılan başlangıç: dönem bitiş tarihinden sonraki gün 00:00.
- Dönem kaydında scoring_start_date / scoring_start_at alanı varsa yalnızca dönem sonrasına denk geliyorsa kullanılır.
- Eski kayıtta puanlama başlangıcı dönem içinde kaldıysa dönem bitişinden sonraki gün esas alınır.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Any

logger = logging.getLogger(__name__)

LOGGER = logging.getLogger(__name__)

BYS360_SCORING_AFTER_PERIOD_END_MARKER = "BYS360_PERFORMANCE_SCORING_AFTER_PERIOD_END_V1_2"


def _get_attr(obj: Any, *names: str) -> Any:
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name, None)
            if value not in (None, ""):
                return value
    return None


def _as_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(raw[:19] if "T" in raw else raw[:len(fmt)], fmt)
                return parsed
            except Exception as exc:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                LOGGER.warning("BYS360 scoring_window_policy işleminde yakalanan hata loglandı: %r", exc)
                continue
    return None


def period_end_datetime(period: Any) -> datetime | None:
    """Dönem bitiş tarihini güvenli şekilde okur."""
    return _as_datetime(_get_attr(period, "end_date", "ends_at", "period_end", "finish_date", "end_at"))


def _default_scoring_start(period: Any) -> datetime | None:
    end_dt = period_end_datetime(period)
    if not end_dt:
        return None
    return datetime.combine(end_dt.date() + timedelta(days=1), time.min)


def stored_scoring_start_datetime(period: Any) -> datetime | None:
    """Varsa dönem kaydındaki geçerli puanlama başlangıç tarihini okur."""
    stored = _as_datetime(_get_attr(period, "scoring_start_date", "scoring_start_at", "evaluation_start_date", "rating_start_date"))
    default_start = _default_scoring_start(period)
    if stored and default_start and stored < default_start:
        return None
    return stored


def calculate_scoring_start_datetime(period: Any) -> datetime | None:
    """Puanlama başlangıcını üretir: geçerli kayıtlı alan varsa onu, yoksa dönem bitişinden sonraki günü döndürür."""
    stored = stored_scoring_start_datetime(period)
    if stored:
        return stored
    return _default_scoring_start(period)


def scoring_start_display(period: Any) -> str:
    start_dt = calculate_scoring_start_datetime(period)
    if not start_dt:
        return "Dönem bitiş tarihi girilince otomatik oluşur"
    return start_dt.strftime("%d.%m.%Y %H:%M")


def is_before_scoring_start(period: Any, now: datetime | None = None) -> bool:
    """Bugün puanlama başlangıcından önceyse True döner."""
    start_dt = calculate_scoring_start_datetime(period)
    if not start_dt:
        return False
    current = now or datetime.now()
    return current < start_dt


def is_scoring_open(period: Any, now: datetime | None = None) -> bool:
    return not is_before_scoring_start(period, now=now)


def scoring_window_payload(period: Any, now: datetime | None = None) -> dict[str, Any]:
    start_dt = calculate_scoring_start_datetime(period)
    current = now or datetime.now()
    before_start = bool(start_dt and current < start_dt)
    return {
        "scoring_policy_marker": BYS360_SCORING_AFTER_PERIOD_END_MARKER,
        "scoring_start_at": start_dt.isoformat() if start_dt else None,
        "scoring_start_display": scoring_start_display(period),
        "scoring_allowed": not before_start,
        "scoring_blocked_reason": "Puanlama dönem bitişinden sonra başlayacaktır." if before_start else None,
    }


def apply_scoring_start_to_period(period: Any) -> bool:
    """Modelde uygun alan varsa otomatik başlangıç tarihini nesneye yazar.

    DB kolonunun olmadığı eski kurulumlarda hata vermez, sadece False döner.
    """
    start_dt = calculate_scoring_start_datetime(period)
    if not start_dt:
        return False
    for field in ("scoring_start_date", "scoring_start_at"):
        if hasattr(period, field):
            current = getattr(period, field, None)
            current_dt = _as_datetime(current)
            if current in (None, "") or (current_dt and current_dt < start_dt):
                setattr(period, field, start_dt)
                return True
    return False


__all__ = [
    "BYS360_SCORING_AFTER_PERIOD_END_MARKER",
    "calculate_scoring_start_datetime",
    "scoring_start_display",
    "is_before_scoring_start",
    "is_scoring_open",
    "scoring_window_payload",
    "apply_scoring_start_to_period",
]
