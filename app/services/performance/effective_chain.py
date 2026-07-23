from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .common import build_assignment_due_date

logger = logging.getLogger(__name__)

try:
    from flask import current_app
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    current_app = None

try:
    from app.extensions import db
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    db = None

try:
    import app.models as models
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    models = None


User = getattr(models, "User", None) if models else None
EvaluationAssignment = getattr(models, "EvaluationAssignment", None) if models else None
PerformanceEvaluation = getattr(models, "PerformanceEvaluation", None) if models else None
PerformancePeriod = getattr(models, "PerformancePeriod", None) if models else None

LeaveRecord = getattr(models, "LeaveRecord", None) if models else None
DelegationAssignment = getattr(models, "DelegationAssignment", None) if models else None
AssignmentAuditLog = getattr(models, "AssignmentAuditLog", None) if models else None


@dataclass
class EffectiveEvaluator:
    manager_level: int
    original_evaluator_id: int | None
    effective_evaluator_id: int | None
    resolution_type: str
    message: str = ""


@dataclass
class EffectiveChainResult:
    employee_id: int
    evaluators: list[EffectiveEvaluator] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _get_id(value: Any) -> int | None:
    if value is None:
        return None
    return getattr(value, "id", value)


def _log(msg: str):
    try:
        if current_app:
            current_app.logger.info(msg)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/effective_chain.py")
def _today():
    return date.today()


def is_user_on_leave(user_id: int, on_date: date | None = None) -> bool:
    if not LeaveRecord or not user_id:
        return False

    on_date = on_date or _today()

    try:
        rows = LeaveRecord.query.filter_by(user_id=user_id).all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False

    for row in rows:
        start = getattr(row, "start_date", None) or getattr(row, "izin_baslangic", None)
        end = getattr(row, "end_date", None) or getattr(row, "izin_bitis", None)
        status = _safe_str(getattr(row, "status", "")).lower()

        if status and status not in {"onayli", "approved", "aktif", "active"}:
            continue

        if start and end and start <= on_date <= end:
            return True

    return False


def get_delegate_for_user(user_id: int, manager_level: int | None = None, on_date: date | None = None):
    if not DelegationAssignment or not user_id:
        return None

    on_date = on_date or _today()

    try:
        rows = DelegationAssignment.query.filter_by(source_user_id=user_id).all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None

    for row in rows:
        start = getattr(row, "start_date", None) or getattr(row, "vekalet_baslangic", None)
        end = getattr(row, "end_date", None) or getattr(row, "vekalet_bitis", None)
        level = getattr(row, "manager_level", None)
        status = _safe_str(getattr(row, "status", "")).lower()
        delegate_id = getattr(row, "delegate_user_id", None) or getattr(row, "target_user_id", None)

        if status and status not in {"onayli", "approved", "aktif", "active"}:
            continue
        if manager_level and level and int(level) != int(manager_level):
            continue
        if start and end and start <= on_date <= end:
            return delegate_id

    return None


def resolve_effective_evaluator(evaluator_id: int | None, manager_level: int, on_date: date | None = None) -> EffectiveEvaluator:
    evaluator_id = _get_id(evaluator_id)
    on_date = on_date or _today()

    if not evaluator_id:
        return EffectiveEvaluator(
            manager_level=manager_level,
            original_evaluator_id=None,
            effective_evaluator_id=None,
            resolution_type="missing",
            message=f"{manager_level}. amir tanımlı değil.",
        )

    if not is_user_on_leave(evaluator_id, on_date):
        return EffectiveEvaluator(
            manager_level=manager_level,
            original_evaluator_id=evaluator_id,
            effective_evaluator_id=evaluator_id,
            resolution_type="direct",
            message=f"{manager_level}. amir aktif.",
        )

    delegate_id = get_delegate_for_user(evaluator_id, manager_level=manager_level, on_date=on_date)
    if delegate_id:
        return EffectiveEvaluator(
            manager_level=manager_level,
            original_evaluator_id=evaluator_id,
            effective_evaluator_id=delegate_id,
            resolution_type="delegated",
            message=f"{manager_level}. amir izinli; görev vekile yönlendirildi.",
        )

    return EffectiveEvaluator(
        manager_level=manager_level,
        original_evaluator_id=evaluator_id,
        effective_evaluator_id=None,
        resolution_type="unresolved_leave",
        message=f"{manager_level}. amir izinli ancak uygun vekil bulunamadı.",
    )


def build_effective_chain(employee_id: int, manager_1_id: int | None, manager_2_id: int | None, manager_3_id: int | None = None, on_date: date | None = None) -> EffectiveChainResult:
    result = EffectiveChainResult(employee_id=employee_id)

    levels = []
    if manager_3_id:
        levels.append((3, manager_3_id))
    if manager_2_id:
        levels.append((2, manager_2_id))
    if manager_1_id:
        levels.append((1, manager_1_id))

    if not levels:
        result.issues.append("Personel için değerlendirici zinciri bulunamadı.")
        return result

    for level, evaluator_id in levels:
        resolved = resolve_effective_evaluator(evaluator_id, manager_level=level, on_date=on_date)
        result.evaluators.append(resolved)
        if resolved.resolution_type in {"missing", "unresolved_leave"}:
            result.issues.append(resolved.message)

    return result


def write_assignment_audit_log(period_id: int, employee_id: int, effective: EffectiveEvaluator):
    if not AssignmentAuditLog or not db:
        return None

    row = AssignmentAuditLog(
        period_id=period_id,
        employee_id=employee_id,
        manager_level=effective.manager_level,
        original_evaluator_id=effective.original_evaluator_id,
        effective_evaluator_id=effective.effective_evaluator_id,
        resolution_type=effective.resolution_type,
        message=effective.message,
    )
    db.session.add(row)
    db.session.flush()
    return row


def ensure_effective_assignment(period_id: int, employee_id: int, effective: EffectiveEvaluator):
    if not EvaluationAssignment or not db:
        return None

    if not effective.effective_evaluator_id:
        return None

    period = db.session.get(PerformancePeriod, period_id)

    row = EvaluationAssignment.query.filter_by(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=effective.effective_evaluator_id,
        manager_level=effective.manager_level,
    ).first()

    if row:
        expected_due_date = build_assignment_due_date(period, getattr(row, "assigned_at", None))
        if getattr(row, "due_date", None) != expected_due_date:
            row.due_date = expected_due_date
            db.session.add(row)
            db.session.flush()
        return row

    row = EvaluationAssignment(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=effective.effective_evaluator_id,
        manager_level=effective.manager_level,
        status="bekliyor",
        due_date=build_assignment_due_date(period, None),
    )
    db.session.add(row)
    db.session.flush()
    return row


def sync_evaluation_summary(period_id: int, employee_id: int, effective_chain: EffectiveChainResult):
    if not PerformanceEvaluation or not db:
        return None

    row = PerformanceEvaluation.query.filter_by(period_id=period_id, employee_id=employee_id).first()
    if not row:
        row = PerformanceEvaluation(
            period_id=period_id,
            employee_id=employee_id,
            status="bekliyor",
        )
        db.session.add(row)
        db.session.flush()

    for eff in effective_chain.evaluators:
        if eff.manager_level == 1:
            row.level_1_evaluator_id = eff.effective_evaluator_id
        elif eff.manager_level == 2:
            row.level_2_evaluator_id = eff.effective_evaluator_id
        elif eff.manager_level == 3:
            row.level_3_evaluator_id = eff.effective_evaluator_id

    return row


def generate_effective_assignments(period_id: int, chains: list[dict[str, Any]], on_date: date | None = None) -> dict[str, Any]:
    if not db:
        return {"ok": False, "message": "db bağlantısı yok", "created": 0, "issues": []}

    created = 0
    issues: list[str] = []

    for chain in chains:
        employee_id = _get_id(chain.get("employee_id"))
        manager_1_id = _get_id(chain.get("manager_1_id"))
        manager_2_id = _get_id(chain.get("manager_2_id"))
        manager_3_id = _get_id(chain.get("manager_3_id"))

        effective_chain = build_effective_chain(
            employee_id=employee_id,
            manager_1_id=manager_1_id,
            manager_2_id=manager_2_id,
            manager_3_id=manager_3_id,
            on_date=on_date,
        )

        sync_evaluation_summary(period_id, employee_id, effective_chain)

        for eff in effective_chain.evaluators:
            before = EvaluationAssignment.query.count() if EvaluationAssignment else 0
            ensure_effective_assignment(period_id, employee_id, eff)
            write_assignment_audit_log(period_id, employee_id, eff)
            after = EvaluationAssignment.query.count() if EvaluationAssignment else before
            created += max(0, after - before)

        issues.extend([f"employee_id={employee_id}: {msg}" for msg in effective_chain.issues])

    db.session.commit()
    return {
        "ok": True,
        "message": "Efektif amir zinciri ile assignment üretimi tamamlandı.",
        "created": created,
        "issues": issues,
    }