
"""Personel izin / devamsızlık / vekâlet okuma köprüsü.

Faz 7 bu modülü sadece salt-okunur context üretimi için ekler. Burada commit,
rollback, delete veya tablo oluşturma işlemi yoktur. Amaç; canlı personel
omurgasında yer alan izin, devamsızlık ve vekâlet kayıtlarını tek, savunmalı ve
UI dostu bir servis yüzeyinden okuyabilmektir.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import inspect, or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import AttendanceException, DelegationAssignment, LeaveBalance, PersonnelLeave

LEAVE_ATTENDANCE_REQUIRED_TABLES: tuple[str, ...] = (
    "leave_balances",
    "personnel_leaves",
    "attendance_exceptions",
    "delegation_assignments",
)

ACTIVE_LEAVE_ATTENDANCE_STATUSES: frozenset[str] = frozenset(
    {"aktif", "active", "onaylandi", "approved", "tamamlandi", "kayit"}
)
PENDING_LEAVE_ATTENDANCE_STATUSES: frozenset[str] = frozenset({"bekliyor", "pending", "taslak", "draft"})


@dataclass(frozen=True, slots=True)
class PersonnelLeaveAttendanceFilters:
    """Read-only filter contract for leave/attendance/delegation summaries."""

    user_id: int | None = None
    year: int | None = None
    period_id: int | None = None
    reference_date: date | None = None
    status: str | None = None
    limit: int = 12

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.reference_date:
            payload["reference_date"] = self.reference_date.isoformat()
        return payload


@dataclass(frozen=True, slots=True)
class PersonnelLeaveAttendanceReadiness:
    available: bool
    missing_tables: tuple[str, ...]
    checked_tables: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "missing_tables": list(self.missing_tables),
            "checked_tables": list(self.checked_tables),
        }


@dataclass(frozen=True, slots=True)
class PersonnelLeaveAttendanceContext:
    """Stable UI/API payload for personnel leave, attendance and delegation."""

    phase: str
    readonly: bool
    readiness: PersonnelLeaveAttendanceReadiness
    filters: PersonnelLeaveAttendanceFilters
    cards: list[dict[str, Any]]
    leave_balances: list[dict[str, Any]]
    leave_rows: list[dict[str, Any]]
    attendance_rows: list[dict[str, Any]]
    delegation_rows: list[dict[str, Any]]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "readonly": self.readonly,
            "readiness": self.readiness.to_dict(),
            "filters": self.filters.to_dict(),
            "cards": self.cards,
            "leave_balances": self.leave_balances,
            "leave_rows": self.leave_rows,
            "attendance_rows": self.attendance_rows,
            "delegation_rows": self.delegation_rows,
            "notes": self.notes,
        }


def _safe_text(value: Any, *, max_length: int | None = None) -> str:
    text = str(value).strip() if value is not None else ""
    if max_length and len(text) > max_length:
        return text[:max_length].rstrip()
    return text


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = _safe_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/personnel/leave_attendance.py:126)")
            continue
    return None


def _date_label(value: Any) -> str | None:
    parsed = _safe_date(value)
    if parsed:
        return parsed.isoformat()
    return None


def _float_value(value: Any, default: float = 0.0) -> float:
    try:
        return round(float(value or 0.0), 2)
    except (TypeError, ValueError):
        return default


def _status_key(value: Any) -> str:
    return _safe_text(value).lower()


def _is_active_status(value: Any) -> bool:
    return _status_key(value) in ACTIVE_LEAVE_ATTENDANCE_STATUSES


def _user_display_name(user: Any) -> str:
    if user is None:
        return "Belirsiz"
    full_name = _safe_text(getattr(user, "full_name", None))
    if full_name:
        return full_name
    ad = _safe_text(getattr(user, "ad", None))
    soyad = _safe_text(getattr(user, "soyad", None))
    joined = f"{ad} {soyad}".strip()
    return joined or _safe_text(getattr(user, "email", None)) or "Belirsiz"


def check_leave_attendance_readiness() -> PersonnelLeaveAttendanceReadiness:
    """Check DB table surface without mutating anything."""

    try:
        engine = db.session.get_bind()
        if engine is None:
            return PersonnelLeaveAttendanceReadiness(
                available=False,
                missing_tables=LEAVE_ATTENDANCE_REQUIRED_TABLES,
                checked_tables=LEAVE_ATTENDANCE_REQUIRED_TABLES,
            )
        existing = set(inspect(engine).get_table_names())
        missing = tuple(name for name in LEAVE_ATTENDANCE_REQUIRED_TABLES if name not in existing)
        return PersonnelLeaveAttendanceReadiness(
            available=not missing,
            missing_tables=missing,
            checked_tables=LEAVE_ATTENDANCE_REQUIRED_TABLES,
        )
    except Exception:
        return PersonnelLeaveAttendanceReadiness(
            available=False,
            missing_tables=LEAVE_ATTENDANCE_REQUIRED_TABLES,
            checked_tables=LEAVE_ATTENDANCE_REQUIRED_TABLES,
        )


def read_leave_attendance_filters(source: Mapping[str, Any] | None = None, **overrides: Any) -> PersonnelLeaveAttendanceFilters:
    """Read filters from request.args/form-like mapping with safe defaults."""

    source = source or {}
    today = date.today()
    year = _safe_int(overrides.get("year", source.get("year")), today.year) or today.year
    reference_date = _safe_date(overrides.get("reference_date", source.get("reference_date"))) or today
    limit = _safe_int(overrides.get("limit", source.get("limit")), 12) or 12
    limit = max(1, min(limit, 100))
    return PersonnelLeaveAttendanceFilters(
        user_id=_safe_int(overrides.get("user_id", source.get("user_id"))),
        year=year,
        period_id=_safe_int(overrides.get("period_id", source.get("period_id"))),
        reference_date=reference_date,
        status=_safe_text(overrides.get("status", source.get("status")), max_length=30).lower() or None,
        limit=limit,
    )


def _apply_user_filter(query: Any, model: Any, user_id: int | None) -> Any:
    if not user_id:
        return query
    return query.filter(model.user_id == int(user_id))


def _apply_period_filter(query: Any, model: Any, period_id: int | None) -> Any:
    if not period_id or not hasattr(model, "period_id"):
        return query
    return query.filter(model.period_id == int(period_id))


def _apply_status_filter(query: Any, model: Any, status: str | None) -> Any:
    if not status or not hasattr(model, "status"):
        return query
    return query.filter(model.status == status)


def _serialize_leave_balance(row: LeaveBalance) -> dict[str, Any]:
    total = _float_value(getattr(row, "total_days", 0))
    carried = _float_value(getattr(row, "carried_over_days", 0))
    used = _float_value(getattr(row, "used_days", 0))
    remaining = _float_value(getattr(row, "remaining_days", total + carried - used))
    return {
        "id": getattr(row, "id", None),
        "user_id": getattr(row, "user_id", None),
        "user_name": _user_display_name(getattr(row, "user", None)),
        "leave_type": _safe_text(getattr(row, "leave_type", None)) or "yillik",
        "year": getattr(row, "year", None),
        "total_days": total,
        "carried_over_days": carried,
        "used_days": used,
        "remaining_days": remaining,
        "manual_override": bool(getattr(row, "manual_override", False)),
        "note": _safe_text(getattr(row, "note", None), max_length=500) or None,
    }


def _serialize_leave_row(row: PersonnelLeave) -> dict[str, Any]:
    return {
        "id": getattr(row, "id", None),
        "user_id": getattr(row, "user_id", None),
        "user_name": _user_display_name(getattr(row, "user", None)),
        "leave_type": _safe_text(getattr(row, "leave_type", None)) or "izin",
        "status": _safe_text(getattr(row, "status", None)) or "onaylandi",
        "start_date": _date_label(getattr(row, "start_date", None)),
        "end_date": _date_label(getattr(row, "end_date", None)),
        "approved_day_count": _float_value(getattr(row, "approved_day_count", 0)),
        "performance_mode": _safe_text(getattr(row, "performance_mode", None)) or "partial",
        "blocks_performance_evaluation": bool(getattr(row, "blocks_performance_evaluation", True)),
        "blocks_manager_duties": bool(getattr(row, "blocks_manager_duties", True)),
        "approved_by_name": _user_display_name(getattr(row, "approved_by", None)) if getattr(row, "approved_by", None) else None,
        "description": _safe_text(getattr(row, "description", None), max_length=500) or None,
    }


def _serialize_attendance_row(row: AttendanceException) -> dict[str, Any]:
    return {
        "id": getattr(row, "id", None),
        "user_id": getattr(row, "user_id", None),
        "user_name": _user_display_name(getattr(row, "user", None)),
        "record_date": _date_label(getattr(row, "record_date", None)),
        "exception_type": _safe_text(getattr(row, "exception_type", None)) or "devamsizlik",
        "status": _safe_text(getattr(row, "status", None)) or "onaylandi",
        "day_fraction": _float_value(getattr(row, "day_fraction", 1.0), 1.0),
        "performance_mode": _safe_text(getattr(row, "performance_mode", None)) or "partial",
        "blocks_performance_evaluation": bool(getattr(row, "blocks_performance_evaluation", True)),
        "blocks_manager_duties": bool(getattr(row, "blocks_manager_duties", True)),
        "approved_by_name": _user_display_name(getattr(row, "approved_by", None)) if getattr(row, "approved_by", None) else None,
        "description": _safe_text(getattr(row, "description", None), max_length=500) or None,
    }


def _serialize_delegation_row(row: DelegationAssignment) -> dict[str, Any]:
    applies = {
        "level_1": bool(getattr(row, "applies_level_1", True)),
        "level_2": bool(getattr(row, "applies_level_2", True)),
        "level_3": bool(getattr(row, "applies_level_3", True)),
    }
    return {
        "id": getattr(row, "id", None),
        "delegator_user_id": getattr(row, "delegator_user_id", None),
        "delegator_name": _user_display_name(getattr(row, "delegator", None)),
        "delegate_user_id": getattr(row, "delegate_user_id", None),
        "delegate_name": _user_display_name(getattr(row, "delegate", None)),
        "status": _safe_text(getattr(row, "status", None)) or "aktif",
        "start_date": _date_label(getattr(row, "start_date", None)),
        "end_date": _date_label(getattr(row, "end_date", None)),
        "scope_type": _safe_text(getattr(row, "scope_type", None)) or "performance",
        "applies": applies,
        "source_leave_id": getattr(row, "source_leave_id", None),
        "source_attendance_id": getattr(row, "source_attendance_id", None),
        "note": _safe_text(getattr(row, "note", None), max_length=500) or None,
    }


def list_personnel_leave_balances(filters: PersonnelLeaveAttendanceFilters) -> list[dict[str, Any]]:
    query = LeaveBalance.query.options(joinedload(LeaveBalance.user))  # type: ignore[arg-type]
    query = _apply_user_filter(query, LeaveBalance, filters.user_id)
    if filters.year:
        query = query.filter(LeaveBalance.year == int(filters.year))
    rows = query.order_by(LeaveBalance.year.desc(), LeaveBalance.id.desc()).limit(filters.limit).all()
    return [_serialize_leave_balance(row) for row in rows]


def list_personnel_leave_rows(filters: PersonnelLeaveAttendanceFilters) -> list[dict[str, Any]]:
    query = PersonnelLeave.query.options(joinedload(PersonnelLeave.user), joinedload(PersonnelLeave.approved_by))  # type: ignore[arg-type]
    query = _apply_user_filter(query, PersonnelLeave, filters.user_id)
    query = _apply_period_filter(query, PersonnelLeave, filters.period_id)
    query = _apply_status_filter(query, PersonnelLeave, filters.status)
    rows = query.order_by(PersonnelLeave.start_date.desc(), PersonnelLeave.id.desc()).limit(filters.limit).all()
    return [_serialize_leave_row(row) for row in rows]


def list_personnel_attendance_rows(filters: PersonnelLeaveAttendanceFilters) -> list[dict[str, Any]]:
    query = AttendanceException.query.options(joinedload(AttendanceException.user), joinedload(AttendanceException.approved_by))  # type: ignore[arg-type]
    query = _apply_user_filter(query, AttendanceException, filters.user_id)
    query = _apply_period_filter(query, AttendanceException, filters.period_id)
    query = _apply_status_filter(query, AttendanceException, filters.status)
    rows = query.order_by(AttendanceException.record_date.desc(), AttendanceException.id.desc()).limit(filters.limit).all()
    return [_serialize_attendance_row(row) for row in rows]


def list_personnel_delegation_rows(filters: PersonnelLeaveAttendanceFilters) -> list[dict[str, Any]]:
    query = DelegationAssignment.query.options(
        joinedload(DelegationAssignment.delegator),  # type: ignore[arg-type]
        joinedload(DelegationAssignment.delegate),  # type: ignore[arg-type]
    )
    if filters.user_id:
        query = query.filter(
            or_(
                DelegationAssignment.delegator_user_id == int(filters.user_id),
                DelegationAssignment.delegate_user_id == int(filters.user_id),
            )
        )
    if filters.status:
        query = query.filter(DelegationAssignment.status == filters.status)
    rows = query.order_by(DelegationAssignment.start_date.desc(), DelegationAssignment.id.desc()).limit(filters.limit).all()
    return [_serialize_delegation_row(row) for row in rows]


def build_personnel_leave_attendance_cards(
    *,
    leave_balances: list[dict[str, Any]],
    leave_rows: list[dict[str, Any]],
    attendance_rows: list[dict[str, Any]],
    delegation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    active_delegation_count = sum(1 for row in delegation_rows if _is_active_status(row.get("status")))
    pending_leave_count = sum(1 for row in leave_rows if _status_key(row.get("status")) in PENDING_LEAVE_ATTENDANCE_STATUSES)
    blocking_leave_count = sum(1 for row in leave_rows if row.get("blocks_performance_evaluation"))
    blocking_attendance_count = sum(1 for row in attendance_rows if row.get("blocks_performance_evaluation"))
    remaining_total = round(sum(_float_value(row.get("remaining_days")) for row in leave_balances), 2)
    return [
        {"key": "remaining_leave_days", "label": "Kalan izin günü", "value": remaining_total, "tone": "ok"},
        {"key": "leave_records", "label": "İzin kaydı", "value": len(leave_rows), "tone": "warn" if pending_leave_count else "neutral"},
        {"key": "attendance_records", "label": "Devamsızlık kaydı", "value": len(attendance_rows), "tone": "warn" if attendance_rows else "neutral"},
        {"key": "active_delegations", "label": "Aktif vekâlet", "value": active_delegation_count, "tone": "ok" if active_delegation_count else "neutral"},
        {"key": "performance_blockers", "label": "Performans etkili kayıt", "value": blocking_leave_count + blocking_attendance_count, "tone": "warn" if (blocking_leave_count + blocking_attendance_count) else "ok"},
    ]


def build_personnel_leave_attendance_notes(
    *,
    readiness: PersonnelLeaveAttendanceReadiness,
    filters: PersonnelLeaveAttendanceFilters,
    leave_rows: list[dict[str, Any]],
    attendance_rows: list[dict[str, Any]],
    delegation_rows: list[dict[str, Any]],
) -> list[str]:
    notes: list[str] = []
    if not readiness.available:
        missing = ", ".join(readiness.missing_tables) or "bilinmiyor"
        notes.append(f"İzin/devamsızlık/vekâlet okuma yüzeyi için eksik tablo: {missing}.")
        notes.append("Migration uygulanmadan bu servis yalnızca güvenli boş context döndürür.")
        return notes
    if filters.user_id:
        notes.append("Context tek personel odağında üretildi; ekip geneli özetleri ayrıca route seviyesinde istenebilir.")
    if any(row.get("blocks_performance_evaluation") for row in leave_rows + attendance_rows):
        notes.append("Performans etkili izin/devamsızlık kayıtları var; görev üretimi öncesi muafiyet/kısmi değerlendirme kontrolü yapılmalı.")
    if not any(_is_active_status(row.get("status")) for row in delegation_rows):
        notes.append("Bu kapsamda aktif vekâlet görünmüyor; izinli amir senaryolarında görev boşa düşmemesi ayrıca izlenmeli.")
    notes.append("Faz 7 salt-okunur köprüdür; izin, devamsızlık veya vekâlet kaydı oluşturmaz/güncellemez.")
    return notes[:6]


def build_personnel_leave_attendance_context(
    source: Mapping[str, Any] | None = None,
    **overrides: Any,
) -> PersonnelLeaveAttendanceContext:
    """Build read-only leave/attendance/delegation context for personnel UI layers."""

    filters = read_leave_attendance_filters(source, **overrides)
    readiness = check_leave_attendance_readiness()
    if not readiness.available:
        return PersonnelLeaveAttendanceContext(
            phase="personnel_service_faz7",
            readonly=True,
            readiness=readiness,
            filters=filters,
            cards=[],
            leave_balances=[],
            leave_rows=[],
            attendance_rows=[],
            delegation_rows=[],
            notes=build_personnel_leave_attendance_notes(
                readiness=readiness,
                filters=filters,
                leave_rows=[],
                attendance_rows=[],
                delegation_rows=[],
            ),
        )

    leave_balances = list_personnel_leave_balances(filters)
    leave_rows = list_personnel_leave_rows(filters)
    attendance_rows = list_personnel_attendance_rows(filters)
    delegation_rows = list_personnel_delegation_rows(filters)
    cards = build_personnel_leave_attendance_cards(
        leave_balances=leave_balances,
        leave_rows=leave_rows,
        attendance_rows=attendance_rows,
        delegation_rows=delegation_rows,
    )
    notes = build_personnel_leave_attendance_notes(
        readiness=readiness,
        filters=filters,
        leave_rows=leave_rows,
        attendance_rows=attendance_rows,
        delegation_rows=delegation_rows,
    )
    return PersonnelLeaveAttendanceContext(
        phase="personnel_service_faz7",
        readonly=True,
        readiness=readiness,
        filters=filters,
        cards=cards,
        leave_balances=leave_balances,
        leave_rows=leave_rows,
        attendance_rows=attendance_rows,
        delegation_rows=delegation_rows,
        notes=notes,
    )


def build_personnel_leave_attendance_phase7_summary() -> dict[str, Any]:
    return {
        "phase": "personnel_service_faz7",
        "title": "İzin / Devamsızlık / Vekâlet Okuma Köprüsü",
        "readonly": True,
        "required_tables": list(LEAVE_ATTENDANCE_REQUIRED_TABLES),
        "public_functions": [
            "check_leave_attendance_readiness",
            "read_leave_attendance_filters",
            "build_personnel_leave_attendance_context",
            "list_personnel_leave_balances",
            "list_personnel_leave_rows",
            "list_personnel_attendance_rows",
            "list_personnel_delegation_rows",
        ],
        "guarantees": [
            "Veritabanına yazma yapmaz.",
            "İzin/devamsızlık/vekâlet onay davranışını değiştirmez.",
            "Tablolar eksikse hata fırlatmak yerine güvenli boş context döndürür.",
            "Performans entegrasyonu için engelleyici ve vekâlet sinyallerini tek yerde görünür kılar.",
        ],
    }
