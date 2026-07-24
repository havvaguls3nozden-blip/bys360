from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.extensions import db
from app.services.performance.delegation import (
    log_assignment_decision,
    resolve_effective_evaluator,
    resolve_employee_performance_mode,
)

from .common import build_assignment_due_date

logger = logging.getLogger(__name__)

try:
    import app.models as models
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    models = None  # type: ignore[assignment]

PerformancePeriod = getattr(models, "PerformancePeriod", None) if models else None
EvaluationAssignment = getattr(models, "EvaluationAssignment", None) if models else None
PerformanceEvaluation = getattr(models, "PerformanceEvaluation", None) if models else None


@dataclass
class EffectiveChainResult:
    employee_id: int
    period_id: int
    performance_mode: str
    created_assignments: int = 0
    infos: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def ensure_evaluation_summary(period_id: int, employee_id: int, chain_map: dict[int, int | None]) -> Any:
    if not PerformanceEvaluation or not db:
        return None
    row = PerformanceEvaluation.query.filter_by(period_id=period_id, employee_id=employee_id).first()
    if row:
        row.level_1_evaluator_id = chain_map.get(1)
        row.level_2_evaluator_id = chain_map.get(2)
        row.level_3_evaluator_id = chain_map.get(3)
        db.session.add(row)
        db.session.flush()
        return row

    row = PerformanceEvaluation(
        period_id=period_id,
        employee_id=employee_id,
        level_1_evaluator_id=chain_map.get(1),
        level_2_evaluator_id=chain_map.get(2),
        level_3_evaluator_id=chain_map.get(3),
        status="bekliyor",
    )
    db.session.add(row)
    db.session.flush()
    return row


def ensure_assignment(period_id: int, employee_id: int, evaluator_id: int | None, manager_level: int) -> bool:
    if not evaluator_id:
        return False
    if not EvaluationAssignment or not db or not PerformancePeriod:
        return False

    period = db.session.get(PerformancePeriod, period_id)

    existing = (
        EvaluationAssignment.query
        .filter_by(
            period_id=period_id,
            employee_id=employee_id,
            evaluator_id=evaluator_id,
            manager_level=manager_level,
        )
        .first()
    )
    if existing:
        expected_due_date = build_assignment_due_date(period, getattr(existing, "assigned_at", None))
        if getattr(existing, "due_date", None) != expected_due_date:
            existing.due_date = expected_due_date
            db.session.add(existing)
            db.session.flush()
        return False

    row = EvaluationAssignment(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=evaluator_id,
        manager_level=manager_level,
        status="bekliyor",
        due_date=build_assignment_due_date(period, None),
    )
    db.session.add(row)
    db.session.flush()
    return True


def apply_effective_chain(
    *,
    period_id: int,
    employee_id: int,
    manager_chain: dict[int, int | None],
    check_date=None,
) -> EffectiveChainResult:
    result = EffectiveChainResult(
        employee_id=employee_id,
        period_id=period_id,
        performance_mode="informational",
    )

    employee_leave = resolve_employee_performance_mode(employee_id, check_date=check_date)
    result.performance_mode = employee_leave.get("performance_mode") or "informational"

    if employee_leave.get("has_active_leave"):
        result.infos.append(
            f"Personel aktif izin/rapor kaydına sahip. Performans modu: {result.performance_mode}."
        )

    if result.performance_mode == "exclude":
        result.infos.append("Personel ilgili dönem için değerlendirmeden muaf tutuldu.")
        for level, evaluator_id in manager_chain.items():
            log_assignment_decision(
                period_id=period_id,
                employee_id=employee_id,
                manager_level=level,
                original_evaluator_id=evaluator_id,
                effective_evaluator_id=None,
                reason_type="excluded_due_leave",
                details={"performance_mode": result.performance_mode},
            )
        return result

    effective_chain: dict[int, int | None] = {}
    for level in sorted(manager_chain.keys()):
        original_evaluator_id = manager_chain.get(level)
        resolved = resolve_effective_evaluator(original_evaluator_id, level, check_date=check_date)
        effective_chain[level] = resolved.effective_evaluator_id

        if resolved.warning_level == "info":
            result.infos.append(f"L{level}: {resolved.note}")
        elif resolved.warning_level == "warning":
            result.warnings.append(f"L{level}: {resolved.note}")
        else:
            result.errors.append(f"L{level}: {resolved.note}")

        log_assignment_decision(
            period_id=period_id,
            employee_id=employee_id,
            manager_level=level,
            original_evaluator_id=resolved.original_evaluator_id,
            effective_evaluator_id=resolved.effective_evaluator_id,
            reason_type=resolved.reason_type,
            details={
                "delegated": resolved.delegated,
                "note": resolved.note,
                "performance_mode": result.performance_mode,
            },
        )

    ensure_evaluation_summary(period_id, employee_id, effective_chain)

    for level in sorted(effective_chain.keys()):
        created = ensure_assignment(period_id, employee_id, effective_chain.get(level), level)
        if created:
            result.created_assignments += 1

    db.session.flush()
    return result