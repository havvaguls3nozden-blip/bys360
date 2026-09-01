from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from app.models import EvaluationAssignment, PerformanceEvaluation, User
from app.services.hierarchy_health_service import (
    build_hierarchy_health_rows,
    summarize_hierarchy_health,
)
from app.services.performance.assignments import (
    build_assignment_log_severity_summary,
    build_assignment_log_summary,
    get_latest_assignment_generation_logs,
    is_informational_special_case,
)

LEVEL_TO_EVALUATION_FIELD = {
    1: "level_1_evaluator_id",
    2: "level_2_evaluator_id",
    3: "level_3_evaluator_id",
}


def _safe_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _clean_text(value) -> str:
    return str(value or "").strip()


def _name(user: User | None) -> str:
    if not user:
        return "-"
    full_name = _clean_text(getattr(user, "full_name", None))
    if full_name:
        return full_name
    return f"{_clean_text(getattr(user, 'ad', None))} {_clean_text(getattr(user, 'soyad', None))}".strip() or "-"


def _unit(user: User | None) -> str:
    if not user:
        return "-"
    return _clean_text(getattr(user, "birim", None)) or _clean_text(getattr(user, "ust_birim", None)) or "-"


def _is_open(status: str | None) -> bool:
    folded = _clean_text(status).lower()
    return folded not in {"tamamlandi", "completed"}


def _build_duplicate_rows(assignments: list[EvaluationAssignment]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int], list[EvaluationAssignment]] = defaultdict(list)
    for row in assignments:
        grouped[(int(row.employee_id), int(row.manager_level or 0))].append(row)

    duplicate_rows: list[dict[str, Any]] = []
    for (_, manager_level), rows in grouped.items():
        if len(rows) <= 1:
            continue
        ordered = sorted(rows, key=lambda item: (getattr(item, "assigned_at", None) or getattr(item, "created_at", None), item.id or 0), reverse=True)
        employee = getattr(ordered[0], "employee", None)
        evaluators = []
        seen = set()
        for row in ordered:
            evaluator = getattr(row, "evaluator", None)
            label = _name(evaluator)
            if label not in seen:
                seen.add(label)
                evaluators.append(label)
        duplicate_rows.append({
            "employee": employee,
            "employee_name": _name(employee),
            "employee_unit": _unit(employee),
            "manager_level": manager_level,
            "assignment_ids": [row.id for row in ordered if getattr(row, "id", None)],
            "row_count": len(ordered),
            "evaluators": evaluators,
            "status_labels": [
                _clean_text(getattr(row, "status", None)) or "bekliyor"
                for row in ordered
            ],
            "source_labels": [
                _clean_text(getattr(row, "assignment_source", None)) or "direct"
                for row in ordered
            ],
        })
    duplicate_rows.sort(key=lambda item: (-_safe_int(item.get("row_count")), _clean_text(item.get("employee_name")).lower(), _safe_int(item.get("manager_level"))))
    return duplicate_rows


def _build_mismatch_rows(
    evaluations: list[PerformanceEvaluation],
    assignments: list[EvaluationAssignment],
) -> list[dict[str, Any]]:
    assignment_map: dict[tuple[int, int], list[EvaluationAssignment]] = defaultdict(list)
    for row in assignments:
        assignment_map[(int(row.employee_id), int(row.manager_level or 0))].append(row)

    mismatch_rows: list[dict[str, Any]] = []
    for evaluation in evaluations:
        employee = getattr(evaluation, "employee", None)
        for level, field_name in LEVEL_TO_EVALUATION_FIELD.items():
            expected_id = getattr(evaluation, field_name, None)
            if not expected_id:
                continue
            level_assignments = assignment_map.get((int(evaluation.employee_id), int(level)), [])
            if not level_assignments:
                mismatch_rows.append({
                    "employee": employee,
                    "employee_name": _name(employee),
                    "employee_unit": _unit(employee),
                    "manager_level": level,
                    "expected_manager_id": int(expected_id),
                    "expected_manager_name": "-",
                    "actual_manager_names": [],
                    "reason": "Beklenen amir için görev satırı bulunamadı.",
                })
                continue

            expected_match = False
            actual_manager_names = []
            expected_manager_name = "-"
            for assignment in level_assignments:
                expected_manager = getattr(assignment, "original_evaluator", None)
                if expected_manager and expected_manager.id == expected_id:
                    expected_manager_name = _name(expected_manager)
                elif getattr(assignment, "evaluator", None) and getattr(assignment.evaluator, "id", None) == expected_id:
                    expected_manager_name = _name(getattr(assignment, "evaluator", None))

                actual_manager_names.append(_name(getattr(assignment, "evaluator", None)))
                if getattr(assignment, "original_evaluator_id", None) == expected_id or getattr(assignment, "evaluator_id", None) == expected_id:
                    expected_match = True

            if not expected_match:
                mismatch_rows.append({
                    "employee": employee,
                    "employee_name": _name(employee),
                    "employee_unit": _unit(employee),
                    "manager_level": level,
                    "expected_manager_id": int(expected_id),
                    "expected_manager_name": expected_manager_name,
                    "actual_manager_names": [name for name in actual_manager_names if name and name != "-"],
                    "reason": "Değerlendirme kaydı ile görev satırı farklı amire işaret ediyor.",
                })
    mismatch_rows.sort(key=lambda item: (_clean_text(item.get("employee_name")).lower(), _safe_int(item.get("manager_level"))))
    return mismatch_rows


def _build_orphan_rows(
    evaluations: list[PerformanceEvaluation],
    assignments: list[EvaluationAssignment],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evaluation_by_employee = {int(row.employee_id): row for row in evaluations}
    assignment_groups: dict[int, list[EvaluationAssignment]] = defaultdict(list)
    for row in assignments:
        assignment_groups[int(row.employee_id)].append(row)

    orphan_evaluations: list[dict[str, Any]] = []
    for evaluation in evaluations:
        if assignment_groups.get(int(evaluation.employee_id)):
            continue
        employee = getattr(evaluation, "employee", None)
        orphan_evaluations.append({
            "employee": employee,
            "employee_name": _name(employee),
            "employee_unit": _unit(employee),
            "status": _clean_text(getattr(evaluation, "status", None)) or "bekliyor",
            "workflow_status": _clean_text(getattr(evaluation, "workflow_status", None)) or "-",
            "exempted": bool(getattr(evaluation, "evaluation_exempted", False)),
        })

    orphan_assignments: list[dict[str, Any]] = []
    for employee_id, rows in assignment_groups.items():
        if employee_id in evaluation_by_employee:
            continue
        employee = getattr(rows[0], "employee", None) if rows else None
        orphan_assignments.append({
            "employee": employee,
            "employee_name": _name(employee),
            "employee_unit": _unit(employee),
            "manager_levels": sorted({_safe_int(getattr(row, "manager_level", None)) for row in rows}),
            "assignment_ids": [row.id for row in rows if getattr(row, "id", None)],
            "sources": sorted({_clean_text(getattr(row, "assignment_source", None)) or "direct" for row in rows}),
        })

    orphan_evaluations.sort(key=lambda item: _clean_text(item.get("employee_name")).lower())
    orphan_assignments.sort(key=lambda item: _clean_text(item.get("employee_name")).lower())
    return orphan_evaluations, orphan_assignments


def _build_manager_pressure_rows(assignments: list[EvaluationAssignment]) -> list[dict[str, Any]]:
    buckets: dict[int, dict[str, Any]] = {}
    for row in assignments:
        evaluator = getattr(row, "evaluator", None)
        if not evaluator:
            continue
        bucket = buckets.setdefault(int(evaluator.id), {
            "manager": evaluator,
            "manager_name": _name(evaluator),
            "manager_unit": _unit(evaluator),
            "open_count": 0,
            "overdue_count": 0,
            "delegated_count": 0,
            "uncovered_count": 0,
            "employee_names": set(),
        })
        if _is_open(getattr(row, "status", None)):
            bucket["open_count"] += 1
        if bool(getattr(row, "is_overdue", False)):
            bucket["overdue_count"] += 1
        source = _clean_text(getattr(row, "assignment_source", None)).lower() or "direct"
        if source == "delegated":
            bucket["delegated_count"] += 1
        elif source == "uncovered":
            bucket["uncovered_count"] += 1
        employee = getattr(row, "employee", None)
        if employee:
            bucket["employee_names"].add(_name(employee))

    rows = []
    for bucket in buckets.values():
        bucket["employee_names"] = sorted(bucket["employee_names"])[:6]
        bucket["risk_score"] = (
            int(bucket["open_count"]) * 2
            + int(bucket["overdue_count"]) * 3
            + int(bucket["delegated_count"]) * 2
            + int(bucket["uncovered_count"]) * 4
        )
        rows.append(bucket)
    rows.sort(
        key=lambda item: (
            -_safe_int(item.get("risk_score")),
            -_safe_int(item.get("overdue_count")),
            -_safe_int(item.get("open_count")),
            _clean_text(item.get("manager_name")).lower(),
        )
    )
    return rows[:12]


def build_performance_task_health_report(period, scope_user_ids: Iterable[int] | None = None) -> dict[str, Any]:
    empty_summary = {
        "employee_count": 0,
        "evaluation_count": 0,
        "assignment_count": 0,
        "duplicate_level_count": 0,
        "mismatch_count": 0,
        "orphan_evaluation_count": 0,
        "orphan_assignment_count": 0,
        "delegated_count": 0,
        "uncovered_count": 0,
        "overdue_count": 0,
        "chain_issue_count": 0,
        "chain_conflict_count": 0,
        "balanced_chain_count": 0,
    }
    if not period:
        return {
            "summary": empty_summary,
            "assignments": [],
            "evaluations": [],
            "health_rows": [],
            "health_summary": summarize_hierarchy_health([]),
            "duplicate_rows": [],
            "mismatch_rows": [],
            "orphan_evaluations": [],
            "orphan_assignments": [],
            "manager_pressure_rows": [],
            "coverage_log_rows": [],
            "coverage_summary": build_assignment_log_summary([]),
            "coverage_severity_summary": build_assignment_log_severity_summary([]),
        }

    normalized_scope_user_ids: set[int] | None
    if scope_user_ids is None:
        normalized_scope_user_ids = None
    else:
        normalized_scope_user_ids = {int(value) for value in scope_user_ids if value}

    user_query = User.query.filter(User.role != "admin", User.is_active.is_(True))
    if normalized_scope_user_ids is not None:
        user_query = user_query.filter(User.id.in_(list(normalized_scope_user_ids)))
    scoped_users = user_query.order_by(User.ad.asc(), User.soyad.asc()).all()
    scoped_user_ids = {int(user.id) for user in scoped_users}

    evaluation_query = PerformanceEvaluation.query.filter_by(period_id=period.id)
    assignment_query = EvaluationAssignment.query.filter_by(period_id=period.id)
    if normalized_scope_user_ids is not None:
        if scoped_user_ids:
            evaluation_query = evaluation_query.filter(PerformanceEvaluation.employee_id.in_(list(scoped_user_ids)))
            assignment_query = assignment_query.filter(EvaluationAssignment.employee_id.in_(list(scoped_user_ids)))
        else:
            evaluation_query = evaluation_query.filter(PerformanceEvaluation.employee_id == -1)
            assignment_query = assignment_query.filter(EvaluationAssignment.employee_id == -1)

    evaluations = evaluation_query.order_by(PerformanceEvaluation.employee_id.asc()).all()
    assignments = assignment_query.order_by(EvaluationAssignment.employee_id.asc(), EvaluationAssignment.manager_level.asc(), EvaluationAssignment.id.asc()).all()

    duplicate_rows = _build_duplicate_rows(assignments)
    mismatch_rows = _build_mismatch_rows(evaluations, assignments)
    orphan_evaluations, orphan_assignments = _build_orphan_rows(evaluations, assignments)
    manager_pressure_rows = _build_manager_pressure_rows(assignments)

    coverage_payload = get_latest_assignment_generation_logs(
        period.id,
        limit=800,
        employee_ids=list(scoped_user_ids) if normalized_scope_user_ids is not None else None,
    )
    coverage_log_rows = [
        row for row in (coverage_payload.get("rows") or [])
        if not is_informational_special_case(getattr(row, "reason", None), getattr(row, "event_type", None))
    ]
    coverage_summary = build_assignment_log_summary(coverage_log_rows)
    coverage_severity_summary = build_assignment_log_severity_summary(coverage_log_rows)

    health_rows = build_hierarchy_health_rows(scoped_users)
    health_summary = summarize_hierarchy_health(health_rows)

    summary = {
        "employee_count": len(scoped_users),
        "evaluation_count": len(evaluations),
        "assignment_count": len(assignments),
        "duplicate_level_count": len(duplicate_rows),
        "mismatch_count": len(mismatch_rows),
        "orphan_evaluation_count": len(orphan_evaluations),
        "orphan_assignment_count": len(orphan_assignments),
        "delegated_count": sum(1 for row in assignments if (_clean_text(getattr(row, "assignment_source", None)).lower() == "delegated")),
        "uncovered_count": sum(1 for row in assignments if (_clean_text(getattr(row, "assignment_source", None)).lower() == "uncovered")) or _safe_int(coverage_summary.get("uncovered")),
        "overdue_count": sum(1 for row in assignments if bool(getattr(row, "is_overdue", False))),
        "chain_issue_count": _safe_int(health_summary.get("missing_chain_count")),
        "chain_conflict_count": _safe_int(health_summary.get("conflict_count")),
        "balanced_chain_count": _safe_int(health_summary.get("balanced_count")),
    }

    return {
        "summary": summary,
        "assignments": assignments,
        "evaluations": evaluations,
        "health_rows": health_rows,
        "health_summary": health_summary,
        "duplicate_rows": duplicate_rows,
        "mismatch_rows": mismatch_rows,
        "orphan_evaluations": orphan_evaluations,
        "orphan_assignments": orphan_assignments,
        "manager_pressure_rows": manager_pressure_rows,
        "coverage_log_rows": coverage_log_rows,
        "coverage_summary": coverage_summary,
        "coverage_severity_summary": coverage_severity_summary,
    }