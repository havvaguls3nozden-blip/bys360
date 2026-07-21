from __future__ import annotations

from typing import Any

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import PerformanceEvaluation, PerformancePeriod
from app.services.performance.low_score_process_service import (
    ensure_low_score_process_for_evaluation,
    ensure_low_score_processes_for_period,
)

from .policy import is_evaluation_publish_exempt, is_evaluation_publishable


def publish_evaluation(evaluation: PerformanceEvaluation, acted_by: Any) -> tuple[bool, str]:
    period = getattr(evaluation, 'period', None)
    ensure_low_score_process_for_evaluation(evaluation, actor_user_id=getattr(acted_by, 'id', None))
    ok, reason = is_evaluation_publishable(period, evaluation)
    if not ok:
        return False, reason

    now = utc_now()
    evaluation.is_published_to_employee = True
    evaluation.published_to_employee_at = now
    evaluation.published_to_employee_by_id = getattr(acted_by, 'id', None)

    if period:
        period.results_published = True
        period.published_at = now
        period.published_by_id = getattr(acted_by, 'id', None)

    return True, 'Değerlendirme personele yayınlandı.'


def unpublish_evaluation(evaluation: PerformanceEvaluation, acted_by: Any | None = None) -> tuple[bool, str]:
    if not evaluation:
        return False, 'Değerlendirme bulunamadı.'

    evaluation.is_published_to_employee = False
    evaluation.published_to_employee_at = None
    evaluation.published_to_employee_by_id = getattr(acted_by, 'id', None)

    period = getattr(evaluation, 'period', None)
    if period and not any(
        bool(getattr(item, 'is_published_to_employee', False))
        for item in PerformanceEvaluation.query.filter_by(period_id=period.id).all()
        if item.id != evaluation.id
    ):
        period.results_published = False
        period.published_at = None
        period.published_by_id = getattr(acted_by, 'id', None)

    return True, 'Değerlendirme yayından kaldırıldı.'


def publish_period_results(period: PerformancePeriod, acted_by: Any) -> dict[str, Any]:
    evaluations = (
        PerformanceEvaluation.query
        .filter_by(period_id=period.id)
        .order_by(PerformanceEvaluation.id.asc())
        .all()
    )

    ensure_low_score_processes_for_period(period, actor_user_id=getattr(acted_by, 'id', None))

    now = utc_now()
    published_count = 0
    skipped: list[dict[str, Any]] = []
    published_evaluation_ids: list[int] = []

    for evaluation in evaluations:
        if is_evaluation_publish_exempt(evaluation):
            continue
        ok, reason = is_evaluation_publishable(period, evaluation)
        if not ok:
            skipped.append({
                'evaluation_id': evaluation.id,
                'employee_id': evaluation.employee_id,
                'reason': reason,
            })
            continue

        evaluation.is_published_to_employee = True
        evaluation.published_to_employee_at = now
        evaluation.published_to_employee_by_id = getattr(acted_by, 'id', None)
        published_count += 1
        published_evaluation_ids.append(evaluation.id)

    if published_count > 0:
        period.results_published = True
        period.published_at = now
        period.published_by_id = getattr(acted_by, 'id', None)

    db.session.flush()

    return {
        'published_count': published_count,
        'skipped': skipped,
        'published_evaluation_ids': published_evaluation_ids,
    }


def unpublish_period_results(period: PerformancePeriod, acted_by: Any) -> dict[str, Any]:
    evaluations = (
        PerformanceEvaluation.query
        .filter_by(period_id=period.id)
        .order_by(PerformanceEvaluation.id.asc())
        .all()
    )

    unpublished_ids: list[int] = []
    for evaluation in evaluations:
        if bool(getattr(evaluation, 'is_published_to_employee', False)):
            unpublished_ids.append(evaluation.id)
        evaluation.is_published_to_employee = False
        evaluation.published_to_employee_at = None
        evaluation.published_to_employee_by_id = getattr(acted_by, 'id', None)

    period.results_published = False
    period.published_at = None
    period.published_by_id = getattr(acted_by, 'id', None)

    db.session.flush()

    return {
        'unpublished_count': len(unpublished_ids),
        'unpublished_evaluation_ids': unpublished_ids,
    }