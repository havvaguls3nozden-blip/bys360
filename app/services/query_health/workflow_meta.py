
"""Atama listeleri icin is akisi rozeti ve filtre yardimcilari."""
from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.models import EvaluationAssignment, PerformanceEvaluation
from app.services.evaluation_workflow_service import get_workflow_state

from .constants import WORKFLOW_BADGE_CLASS_MAP, WORKFLOW_FILTER_ORDER

DEFAULT_WORKFLOW_KEY = "taslak_1_amir"
DEFAULT_WORKFLOW_LABEL = "1. amirde taslak"


def attach_workflow_meta(assignments: list[EvaluationAssignment]) -> dict[str, int]:
    if not assignments:
        return {}

    period_employee_pairs = {(a.period_id, a.employee_id) for a in assignments}
    filters = [
        ((PerformanceEvaluation.period_id == period_id) & (PerformanceEvaluation.employee_id == employee_id))
        for period_id, employee_id in period_employee_pairs
    ]

    evaluations = []
    if filters:
        evaluations = (
            PerformanceEvaluation.query.options(
                joinedload(PerformanceEvaluation.period),
                joinedload(PerformanceEvaluation.employee),
            )
            .filter(or_(*filters))
            .all()
        )

    evaluation_map = {(e.period_id, e.employee_id): e for e in evaluations}
    workflow_counts: dict[str, int] = {}

    for assignment in assignments:
        evaluation = evaluation_map.get((assignment.period_id, assignment.employee_id))
        workflow = get_workflow_state(evaluation) if evaluation else None
        assignment.workflow_key = workflow.key if workflow else DEFAULT_WORKFLOW_KEY
        assignment.workflow_label = workflow.label if workflow else DEFAULT_WORKFLOW_LABEL
        assignment.workflow_badge_class = WORKFLOW_BADGE_CLASS_MAP.get(assignment.workflow_key, "neutral")
        workflow_counts[assignment.workflow_key] = workflow_counts.get(assignment.workflow_key, 0) + 1

    return workflow_counts


def build_workflow_filter_items(assignments: list[EvaluationAssignment], selected_key: str = "") -> list[dict[str, object]]:
    counts = attach_workflow_meta(assignments)
    total = len(assignments)
    items: list[dict[str, object]] = []
    for key, label, tone in WORKFLOW_FILTER_ORDER:
        count = total if not key else counts.get(key, 0)
        items.append(
            {
                "key": key,
                "label": label,
                "count": count,
                "tone": tone,
                "selected": key == (selected_key or ""),
            }
        )
    return items