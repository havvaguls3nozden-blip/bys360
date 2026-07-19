from __future__ import annotations

from app.models import EvaluationAssignment, PerformanceEvaluation, User
# BYS360_PHASE8_4_PREVIEW_IMPORT_START
from app.services.performance.period_scope_assignment import filter_period_scope_employees
# BYS360_PHASE8_4_PREVIEW_IMPORT_END

from .chain import build_chain_debug_payload, build_resolved_chain
from .schedule import build_due_date_for_period, period_schedule_snapshot
from .visibility import build_previous_level_comment_snapshot
from .weights import resolve_weight_plan
from .workflow import current_actionable_levels
from .rules import normalize_level_mode, resolve_chain_policy
from .dto import AssignmentPreview


def _existing_assignments(period_id: int, employee_id: int) -> list[EvaluationAssignment]:
    return (
        EvaluationAssignment.query.filter_by(period_id=period_id, employee_id=employee_id)
        .order_by(EvaluationAssignment.manager_level.asc(), EvaluationAssignment.id.asc())
        .all()
    )


def _existing_evaluation(period_id: int, employee_id: int):
    return PerformanceEvaluation.query.filter_by(period_id=period_id, employee_id=employee_id).first()


def build_assignment_preview(employee, period) -> dict[str, object]:
    resolved_chain = build_resolved_chain(employee=employee, period=period)
    policy = resolve_chain_policy(employee)
    level_mode = normalize_level_mode(period)
    weight_plan = resolve_weight_plan(employee=employee, period=period, resolved_chain=resolved_chain)
    due_date = build_due_date_for_period(period)
    existing_assignments = _existing_assignments(period.id, employee.id) if period else []
    existing_by_level = {item.manager_level: item for item in existing_assignments}
    evaluation = _existing_evaluation(period.id, employee.id) if period else None
    previews: list[AssignmentPreview] = []
    for level in resolved_chain.order:
        chain_level = resolved_chain.levels.get(level)
        if not chain_level:
            continue
        existing = existing_by_level.get(level)
        previews.append(
            AssignmentPreview(
                level=level,
                label=chain_level.label,
                evaluator_id=chain_level.evaluator_id,
                evaluator_name=chain_level.evaluator_name,
                evaluator_role=chain_level.evaluator_role,
                due_date_iso=due_date.isoformat() if due_date else None,
                score_enabled=chain_level.score_enabled,
                visible_previous_levels=[item['level'] for item in build_previous_level_comment_snapshot(evaluation=evaluation, current_level=level, policy=policy, level_mode=level_mode)],
                existing_status=getattr(existing, 'status', None),
                existing_assignment_id=getattr(existing, 'id', None),
            )
        )
    return {
        'employee': {
            'id': employee.id,
            'sicil_no': employee.sicil_no,
            'full_name': employee.full_name,
            'role': employee.role,
            'unvan': employee.unvan,
            'birim': employee.birim,
            'ust_birim': employee.ust_birim,
        },
        'period': {
            'id': getattr(period, 'id', None),
            'title': getattr(period, 'title', None),
            **period_schedule_snapshot(period),
        },
        'resolved_chain': resolved_chain.to_dict(),
        'weight_plan': weight_plan.to_dict(),
        'assignments': [item.to_dict() for item in previews],
        'actionable_levels': current_actionable_levels(resolved_chain=resolved_chain, existing_assignments=existing_assignments),
        'previous_comments': {
            str(level): build_previous_level_comment_snapshot(evaluation=evaluation, current_level=level, policy=policy, level_mode=level_mode)
            for level in resolved_chain.order
            if level in resolved_chain.levels
        },
        'debug': build_chain_debug_payload(employee=employee, period=period),
    }


def build_assignment_previews_for_period(period, limit: int = 25, employee_ids: list[int] | None = None) -> list[dict[str, object]]:
    query = User.query.filter(User.is_active.is_(True))
    if employee_ids:
        query = query.filter(User.id.in_(employee_ids))
    else:
        query = query.filter(~User.role.in_(['admin'])).order_by(User.ad.asc(), User.soyad.asc()).limit(limit)
    return [build_assignment_preview(employee=user, period=period) for user in filter_period_scope_employees(query.all(), period)]

# BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_BOUND
# 3. amir opsiyonelliği ve sahte görev temizliği phase4_third_manager_policy üzerinden izlenir.

# BYS360_PERFORMANCE_COMPLETION_PHASE8_PERIOD_SCOPE_BOUND
# Çoklu dönem ve kapsamlı görev üretimi phase8_period_scope_policy sözleşmesini kullanır.

# BYS360_PERFORMANCE_COMPLETION_PHASE9_REMINDER_BOUND
# Otomatik hatırlatma ve aksatan amir bildirimi phase9_reminder_policy sözleşmesini kullanır.
