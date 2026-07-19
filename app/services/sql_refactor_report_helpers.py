
"""BYS360 SQL Refactor Faz 7 rapor/dashboard aggregate yardımcıları.

Bu servis yalnızca okuma amaçlıdır. Dashboard ve raporlama ekranlarında daha önce
Python listeleri üzerinde hesaplanan durum/puan sayaçlarını SQL COUNT/SUM/AVG/CASE
katmanına indirir. .env, migration veya DB yazımı içermez.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from collections.abc import Iterable

from sqlalchemy import and_, case, func, or_

from app.extensions import db
from app.models import PerformanceEvaluation


@dataclass(frozen=True)
class EvaluationMetricAggregate:
    total: int = 0
    completed: int = 0
    unpublished: int = 0
    pending_feedback: int = 0
    total_assignments: int = 0

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (
            int(self.total or 0),
            int(self.completed or 0),
            int(self.unpublished or 0),
            int(self.pending_feedback or 0),
            int(self.total_assignments or 0),
        )


@dataclass(frozen=True)
class PeriodEvaluationAggregate:
    period_id: int
    total_eval: int = 0
    completed_eval: int = 0
    partial_eval: int = 0
    pending_eval: int = 0
    avg_score: float = 0.0
    score_sum: float = 0.0
    score_count: int = 0
    high_score_count: int = 0
    low_score_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "period_id": int(self.period_id or 0),
            "total_eval": int(self.total_eval or 0),
            "completed_eval": int(self.completed_eval or 0),
            "partial_eval": int(self.partial_eval or 0),
            "pending_eval": int(self.pending_eval or 0),
            "avg_score": round(float(self.avg_score or 0), 2),
            "score_sum": float(self.score_sum or 0),
            "score_count": int(self.score_count or 0),
            "high_score_count": int(self.high_score_count or 0),
            "low_score_count": int(self.low_score_count or 0),
        }


def _safe_ids(values: Iterable[Any] | None) -> list[int]:
    ids: list[int] = []
    for value in values or []:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/sql_refactor_report_helpers.py:70)")
            continue
        if parsed > 0:
            ids.append(parsed)
    return sorted(set(ids))


def report_score_expr():
    """Rapor puanını SQL expression olarak döndürür.

    Mevcut Python resolve_report_score mantığı korunur:
    - 2. veya 3. seviye tamamlandıysa final_total_100,
    - sadece 1. seviye tamamlandıysa level_1_total_100,
    - aksi halde final_total_100.
    """
    return case(
        (
            or_(
                PerformanceEvaluation.level_2_completed.is_(True),
                PerformanceEvaluation.level_3_completed.is_(True),
            ),
            func.coalesce(PerformanceEvaluation.final_total_100, 0),
        ),
        (
            PerformanceEvaluation.level_1_completed.is_(True),
            func.coalesce(PerformanceEvaluation.level_1_total_100, 0),
        ),
        else_=func.coalesce(PerformanceEvaluation.final_total_100, 0),
    )


def scoreable_expr():
    """Rapor ortalamasına girecek puanlı kayıt koşulu."""
    return or_(
        PerformanceEvaluation.level_1_completed.is_(True),
        PerformanceEvaluation.level_2_completed.is_(True),
        PerformanceEvaluation.level_3_completed.is_(True),
    )


def build_dashboard_evaluation_metrics_sql(period_id: int | None, employee_ids: Iterable[Any] | None) -> EvaluationMetricAggregate:
    """Dashboard ana sayaçlarını SQL aggregate ile üretir."""
    scoped_employee_ids = _safe_ids(employee_ids)
    if not period_id or not scoped_employee_ids:
        return EvaluationMetricAggregate()

    completed_case = case((PerformanceEvaluation.status == "tamamlandi", 1), else_=0)
    unpublished_case = case(
        (
            and_(
                PerformanceEvaluation.status == "tamamlandi",
                PerformanceEvaluation.is_published_to_employee.is_(False),
            ),
            1,
        ),
        else_=0,
    )
    pending_feedback_case = case((PerformanceEvaluation.feedback_status == "bekliyor", 1), else_=0)

    row = (
        db.session.query(
            func.count(PerformanceEvaluation.id).label("total"),
            func.coalesce(func.sum(completed_case), 0).label("completed"),
            func.coalesce(func.sum(unpublished_case), 0).label("unpublished"),
            func.coalesce(func.sum(pending_feedback_case), 0).label("pending_feedback"),
        )
        .filter(
            PerformanceEvaluation.period_id == int(period_id),
            PerformanceEvaluation.employee_id.in_(scoped_employee_ids),
        )
        .one()
    )
    total = int(getattr(row, "total", 0) or 0)
    return EvaluationMetricAggregate(
        total=total,
        completed=int(getattr(row, "completed", 0) or 0),
        unpublished=int(getattr(row, "unpublished", 0) or 0),
        pending_feedback=int(getattr(row, "pending_feedback", 0) or 0),
        total_assignments=total,
    )


def build_period_evaluation_aggregates_sql(period_ids: Iterable[Any] | None, employee_ids: Iterable[Any] | None) -> dict[int, PeriodEvaluationAggregate]:
    """Rapor dönem kartları için status/puan özetlerini SQL GROUP BY ile üretir."""
    scoped_period_ids = _safe_ids(period_ids)
    scoped_employee_ids = _safe_ids(employee_ids)
    if not scoped_period_ids or not scoped_employee_ids:
        return {}

    score_expr = report_score_expr()
    completed_any = scoreable_expr()
    score_value = case((completed_any, score_expr), else_=None)
    completed_case = case((PerformanceEvaluation.status == "tamamlandi", 1), else_=0)
    partial_case = case((PerformanceEvaluation.status == "kismen_tamamlandi", 1), else_=0)
    pending_case = case((PerformanceEvaluation.status == "bekliyor", 1), else_=0)
    score_count_case = case((completed_any, 1), else_=0)
    high_score_case = case((and_(completed_any, score_expr > 90), 1), else_=0)
    low_score_case = case((and_(completed_any, score_expr < 70), 1), else_=0)

    rows = (
        db.session.query(
            PerformanceEvaluation.period_id.label("period_id"),
            func.count(PerformanceEvaluation.id).label("total_eval"),
            func.coalesce(func.sum(completed_case), 0).label("completed_eval"),
            func.coalesce(func.sum(partial_case), 0).label("partial_eval"),
            func.coalesce(func.sum(pending_case), 0).label("pending_eval"),
            func.coalesce(func.avg(score_value), 0).label("avg_score"),
            func.coalesce(func.sum(score_value), 0).label("score_sum"),
            func.coalesce(func.sum(score_count_case), 0).label("score_count"),
            func.coalesce(func.sum(high_score_case), 0).label("high_score_count"),
            func.coalesce(func.sum(low_score_case), 0).label("low_score_count"),
        )
        .filter(
            PerformanceEvaluation.period_id.in_(scoped_period_ids),
            PerformanceEvaluation.employee_id.in_(scoped_employee_ids),
        )
        .group_by(PerformanceEvaluation.period_id)
        .all()
    )

    result: dict[int, PeriodEvaluationAggregate] = {}
    for row in rows:
        period_id = int(getattr(row, "period_id", 0) or 0)
        if not period_id:
            continue
        result[period_id] = PeriodEvaluationAggregate(
            period_id=period_id,
            total_eval=int(getattr(row, "total_eval", 0) or 0),
            completed_eval=int(getattr(row, "completed_eval", 0) or 0),
            partial_eval=int(getattr(row, "partial_eval", 0) or 0),
            pending_eval=int(getattr(row, "pending_eval", 0) or 0),
            avg_score=round(float(getattr(row, "avg_score", 0) or 0), 2),
            score_sum=float(getattr(row, "score_sum", 0) or 0),
            score_count=int(getattr(row, "score_count", 0) or 0),
            high_score_count=int(getattr(row, "high_score_count", 0) or 0),
            low_score_count=int(getattr(row, "low_score_count", 0) or 0),
        )
    return result


__all__ = [
    "EvaluationMetricAggregate",
    "PeriodEvaluationAggregate",
    "build_dashboard_evaluation_metrics_sql",
    "build_period_evaluation_aggregates_sql",
    "report_score_expr",
    "scoreable_expr",
]
