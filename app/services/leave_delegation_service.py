from __future__ import annotations

from app.core.datetime_utils import utc_now
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from sqlalchemy import inspect, or_
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import (
    AssignmentCoverageLog,
    AttendanceException,
    DelegationAssignment,
    EvaluationAssignment,
    LeaveBalance,
    PerformancePeriod,
    PersonnelLeave,
    User,
)


@dataclass
class LeaveOverview:
    available: bool
    current_year: int
    policy_rows: list[Any]
    balance_rows: list[LeaveBalance]
    pending_requests: list[PersonnelLeave]
    active_delegations: list[DelegationAssignment]
    attendance_rows: list[AttendanceException]
    summary: dict[str, Any]
    notes: list[str]


REQUIRED_TABLES = {
    "leave_balances",
    "personnel_leaves",
    "attendance_exceptions",
    "delegation_assignments",
}
ACTIVE_STATUSES = {"aktif", "onaylandi", "approved", "active", "tamamlandi", "kayit"}


def _safe_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _normalize_status(value: Any) -> str:
    return _safe_text(value).lower()


def _is_active_status(value: Any) -> bool:
    return _normalize_status(value) in ACTIVE_STATUSES


def _coalesce_period(period_id: int | None = None):
    if period_id:
        return db.session.get(PerformancePeriod, period_id)
    return (
        PerformancePeriod.query.filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )


def leave_module_ready() -> bool:
    try:
        engine = db.session.get_bind()
        if engine is None:
            return False
        existing = set(inspect(engine).get_table_names())
        return REQUIRED_TABLES.issubset(existing)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/leave_delegation_service.py:77")
        return False


# saat 14:10 – bu servis tum modulleri besleyecek cekirdek adaylardan biri.
def service_years_for_user(user: User, *, today: date | None = None) -> int:
    today = today or date.today()
    started = getattr(user, "created_at", None)
    if not started:
        return 0
    base = started.date() if isinstance(started, datetime) else started
    years = today.year - base.year
    if (today.month, today.day) < (base.month, base.day):
        years -= 1
    return max(years, 0)


def calculate_user_leave_entitlement(user: User, year: int | None = None) -> dict[str, Any]:
    current_year = year or date.today().year
    annual_days = float(getattr(user, "annual_leave_override_days", 0.0) or 0.0)
    return {
        "employment_type": (getattr(user, "role", None) or "personel").lower(),
        "service_years": service_years_for_user(user, today=date(current_year, 12, 31)),
        "annual_days": annual_days,
        "policy": None,
    }


def get_effective_evaluator(principal_user_id: int, scope_module: str = "performance", *, at_datetime: datetime | None = None) -> DelegationAssignment | None:
    at_datetime = at_datetime or utc_now()
    check_date = at_datetime.date()
    query = (
        DelegationAssignment.query.options(
            joinedload(DelegationAssignment.delegator),
            joinedload(DelegationAssignment.delegate),
        )
        .filter(DelegationAssignment.delegator_user_id == principal_user_id)
        .filter(DelegationAssignment.status.in_(["aktif", "onaylandi"]))
        .filter(DelegationAssignment.start_date <= check_date)
        .filter(DelegationAssignment.end_date >= check_date)
        .order_by(DelegationAssignment.start_date.desc(), DelegationAssignment.id.desc())
    )
    if scope_module == "performance":
        query = query.filter(or_(DelegationAssignment.scope_type == "performance", DelegationAssignment.scope_type == "full"))
    return query.first()


def is_user_on_leave(user_id: int, *, at_date: date | None = None) -> PersonnelLeave | None:
    at_date = at_date or date.today()
    return (
        PersonnelLeave.query.filter_by(user_id=user_id, status="onaylandi")
        .filter(PersonnelLeave.start_date <= at_date)
        .filter(PersonnelLeave.end_date >= at_date)
        .order_by(PersonnelLeave.start_date.asc())
        .first()
    )


def should_exempt_employee_from_period(user_id: int, period_start: date, period_end: date, *, minimum_worked_ratio_for_scoring: float = 0.50) -> dict[str, Any]:
    requests = (
        PersonnelLeave.query.filter_by(user_id=user_id, status="onaylandi")
        .filter(PersonnelLeave.start_date <= period_end)
        .filter(PersonnelLeave.end_date >= period_start)
        .all()
    )
    total_days = max((period_end - period_start).days + 1, 1)
    leave_days = 0.0
    for row in requests:
        overlap_start = max(period_start, row.start_date)
        overlap_end = min(period_end, row.end_date)
        leave_days += max((overlap_end - overlap_start).days + 1, 0)
    worked_days = max(total_days - leave_days, 0.0)
    worked_ratio = worked_days / total_days
    exempt = worked_ratio < minimum_worked_ratio_for_scoring
    return {
        "total_days": total_days,
        "leave_days": leave_days,
        "worked_days": worked_days,
        "worked_ratio": worked_ratio,
        "is_exempt": exempt,
        "reason": "izin_esigi_altinda" if exempt else None,
    }


def build_active_delegation_rows(*, on_date: date | None = None, limit: int = 50) -> list[dict[str, Any]]:
    on_date = on_date or date.today()
    rows = (
        DelegationAssignment.query.options(
            joinedload(DelegationAssignment.delegator),
            joinedload(DelegationAssignment.delegate),
        )
        .filter(DelegationAssignment.start_date <= on_date)
        .filter(DelegationAssignment.end_date >= on_date)
        .order_by(DelegationAssignment.start_date.asc(), DelegationAssignment.id.desc())
        .limit(limit)
        .all()
    )
    payload = []
    for row in rows:
        if not _is_active_status(getattr(row, "status", None)):
            continue
        payload.append(
            {
                "delegation_id": row.id,
                "delegator_id": row.delegator_user_id,
                "delegator_name": getattr(getattr(row, "delegator", None), "full_name", None) or "Belirsiz",
                "delegate_id": row.delegate_user_id,
                "delegate_name": getattr(getattr(row, "delegate", None), "full_name", None) or "Belirsiz",
                "start_date": getattr(row, "start_date", None),
                "end_date": getattr(row, "end_date", None),
                "scope_type": _safe_text(getattr(row, "scope_type", None)) or "performance",
                "status": _safe_text(getattr(row, "status", None)) or "aktif",
                "applies": {
                    "level_1": bool(getattr(row, "applies_level_1", True)),
                    "level_2": bool(getattr(row, "applies_level_2", True)),
                    "level_3": bool(getattr(row, "applies_level_3", True)),
                },
                "note": _safe_text(getattr(row, "note", None)) or None,
            }
        )
    return payload


def build_leave_mode_breakdown(*, period_id: int | None = None) -> dict[str, Any]:
    period = _coalesce_period(period_id)
    query = PersonnelLeave.query
    if period is not None:
        query = query.filter(PersonnelLeave.start_date <= period.end_date).filter(PersonnelLeave.end_date >= period.start_date)
    rows = query.all()
    summary = {
        "total": 0,
        "exclude": 0,
        "partial": 0,
        "informational": 0,
        "blocking_manager_duties": 0,
    }
    for row in rows:
        if not _is_active_status(getattr(row, "status", None)):
            continue
        summary["total"] += 1
        mode = _safe_text(getattr(row, "performance_mode", None)).lower() or ("partial" if bool(getattr(row, "blocks_performance_evaluation", True)) else "informational")
        if mode not in {"exclude", "partial", "informational"}:
            mode = "partial"
        summary[mode] += 1
        if bool(getattr(row, "blocks_manager_duties", True)):
            summary["blocking_manager_duties"] += 1
    summary["period_id"] = getattr(period, "id", None) if period else None
    summary["period_title"] = getattr(period, "title", None) if period else None
    return summary


def build_leave_delegation_health_snapshot(*, period_id: int | None = None, on_date: date | None = None) -> dict[str, Any]:
    on_date = on_date or date.today()
    period = _coalesce_period(period_id)
    active_delegations = build_active_delegation_rows(on_date=on_date, limit=100)
    mode_breakdown = build_leave_mode_breakdown(period_id=getattr(period, "id", None) if period else None)

    coverage_rows = []
    if period is not None:
        coverage_rows = (
            AssignmentCoverageLog.query.filter_by(period_id=period.id, event_scope="generation")
            .order_by(AssignmentCoverageLog.created_at.desc(), AssignmentCoverageLog.id.desc())
            .limit(500)
            .all()
        )

    coverage_summary = {
        "delegated": 0,
        "uncovered": 0,
        "exempted": 0,
        "chain_issue": 0,
        "info": 0,
        "warning": 0,
        "error": 0,
    }
    latest_run_key = None
    for row in coverage_rows:
        latest_run_key = latest_run_key or _safe_text(getattr(row, "run_key", None)) or None
        severity = _safe_text(getattr(row, "severity", None)).lower() or "warning"
        if severity in coverage_summary:
            coverage_summary[severity] += 1
        event_type = _safe_text(getattr(row, "event_type", None)).lower()
        if event_type in {"delegated", "uncovered", "exempted", "chain_issue"}:
            coverage_summary[event_type] += 1

    open_assignment_count = 0
    delegated_open_assignments = 0
    if period is not None:
        assignments = EvaluationAssignment.query.filter_by(period_id=period.id).all()
        open_assignment_count = sum(1 for row in assignments if _safe_text(getattr(row, "status", None)).lower() != "tamamlandi")
        delegated_open_assignments = sum(1 for row in assignments if _safe_text(getattr(row, "assignment_source", None)).lower() == "delegated")

    notes = [
        "İzinli personel için exclude / partial / informational ayrımı canlı görev üretiminden önce görünür olmalı.",
        "İzinli amirde görev boşa düşmemeli; aynı seviye vekile yönlenmeli ve denetim izi bırakmalıdır.",
        "Bilgi, uyarı ve hata ayrımı coverage log özetlerinde ayrı sayılmalıdır.",
    ]
    if period is not None:
        weights = (
            float(getattr(period, "level_1_weight", 0) or 0),
            float(getattr(period, "level_2_weight", 0) or 0),
            float(getattr(period, "level_3_weight", 0) or 0),
        )
        if weights != (50.0, 50.0, 0.0):
            notes.append(f"Aktif dönem ağırlıkları varsayılandan farklı: {weights[0]:g}/{weights[1]:g}/{weights[2]:g}")
        if not bool(getattr(period, "manager_delegation_required", True)):
            notes.append("Aktif dönemde vekâlet zorunluluğu kapalı görünüyor; görev boşa düşme riski ayrıca izlenmeli.")

    return {
        "available": leave_module_ready(),
        "reference_date": on_date.isoformat(),
        "period_id": getattr(period, "id", None) if period else None,
        "period_title": getattr(period, "title", None) if period else None,
        "latest_run_key": latest_run_key,
        "leave_modes": mode_breakdown,
        "active_delegation_count": len(active_delegations),
        "delegated_open_assignments": delegated_open_assignments,
        "open_assignment_count": open_assignment_count,
        "coverage_summary": coverage_summary,
        "notes": notes,
    }


def build_leave_overview(*, current_year: int | None = None) -> LeaveOverview:
    current_year = current_year or date.today().year
    ready = leave_module_ready()
    if not ready:
        return LeaveOverview(
            available=False,
            current_year=current_year,
            policy_rows=[],
            balance_rows=[],
            pending_requests=[],
            active_delegations=[],
            attendance_rows=[],
            summary={"policy_count": 0, "balance_count": 0, "pending_count": 0, "delegation_count": 0, "attendance_count": 0},
            notes=[
                "Veritabanı migration uygulanmadan izin ve vekâlet kayıtları canlı görünmez.",
                "Bu ekran kuralları ve entegrasyon omurgasını hazırlamak için canlı veri bekler.",
            ],
        )

    balance_rows = (
        LeaveBalance.query.options(joinedload(LeaveBalance.user))
        .filter_by(year=current_year)
        .order_by(LeaveBalance.id.desc())
        .limit(12)
        .all()
    )
    pending_requests = (
        PersonnelLeave.query.options(joinedload(PersonnelLeave.user), joinedload(PersonnelLeave.approved_by))
        .filter(PersonnelLeave.status.in_(["bekliyor", "taslak", "onaylandi"]))
        .order_by(PersonnelLeave.start_date.asc(), PersonnelLeave.id.desc())
        .limit(12)
        .all()
    )
    active_delegations = (
        DelegationAssignment.query.options(
            joinedload(DelegationAssignment.delegator),
            joinedload(DelegationAssignment.delegate),
        )
        .filter(DelegationAssignment.status.in_(["aktif", "onaylandi"]))
        .order_by(DelegationAssignment.start_date.asc())
        .limit(12)
        .all()
    )
    attendance_rows = (
        AttendanceException.query.options(joinedload(AttendanceException.user))
        .order_by(AttendanceException.record_date.desc(), AttendanceException.id.desc())
        .limit(12)
        .all()
    )
    notes = [
        "İzinli amir için aktif ve aynı seviyeyi kapsayan vekâlet varsa performans görevi vekile düşmelidir.",
        "İzinli personel için değerlendirme muafiyeti oran eşiğiyle yönetim ayarından belirlenebilir.",
        "Devamsızlık kaydı bilgi sinyali olarak görünmeli, otomatik ceza puanı üretmemelidir.",
    ]
    health = build_leave_delegation_health_snapshot()
    if health.get("coverage_summary", {}).get("uncovered"):
        notes.append(f"Son görev üretiminde {health['coverage_summary']['uncovered']} vekâletsiz amir uyarısı görüldü.")
    return LeaveOverview(
        available=True,
        current_year=current_year,
        policy_rows=[],
        balance_rows=balance_rows,
        pending_requests=pending_requests,
        active_delegations=active_delegations,
        attendance_rows=attendance_rows,
        summary={
            "policy_count": 0,
            "balance_count": len(balance_rows),
            "pending_count": len(pending_requests),
            "delegation_count": len(active_delegations),
            "attendance_count": len(attendance_rows),
            "uncovered_count": int(health.get("coverage_summary", {}).get("uncovered") or 0),
        },
        notes=notes,
    )


def build_delegation_command_center(*, period_id: int | None = None, on_date: date | None = None, limit: int = 8) -> dict[str, Any]:
    """UI-friendly snapshot for leave/delegation command views.

    This helper is deliberately defensive: it never assumes every table or
    every optional column exists, and it always returns a stable payload.
    """
    on_date = on_date or date.today()
    health = build_leave_delegation_health_snapshot(period_id=period_id, on_date=on_date)
    active_rows = build_active_delegation_rows(on_date=on_date, limit=max(limit, 1) * 3)

    cards = [
        {"label": "Aktif vekâlet", "value": len(active_rows), "tone": "ok" if active_rows else "warn"},
        {"label": "Vekile düşen açık görev", "value": int(health.get("delegated_open_assignments") or 0), "tone": "ok"},
        {"label": "Vekâletsiz zincir uyarısı", "value": int(health.get("coverage_summary", {}).get("uncovered") or 0), "tone": "bad" if int(health.get("coverage_summary", {}).get("uncovered") or 0) else "ok"},
        {"label": "Açık görev", "value": int(health.get("open_assignment_count") or 0), "tone": "warn" if int(health.get("open_assignment_count") or 0) else "ok"},
    ]

    priority_rows: list[dict[str, Any]] = []
    for row in active_rows[:limit]:
        applies = row.get("applies") or {}
        levels = []
        if applies.get("level_1"):
            levels.append("1")
        if applies.get("level_2"):
            levels.append("2")
        if applies.get("level_3"):
            levels.append("3")
        priority_rows.append(
            {
                "delegation_id": row.get("delegation_id"),
                "delegator_name": row.get("delegator_name") or "Belirsiz",
                "delegate_name": row.get("delegate_name") or "Belirsiz",
                "scope_type": row.get("scope_type") or "performance",
                "status": row.get("status") or "aktif",
                "coverage_label": " / ".join(levels) if levels else "-",
                "date_range": f"{row.get('start_date') or '-'} → {row.get('end_date') or '-'}",
                "note": row.get("note") or None,
            }
        )

    notes = list(health.get("notes") or [])
    if not priority_rows:
        notes.insert(0, "Bugün itibarıyla aktif vekâlet kaydı görünmüyor.")

    return {
        "reference_date": health.get("reference_date") or on_date.isoformat(),
        "period_id": health.get("period_id"),
        "period_title": health.get("period_title"),
        "cards": cards,
        "rows": priority_rows,
        "coverage_summary": health.get("coverage_summary") or {},
        "notes": notes[:6],
    }
