from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.models import OrganizationUnit, PerformanceEvaluation, User

from .common import _full_name, _safe_float, _safe_str


def filter_scope_users_by_query(scope_users: Iterable[Any], q: str):
    if not q:
        return list(scope_users)

    q_lower = _safe_str(q).lower()
    return [
        user
        for user in scope_users
        if q_lower in _safe_str(getattr(user, "full_name", "")).lower()
        or q_lower in _safe_str(getattr(user, "ad", "")).lower()
        or q_lower in _safe_str(getattr(user, "soyad", "")).lower()
        or q_lower in _safe_str(getattr(user, "sicil_no", "")).lower()
        or q_lower in _safe_str(getattr(user, "birim", "")).lower()
        or q_lower in _safe_str(getattr(user, "ust_birim", "")).lower()
        or q_lower in _safe_str(getattr(user, "unvan", "")).lower()
    ]


def score_for_report(evaluation: Any):
    if bool(getattr(evaluation, "level_2_completed", False)) or bool(getattr(evaluation, "level_3_completed", False)):
        return float(getattr(evaluation, "final_total_100", 0) or 0)
    if bool(getattr(evaluation, "level_1_completed", False)):
        return float(getattr(evaluation, "level_1_total_100", 0) or 0)
    return None


def resolve_report_score(evaluation: Any) -> float:
    score = score_for_report(evaluation)
    if score is None:
        score = float(getattr(evaluation, "final_total_100", 0) or 0)
    return round(float(score), 2)


def attach_report_scores(evaluations: Iterable[Any]):
    items = list(evaluations)
    for evaluation in items:
        evaluation.report_final_score = resolve_report_score(evaluation)
    return items

def build_team_compare_rows(period_id: int | None = None, manager_id: int | None = None) -> list[dict[str, Any]]:
    query = PerformanceEvaluation.query.join(User, User.id == PerformanceEvaluation.employee_id)
    if period_id is not None:
        query = query.filter(PerformanceEvaluation.period_id == period_id)

    rows: list[dict[str, Any]] = []

    for row in query.all():
        if bool(getattr(row, "evaluation_exempted", False)):
            continue
        employee = row.employee
        if manager_id is not None:
            chain_ids = {row.level_1_evaluator_id, row.level_2_evaluator_id, row.level_3_evaluator_id}
            if manager_id not in chain_ids:
                continue

        rows.append({
            "evaluation_id": row.id,
            "employee_id": employee.id if employee else None,
            "name": _full_name(employee),
            "birim": _safe_str(getattr(employee, "birim", "")),
            "ust_birim": _safe_str(getattr(employee, "ust_birim", "")),
            "score": _safe_float(getattr(row, "final_total_100", 0), 0),
            "status": _safe_str(getattr(row, "status", "")),
        })

    rows.sort(key=lambda item: (-item["score"], item["name"].lower()))
    return rows

def build_org_tree_from_units() -> list[dict[str, Any]]:
    units = (
        OrganizationUnit.query
        .order_by(
            OrganizationUnit.parent_id.asc().nullsfirst(),
            OrganizationUnit.sort_order.asc(),
            OrganizationUnit.name.asc(),
        )
        .all()
    )

    children_map: dict[int | None, list[OrganizationUnit]] = {}
    for unit in units:
        children_map.setdefault(unit.parent_id, []).append(unit)

    def _build(node: OrganizationUnit) -> dict[str, Any]:
        return {
            "id": node.id,
            "name": getattr(node, "name", "-"),
            "unit_type": getattr(node, "unit_type", "-"),
            "children": [_build(child) for child in children_map.get(node.id, [])],
        }

    return [_build(root) for root in children_map.get(None, [])]

__all__ = ['attach_report_scores', 'build_org_tree_from_units', 'build_team_compare_rows', 'filter_scope_users_by_query', 'resolve_report_score', 'score_for_report']