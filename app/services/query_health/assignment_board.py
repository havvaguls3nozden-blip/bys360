
"""Atama panosu sorgu ve filtre yardimcilari."""
from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.models import EvaluationAssignment, PerformanceEvaluation, PerformancePeriod, User

from .constants import ALLOWED_ASSIGNMENT_STATUSES, WORKFLOW_FILTERS


def build_assignment_board_query(*, evaluator_id: int | None = None, admin_mode: bool = False):
    query = (
        EvaluationAssignment.query.join(User, EvaluationAssignment.employee_id == User.id)
        .join(PerformancePeriod, EvaluationAssignment.period_id == PerformancePeriod.id)
        .options(
            joinedload(EvaluationAssignment.employee),  # type: ignore[arg-type]
            joinedload(EvaluationAssignment.evaluator),  # type: ignore[arg-type]
            joinedload(EvaluationAssignment.period),  # type: ignore[arg-type]
        )
    )
    if not admin_mode and evaluator_id is not None:
        query = query.filter(EvaluationAssignment.evaluator_id == evaluator_id)
    return query


def apply_assignment_board_filters(query, *, q: str = "", status: str = "", unit: str = "", workflow_status: str = ""):
    if unit:
        query = query.filter(User.birim == unit)

    if q:
        like_q = f"%{q}%"
        query = query.filter(
            or_(
                User.full_name_cache.ilike(like_q),
                User.ad.ilike(like_q),
                User.soyad.ilike(like_q),
                User.sicil_no.ilike(like_q),
                User.birim.ilike(like_q),
                User.ust_birim.ilike(like_q),
                User.unvan.ilike(like_q),
                PerformancePeriod.title.ilike(like_q),
            )
        )

    if status in ALLOWED_ASSIGNMENT_STATUSES:
        query = query.filter(EvaluationAssignment.status == status)
    else:
        status = ""

    if workflow_status in WORKFLOW_FILTERS:
        query = (
            query.outerjoin(
                PerformanceEvaluation,
                (PerformanceEvaluation.period_id == EvaluationAssignment.period_id)
                & (PerformanceEvaluation.employee_id == EvaluationAssignment.employee_id),
            ).filter(PerformanceEvaluation.workflow_status == workflow_status)
        )
    else:
        workflow_status = ""

    return query, status, workflow_status


def ordered_assignment_rows(query):
    rows = (
        query.order_by(
            User.birim.asc().nullsfirst(),
            User.ad.asc(),
            User.soyad.asc(),
            EvaluationAssignment.id.desc(),
        ).all()
    )
    order_map = {3: 0, 2: 1, 1: 2}
    return sorted(rows, key=lambda row: (((getattr(row.employee, 'birim', '') or '')), (getattr(row.employee, 'ad', '') or ''), (getattr(row.employee, 'soyad', '') or ''), order_map.get(getattr(row, 'manager_level', 99), 99), -(getattr(row, 'id', 0) or 0)))