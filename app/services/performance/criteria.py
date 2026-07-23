from __future__ import annotations

from typing import Union

from app.models import PerformanceCriteria, PerformanceEvaluation, PerformanceEvaluationItem

from .common import _safe_float


def get_active_criteria() -> list[PerformanceCriteria]:
    return (
        PerformanceCriteria.query
        .filter_by(is_active=True)
        .order_by(PerformanceCriteria.sort_order.asc(), PerformanceCriteria.id.asc())
        .all()
    )

def get_level_items_map(evaluation_id: int, manager_level: int) -> dict[int, PerformanceEvaluationItem]:
    rows = (
        PerformanceEvaluationItem.query.filter_by(
            evaluation_id=evaluation_id,
            manager_level=manager_level,
        )
        .order_by(PerformanceEvaluationItem.criteria_id.asc(), PerformanceEvaluationItem.id.desc())
        .all()
    )
    result: dict[int, PerformanceEvaluationItem] = {}
    for row in rows:
        criteria_id = int(getattr(row, "criteria_id", 0) or 0)
        if criteria_id and criteria_id not in result:
            result[criteria_id] = row
    return result

def level_1_gave_any_three(evaluation_or_id: int | PerformanceEvaluation) -> bool:
    evaluation_id = evaluation_or_id.id if hasattr(evaluation_or_id, "id") else int(evaluation_or_id)
    items = get_level_items_map(evaluation_id, 1).values()
    return any(_safe_float(getattr(item, "score", None), 0) == 3 for item in items)

def validate_criteria_total() -> tuple[bool, float]:
    rows = PerformanceCriteria.query.filter_by(is_active=True).all()
    total = round(sum(_safe_float(getattr(row, "weight", 0), 0) for row in rows), 2)
    return total == 100.0, total

def score_to_100(score: float, score_min: float = 1.0, score_max: float = 5.0) -> float:
    value = _safe_float(score, 0.0)
    if value <= 0:
        return 0.0
    value = max(score_min, min(score_max, value))
    return round((value / score_max) * 100.0, 2)

__all__ = ['get_active_criteria', 'get_level_items_map', 'level_1_gave_any_three', 'validate_criteria_total', 'score_to_100']