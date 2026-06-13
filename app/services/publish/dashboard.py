from __future__ import annotations



from app.models import PerformanceEvaluation, PerformancePeriod
from .policy import PUBLISHABLE_FINAL_STATUSES, is_evaluation_publish_exempt


def get_publish_dashboard_stats(period: PerformancePeriod | None) -> dict[str, int]:
    if not period:
        return {
            'total': 0,
            'completed': 0,
            'published': 0,
            'unpublished': 0,
        }

    evaluations = [e for e in PerformanceEvaluation.query.filter_by(period_id=period.id).all() if not is_evaluation_publish_exempt(e)]
    total = len(evaluations)
    completed = len([e for e in evaluations if (getattr(e, 'status', '') or '').strip().lower() in PUBLISHABLE_FINAL_STATUSES])
    published = len([e for e in evaluations if bool(getattr(e, 'is_published_to_employee', False))])
    unpublished = total - published

    return {
        'total': total,
        'completed': completed,
        'published': published,
        'unpublished': unpublished,
    }