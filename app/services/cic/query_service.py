"""Canonical CIC personnel and recipient query service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_

from app.models import User
from app.services.cic.config_context import get_setting
from app.services.cic.task_contract import BASE_KEY

__all__ = [
    "_active_staff_users",
    "_cic_v40_active_staff_candidates",
    "_cic_v40_special_day_users",
    "_cic_v40_upcoming_users",
    "_users_by_ids",
    "list_users",
]


def list_users(search: str | None = None, limit: int = 800) -> list[User]:
    q = User.query
    if hasattr(User, "is_active"):
        try:
            q = q.filter(User.is_active.is_(True))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:354")
            pass
    if search:
        s = f"%{search.strip()}%"
        clauses = []
        for attr in ("ad", "soyad", "email", "sicil_no", "birim", "ust_birim", "unvan", "role_label", "username"):
            col = getattr(User, attr, None)
            if col is not None and hasattr(col, "ilike"):
                clauses.append(col.ilike(s))
        if clauses:
            q = q.filter(or_(*clauses))
    # Güvenli sıralama: full_name/ad gibi property olabilecek alanlar order_by içinde kullanılmaz.
    try:
        return q.order_by(User.id.asc()).limit(limit).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:365")
        return q.limit(limit).all()


def _users_by_ids(ids: list[int]) -> list[User]:
    if not ids:
        return []
    rows = User.query.filter(User.id.in_(ids)).all()
    order = {uid: idx for idx, uid in enumerate(ids)}
    return sorted(rows, key=lambda u: order.get(getattr(u, "id", 0), 999999))


def _active_staff_users() -> list[User]:
    q = User.query
    if hasattr(User, "is_active"):
        try:
            q = q.filter(User.is_active.is_(True))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:386")
            pass
    if hasattr(User, "email"):
        q = q.filter(User.email.isnot(None), User.email != "")
    try:
        return q.order_by(User.id.asc()).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:388")
        return q.all()


def _cic_v40_active_staff_candidates() -> list[User]:
    try:
        users = _active_staff_users()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2175")
        users = []
    clean: list[User] = []
    for user in users or []:
        if bool(getattr(user, "celebration_opt_out", False)):
            continue
        clean.append(user)
    return clean


def _cic_v40_special_day_users(now: object = None) -> list[User]:
    from app.services.cic.celebration_dates import (
        _cic_v40_setting_bool,
        _cic_v40_special_days_today,
    )
    from app.services.cic.mail_service import get_recipients

    if not _cic_v40_setting_bool("celebrations_enabled", True) or not _cic_v40_setting_bool("special_day_enabled", True):
        return []
    if not _cic_v40_special_days_today(now):
        return []
    mode = get_setting(f"{BASE_KEY}.special_day_recipient_mode", "all_active") or "all_active"
    if mode == "manual":
        try:
            return list(get_recipients().get("staff") or [])
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2229")
            return []
    return _cic_v40_active_staff_candidates()


def _cic_v40_upcoming_users(kind: str, days: int = 30) -> list[dict[str, Any]]:
    from app.services.cic.celebration_dates import (
        _cic_v40_days_until,
        _cic_v40_mmdd,
        _cic_v40_today,
        _cic_v40_user_date,
    )
    from app.services.cic.celebration_service import (
        _cic_v40_service_year,
    )

    today = _cic_v40_today()
    rows: list[dict[str, Any]] = []
    for user in _cic_v40_active_staff_candidates():
        if kind == "birthday":
            d = _cic_v40_user_date(user, "birth_date", "dogum_tarihi", "date_of_birth")
        else:
            d = _cic_v40_user_date(user, "hire_date", "goreve_baslama_tarihi", "ise_baslama_tarihi", "start_date")
        if not d:
            continue
        left = _cic_v40_days_until(_cic_v40_mmdd(d), today)
        if left is None or left > days:
            continue
        row: dict[str, Any] = {"user": user, "date": d, "days_left": left}
        if kind == "anniversary":
            row["service_year"] = _cic_v40_service_year(user, today)
            if int(row["service_year"] or 0) <= 0:
                continue
        rows.append(row)
    return sorted(rows, key=lambda x: int(x.get("days_left") or 0))
