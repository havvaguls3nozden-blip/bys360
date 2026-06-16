from __future__ import annotations

from app.institutional.hr_common import (
    utc_now,
    date,
    datetime,
    timedelta,
    import_module,
    SimpleNamespace,
    Any,
    Iterable,
    csv,
    io,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    request,
    url_for,
    current_user,
    login_required,
    inspect,
    or_,
    BuildError,
    db,
    main_bp,
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
    LEGACY_SHIM,
    LEGACY_RUNTIME_STATUS,
    LEGACY_ROUTE_FAMILY,
    LEGACY_NOTE,
    LEAVE_TYPE_CHOICES,
    LEAVE_STATUS_CHOICES,
    ATTENDANCE_TYPE_CHOICES,
    DELEGATION_SCOPE_CHOICES,
    DELEGATION_STATUS_CHOICES,
    PERFORMANCE_MODE_LABELS,
    ACTIVE_STATUSES,
    PENDING_STATUSES,
    _safe_import,
    _endpoint_registered,
    _url_or_hash,
    _table_exists,
    _model_ready,
    _safe_text,
    _safe_int,
    _safe_float,
    _current_user_id,
    _safe_commit,
    _resolve_period_id_from_form,
    _date_range_weekday_count,
    _calculate_leave_day_count,
    _active_delegation_exists,
    _leave_overlaps,
    _attendance_overlaps,
    _bool_from_form,
    _active_period,
    _parse_date,
    AttendanceException,
    DelegationAssignment,
    PerformancePeriod,
    PersonnelLeave,
    User,
    build_leave_delegation_health_snapshot,
    build_leave_overview,
    build_user_scope_context,
)

def _parse_date(value: Any) -> date | None:
    raw = _safe_text(value)
    if not raw:
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_scope_helpers.py:13")
        return None


def _bool_from_form(name: str, default: bool = False) -> bool:
    if name not in request.form:
        return default
    return _safe_text(request.form.get(name)).lower() in {"1", "true", "on", "yes", "evet", "aktif"}


def _status_label(value: Any) -> str:
    raw = _safe_text(value, "-").replace("_", " ")
    return raw.title() if raw != "-" else "-"


def _scope_label(value: Any) -> str:
    raw = _safe_text(value, "performance").lower()
    return dict(DELEGATION_SCOPE_CHOICES).get(raw, raw.replace("_", " ").title())


def _leave_type_label(value: Any) -> str:
    raw = _safe_text(value).lower()
    return dict(LEAVE_TYPE_CHOICES).get(raw, raw.replace("_", " ").title() if raw else "-")


def _attendance_type_label(value: Any) -> str:
    raw = _safe_text(value).lower()
    return dict(ATTENDANCE_TYPE_CHOICES).get(raw, raw.replace("_", " ").title() if raw else "-")


def _performance_mode_label(value: Any) -> str:
    raw = _safe_text(value, "partial").lower()
    return PERFORMANCE_MODE_LABELS.get(raw, raw.replace("_", " ").title())


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    value = _safe_text(getattr(user, "full_name", None) or getattr(user, "full_name_cache", None))
    if value:
        return value
    return f"{_safe_text(getattr(user, 'ad', None))} {_safe_text(getattr(user, 'soyad', None))}".strip() or "-"


def _unit_name(user: Any) -> str:
    return _safe_text(getattr(user, "birim", None) or getattr(user, "ust_birim", None), "Belirsiz birim")


def _role_key(user: Any) -> str:
    return _safe_text(getattr(user, "role", None)).lower()


def _profile_missing_fields(user: Any) -> list[str]:
    if not user:
        return []
    checks = [
        ("Ad", bool(_safe_text(getattr(user, "ad", None)))),
        ("Soyad", bool(_safe_text(getattr(user, "soyad", None)))),
        ("Sicil No", bool(_safe_text(getattr(user, "sicil_no", None)))),
        ("E-posta", bool(_safe_text(getattr(user, "email", None)))),
        ("Unvan", bool(_safe_text(getattr(user, "unvan", None)))),
        ("Birim", bool(_safe_text(getattr(user, "birim", None)))),
        ("Üst Birim", bool(_safe_text(getattr(user, "ust_birim", None)))),
        ("1. Amir", bool(_safe_text(getattr(user, "yonetici_sicil", None))) or _role_key(user) in {"admin", "baskan"}),
    ]
    return [label for label, ok in checks if not ok]


def _profile_score(user: Any) -> int:
    total = 8
    missing = len(_profile_missing_fields(user))
    return int(round(((total - missing) / total) * 100)) if total else 0


def _active_period() -> Any | None:
    if not _model_ready(PerformancePeriod):
        return None
    try:
        return PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc()).first()
    except Exception:
        safe_db_rollback()
        return None


def _period_options() -> list[Any]:
    if not _model_ready(PerformancePeriod):
        return []
    try:
        return PerformancePeriod.query.order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc()).limit(36).all()
    except Exception:
        safe_db_rollback()
        return []


def _selected_period_id() -> int | None:
    return _safe_int(request.args.get("period_id") or request.form.get("period_id"))


def _selected_user_id() -> int | None:
    return _safe_int(request.args.get("user_id") or request.form.get("user_id"))


def _all_personnel() -> list[Any]:
    if not _model_ready(User):
        return []
    try:
        query = User.query
        if hasattr(User, "is_active"):
            query = query.filter(User.is_active.is_(True))
        return query.order_by(getattr(User, "ad", User.id).asc(), getattr(User, "soyad", User.id).asc(), User.id.asc()).all()
    except Exception:
        safe_db_rollback()
        return []


def _requested_scope_mode() -> str | None:
    raw = _safe_text(request.args.get("scope") or request.form.get("scope")).lower()
    return raw or None


def _fallback_scope_context() -> dict[str, Any]:
    users = _all_personnel()
    role = _role_key(current_user)
    is_manager = role in {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"}
    requested = _requested_scope_mode() or ("all" if role in {"admin", "baskan", "baskan_yardimcisi"} else "unit" if is_manager else "personal")
    if requested not in {"personal", "unit", "all"}:
        requested = "personal"
    if requested == "all" and role not in {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}:
        requested = "unit" if is_manager else "personal"
    current_id = getattr(current_user, "id", None)
    current_unit = _unit_name(current_user)
    if requested == "all":
        scoped = users
        label = "Tüm kurum"
        heading = "Kurumsal görünüm"
    elif requested == "unit":
        scoped = [u for u in users if _unit_name(u) == current_unit]
        if current_id and not any(getattr(u, "id", None) == current_id for u in scoped):
            scoped.append(current_user)
        label = current_unit
        heading = "Birim görünümü"
    else:
        scoped = [u for u in users if getattr(u, "id", None) == current_id] or ([current_user] if current_id else [])
        label = _full_name(current_user)
        heading = "Kişisel görünüm"
    options = [{"value": "personal", "label": "Kişisel"}]
    if is_manager:
        options.append({"value": "unit", "label": "Birimim"})
    if role in {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}:
        options.append({"value": "all", "label": "Tüm kurum"})
    unit_count = len({_unit_name(u) for u in scoped})
    return {
        "scope_mode": requested,
        "scope_label": label,
        "scope_heading": heading,
        "scope_description": "Canlı çekirdek kapsam görünümü",
        "scope_user_ids": [int(getattr(u, "id")) for u in scoped if getattr(u, "id", None)],
        "scope_user_count": len(scoped),
        "scope_unit_count": unit_count,
        "scope_options": options,
        "role_title": _safe_text(getattr(current_user, "role_label", None) or getattr(current_user, "role", None), "Kapsam"),
    }


def _hr_scope_context() -> dict[str, Any]:
    if build_user_scope_context is not None:
        try:
            ctx = build_user_scope_context(current_user, _requested_scope_mode()) or {}
            fallback = _fallback_scope_context()
            for key, value in fallback.items():
                ctx.setdefault(key, value)
            if not ctx.get("scope_options"):
                ctx["scope_options"] = fallback["scope_options"]
            return ctx
        except Exception:
            safe_db_rollback()
    return _fallback_scope_context()


def _scope_user_ids(scope: dict[str, Any] | None) -> list[int]:
    return [int(v) for v in (scope or {}).get("scope_user_ids", []) if str(v).strip().isdigit()]


def _filter_users_in_scope(users: Iterable[Any], scope: dict[str, Any] | None) -> list[Any]:
    ids = set(_scope_user_ids(scope))
    rows = [u for u in list(users or []) if not ids or getattr(u, "id", None) in ids]
    return sorted(rows, key=lambda u: (_full_name(u).lower(), int(getattr(u, "id", 0) or 0)))


def _scope_bundle() -> tuple[dict[str, Any], list[Any], list[int]]:
    scope = _hr_scope_context()
    users = _filter_users_in_scope(_all_personnel(), scope)
    ids = [int(getattr(u, "id")) for u in users if getattr(u, "id", None)]
    return scope, users, ids


def _empty_overview() -> SimpleNamespace:
    return SimpleNamespace(
        available=False,
        current_year=date.today().year,
        policy_rows=[],
        balance_rows=[],
        pending_requests=[],
        active_delegations=[],
        attendance_rows=[],
        summary={"policy_count": 0, "balance_count": 0, "pending_count": 0, "delegation_count": 0, "attendance_count": 0},
        notes=["İzin, devamsızlık ve vekâlet tabloları hazır olduğunda bu ekran canlı veriyi gösterecek."],
    )


def _leave_overview() -> Any:
    if build_leave_overview is not None:
        try:
            return build_leave_overview(current_year=date.today().year)
        except Exception:
            safe_db_rollback()
    return _empty_overview()


def _delegation_health(period_id: int | None = None) -> dict[str, Any]:
    if build_leave_delegation_health_snapshot is not None:
        try:
            return build_leave_delegation_health_snapshot(period_id=period_id)
        except Exception:
            safe_db_rollback()
    return {
        "available": _model_ready(DelegationAssignment),
        "reference_date": date.today().isoformat(),
        "period_id": period_id,
        "period_title": None,
        "active_delegation_count": 0,
        "delegated_open_assignments": 0,
        "open_assignment_count": 0,
        "coverage_summary": {"uncovered": 0, "delegated": 0, "exempted": 0, "chain_issue": 0, "info": 0, "warning": 0, "error": 0},
        "notes": [],
    }


def _query_rows(model: Any, *, scope_user_ids: list[int] | None = None, date_field: str | None = None, desc: bool = True, limit: int = 50) -> list[Any]:
    if not _model_ready(model):
        return []
    try:
        q = model.query
        if scope_user_ids and hasattr(model, "user_id"):
            q = q.filter(model.user_id.in_(scope_user_ids))
        order_col = getattr(model, date_field, None) if date_field else getattr(model, "id", None)
        if order_col is not None:
            q = q.order_by(order_col.desc() if desc else order_col.asc(), model.id.desc())
        return q.limit(limit).all()
    except Exception:
        safe_db_rollback()
        return []


def _count_rows(model: Any, *filters: Any) -> int:
    if not _model_ready(model):
        return 0
    try:
        q = model.query
        for item in filters:
            q = q.filter(item)
        return int(q.count() or 0)
    except Exception:
        safe_db_rollback()
        return 0


def _selected_user_guard(user_id: int | None, period: Any | None = None) -> dict[str, Any]:
    if not user_id or not _model_ready(User):
        return {"is_manager": False, "requires_delegation": False, "has_covering_delegation": False, "coverage": {"total": 0, "level_1": 0, "level_2": 0, "level_3": 0}}
    try:
        user = db.session.get(User, int(user_id))
        sicil = _safe_text(getattr(user, "sicil_no", None))
        if not sicil:
            return {"is_manager": False, "requires_delegation": False, "has_covering_delegation": False, "coverage": {"total": 0, "level_1": 0, "level_2": 0, "level_3": 0}}
        base = User.query.filter(User.is_active.is_(True), User.id != user.id)
        level_1 = base.filter(User.yonetici_sicil == sicil).count() if hasattr(User, "yonetici_sicil") else 0
        level_2 = base.filter(User.ikinci_yonetici_sicil == sicil).count() if hasattr(User, "ikinci_yonetici_sicil") else 0
        level_3 = base.filter(User.ucuncu_yonetici_sicil == sicil).count() if hasattr(User, "ucuncu_yonetici_sicil") else 0
        total = int(level_1 or 0) + int(level_2 or 0) + int(level_3 or 0)
        today = date.today()
        has_covering = False
        if _model_ready(DelegationAssignment):
            has_covering = bool(
                DelegationAssignment.query.filter_by(delegator_user_id=user.id)
                .filter(DelegationAssignment.start_date <= today, DelegationAssignment.end_date >= today)
                .filter(DelegationAssignment.status.in_(["aktif", "onaylandi"]))
                .first()
            )
        return {
            "is_manager": total > 0,
            "requires_delegation": total > 0,
            "has_covering_delegation": has_covering,
            "coverage": {"total": total, "level_1": int(level_1 or 0), "level_2": int(level_2 or 0), "level_3": int(level_3 or 0)},
        }
    except Exception:
        safe_db_rollback()
        return {"is_manager": False, "requires_delegation": False, "has_covering_delegation": False, "coverage": {"total": 0, "level_1": 0, "level_2": 0, "level_3": 0}}


def _unit_pulse(scope_users: list[Any], scope_user_ids: list[int]) -> list[dict[str, Any]]:
    today = date.today()
    bucket: dict[str, dict[str, Any]] = {}
    for user in scope_users:
        name = _unit_name(user)
        row = bucket.setdefault(name, {"unit_name": name, "employee_count": 0, "leave_today": 0, "attendance_today": 0, "incomplete_profiles": 0, "risk_score": 0})
        row["employee_count"] += 1
        if _profile_missing_fields(user):
            row["incomplete_profiles"] += 1
    if _model_ready(PersonnelLeave) and scope_user_ids:
        try:
            leaves = PersonnelLeave.query.filter(PersonnelLeave.user_id.in_(scope_user_ids), PersonnelLeave.start_date <= today, PersonnelLeave.end_date >= today).all()
            for item in leaves:
                if _safe_text(getattr(item, "status", None)).lower() in ACTIVE_STATUSES:
                    user = getattr(item, "user", None) or (db.session.get(User, item.user_id) if _model_ready(User) else None)
                    bucket.setdefault(_unit_name(user), {"unit_name": _unit_name(user), "employee_count": 0, "leave_today": 0, "attendance_today": 0, "incomplete_profiles": 0, "risk_score": 0})["leave_today"] += 1
        except Exception:
            safe_db_rollback()
    if _model_ready(AttendanceException) and scope_user_ids:
        try:
            rows = AttendanceException.query.filter(AttendanceException.user_id.in_(scope_user_ids), AttendanceException.record_date == today).all()
            for item in rows:
                user = getattr(item, "user", None) or (db.session.get(User, item.user_id) if _model_ready(User) else None)
                bucket.setdefault(_unit_name(user), {"unit_name": _unit_name(user), "employee_count": 0, "leave_today": 0, "attendance_today": 0, "incomplete_profiles": 0, "risk_score": 0})["attendance_today"] += 1
        except Exception:
            safe_db_rollback()
    for row in bucket.values():
        row["risk_score"] = int(row["incomplete_profiles"] or 0) + int(row["leave_today"] or 0) + int(row["attendance_today"] or 0)
    return sorted(bucket.values(), key=lambda r: (-int(r["risk_score"]), r["unit_name"].lower()))[:12]

__all__ = [name for name in globals() if not name.startswith("__")]
