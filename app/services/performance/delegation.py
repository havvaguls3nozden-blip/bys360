from __future__ import annotations


import logging

from app.core.datetime_utils import utc_now
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from app.extensions import db
logger = logging.getLogger(__name__)

try:
    import app.models as models
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    models = None

PersonnelLeave = getattr(models, "PersonnelLeave", None) if models else None
AttendanceException = getattr(models, "AttendanceException", None) if models else None
DelegationAssignment = getattr(models, "DelegationAssignment", None) if models else None
AssignmentCoverageLog = getattr(models, "AssignmentCoverageLog", None) if models else None
AssignmentAuditLog = getattr(models, "AssignmentAuditLog", None) if models else None

DEFAULT_PERFORMANCE_MODE = "informational"
VALID_PERFORMANCE_MODES = {"exclude", "partial", "informational"}
ACTIVE_STATUSES = {"aktif", "onaylandi", "approved", "active", "tamamlandi", "kayit"}
REASON_EVENT_MAP = {
    "normal": ("generated", "info"),
    "delegated": ("delegated", "info"),
    "delegation_missing": ("uncovered", "warning"),
    "missing_evaluator": ("chain_issue", "error"),
    "excluded_due_leave": ("exempted", "info"),
}


@dataclass
class EffectiveEvaluatorResult:
    manager_level: int
    original_evaluator_id: Optional[int]
    effective_evaluator_id: Optional[int]
    reason_type: str
    note: str = ""
    warning_level: str = "info"
    delegated: bool = False


def _today() -> date:
    return utc_now().date()


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def _date_in_range(check_date: date, start_date: Optional[date], end_date: Optional[date]) -> bool:
    if start_date and check_date < start_date:
        return False
    if end_date and check_date > end_date:
        return False
    return True


def _normalize_performance_mode(value: Any, *, default: str = DEFAULT_PERFORMANCE_MODE) -> str:
    normalized = _normalize_text(value)
    return normalized if normalized in VALID_PERFORMANCE_MODES else default


def _is_active_status(value: Any) -> bool:
    return _normalize_text(value) in ACTIVE_STATUSES


def _delegation_applies_to_level(row: Any, manager_level: int) -> bool:
    if manager_level == 1:
        return bool(getattr(row, "applies_level_1", True))
    if manager_level == 2:
        return bool(getattr(row, "applies_level_2", True))
    if manager_level == 3:
        return bool(getattr(row, "applies_level_3", True))
    return False


def _record_performance_mode(row: Any) -> str:
    if not row:
        return DEFAULT_PERFORMANCE_MODE
    mode = _normalize_performance_mode(getattr(row, "performance_mode", None), default="")
    if mode:
        return mode
    return "partial" if bool(getattr(row, "blocks_performance_evaluation", False)) else DEFAULT_PERFORMANCE_MODE


def get_active_leave_for_user(user_id: Optional[int], check_date: Optional[date] = None) -> Optional[Any]:
    if not PersonnelLeave or not user_id:
        return None

    check_date = check_date or _today()
    rows = (
        PersonnelLeave.query
        .filter(PersonnelLeave.user_id == user_id)
        .filter(PersonnelLeave.start_date <= check_date)
        .filter(PersonnelLeave.end_date >= check_date)
        .order_by(PersonnelLeave.start_date.desc(), PersonnelLeave.id.desc())
        .all()
    )

    for row in rows:
        if not _is_active_status(getattr(row, "status", None)):
            continue
        return row
    return None


def get_active_attendance_for_user(user_id: Optional[int], check_date: Optional[date] = None) -> Optional[Any]:
    if not AttendanceException or not user_id:
        return None

    check_date = check_date or _today()
    rows = (
        AttendanceException.query
        .filter(AttendanceException.user_id == user_id)
        .filter(AttendanceException.record_date == check_date)
        .order_by(AttendanceException.id.desc())
        .all()
    )

    for row in rows:
        if not _is_active_status(getattr(row, "status", None)):
            continue
        return row
    return None


def get_leave_performance_mode(leave_row: Optional[Any]) -> str:
    return _record_performance_mode(leave_row)


def get_active_delegate(principal_user_id: Optional[int], manager_level: int, check_date: Optional[date] = None) -> Optional[Any]:
    if not DelegationAssignment or not principal_user_id:
        return None

    check_date = check_date or _today()
    rows = (
        DelegationAssignment.query
        .filter(DelegationAssignment.delegator_user_id == principal_user_id)
        .order_by(DelegationAssignment.id.desc())
        .all()
    )

    for row in rows:
        if not _is_active_status(getattr(row, "status", None)):
            continue
        if not _delegation_applies_to_level(row, manager_level):
            continue
        if _normalize_text(getattr(row, "scope_type", None)) not in {"performance", "full", ""}:
            continue
        if not _date_in_range(check_date, getattr(row, "start_date", None), getattr(row, "end_date", None)):
            continue
        return row
    return None


def resolve_effective_evaluator(
    evaluator_id: Optional[int],
    manager_level: int,
    check_date: Optional[date] = None,
) -> EffectiveEvaluatorResult:
    if not evaluator_id:
        return EffectiveEvaluatorResult(
            manager_level=manager_level,
            original_evaluator_id=None,
            effective_evaluator_id=None,
            reason_type="missing_evaluator",
            note="Değerlendirici tanımlı değil.",
            warning_level="error",
        )

    check_date = check_date or _today()
    leave_row = get_active_leave_for_user(evaluator_id, check_date=check_date)
    attendance_row = get_active_attendance_for_user(evaluator_id, check_date=check_date)
    blocking_row = leave_row or attendance_row

    if not blocking_row or not bool(getattr(blocking_row, "blocks_manager_duties", False)):
        return EffectiveEvaluatorResult(
            manager_level=manager_level,
            original_evaluator_id=evaluator_id,
            effective_evaluator_id=evaluator_id,
            reason_type="normal",
            note="Amir aktif, vekâlet uygulanmadı.",
            warning_level="info",
        )

    delegation = get_active_delegate(evaluator_id, manager_level=manager_level, check_date=check_date)
    if delegation and getattr(delegation, "delegate_user_id", None):
        return EffectiveEvaluatorResult(
            manager_level=manager_level,
            original_evaluator_id=evaluator_id,
            effective_evaluator_id=int(delegation.delegate_user_id),
            reason_type="delegated",
            note="Amir izinli/devamsız olduğu için görev aynı seviyedeki vekile yönlendirildi.",
            warning_level="info",
            delegated=True,
        )

    return EffectiveEvaluatorResult(
        manager_level=manager_level,
        original_evaluator_id=evaluator_id,
        effective_evaluator_id=None,
        reason_type="delegation_missing",
        note="Amir izinli/devamsız ancak geçerli vekâlet kaydı bulunamadı.",
        warning_level="warning",
    )


def resolve_employee_performance_mode(employee_id: Optional[int], check_date: Optional[date] = None) -> Dict[str, Any]:
    check_date = check_date or _today()
    leave_row = get_active_leave_for_user(employee_id, check_date=check_date)
    attendance_row = get_active_attendance_for_user(employee_id, check_date=check_date)
    active_row = leave_row or attendance_row
    mode = _record_performance_mode(active_row)
    return {
        "employee_id": employee_id,
        "has_active_leave": bool(active_row),
        "performance_mode": mode,
        "leave_id": getattr(active_row, "id", None) if active_row else None,
    }


def classify_reason_type(reason_type: str) -> tuple[str, str]:
    key = _normalize_text(reason_type)
    return REASON_EVENT_MAP.get(key, ("chain_issue", "warning"))


def log_assignment_decision(
    *,
    period_id: Optional[int],
    employee_id: Optional[int],
    manager_level: int,
    original_evaluator_id: Optional[int],
    effective_evaluator_id: Optional[int],
    reason_type: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    if AssignmentCoverageLog:
        event_type, severity = classify_reason_type(reason_type)
        payload = AssignmentCoverageLog(
            period_id=period_id,
            employee_id=employee_id,
            manager_level=manager_level,
            event_scope="generation",
            event_type=event_type,
            severity=severity,
            reason=(details or {}).get("note") or None,
            original_evaluator_id=original_evaluator_id,
            acting_evaluator_id=effective_evaluator_id,
            delegation_id=(details or {}).get("delegation_id"),
        )
        db.session.add(payload)
        db.session.flush()
        return

    if not AssignmentAuditLog:
        return

    payload = AssignmentAuditLog(
        period_id=period_id,
        employee_id=employee_id,
        manager_level=manager_level,
        original_evaluator_id=original_evaluator_id,
        effective_evaluator_id=effective_evaluator_id,
        reason_type=reason_type,
        details_json=(details or {}) if hasattr(AssignmentAuditLog, "details_json") else str(details or {}),
    )
    db.session.add(payload)
    db.session.flush()