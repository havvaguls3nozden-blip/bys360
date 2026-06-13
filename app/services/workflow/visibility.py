from __future__ import annotations



from app.models import PerformanceEvaluation

from .constants import (
    WORKFLOW_DRAFT,
    WORKFLOW_RESUBMITTED,
    WORKFLOW_RETURNED,
    WORKFLOW_SEEN,
    WORKFLOW_SUBMITTED,
    VISIBLE_TO_LEVEL_2,
)
from .state import normalize_workflow_status


def can_level_2_see(evaluation: PerformanceEvaluation) -> bool:
    return normalize_workflow_status(evaluation) in VISIBLE_TO_LEVEL_2


def can_level_1_edit(evaluation: PerformanceEvaluation) -> bool:
    # Güncel akışta 1. amir nihai aşamadır. 2. amir gönderdiğinde
    # veya iade sonrası tekrar geldiğinde 1. amir formu düzenleyebilmelidir.
    return normalize_workflow_status(evaluation) in {
        WORKFLOW_DRAFT,
        WORKFLOW_SUBMITTED,
        WORKFLOW_SEEN,
        WORKFLOW_RESUBMITTED,
        WORKFLOW_RETURNED,
    }


def can_level_1_withdraw(evaluation: PerformanceEvaluation) -> bool:
    # Uyum katmanı adı korunuyor; pratikte bu, 2. amirin 1. amire gönderdiği
    # kaydı 1. amir henüz açmadan önce geri çekebilmesi için kullanılır.
    return (
        normalize_workflow_status(evaluation) in {WORKFLOW_SUBMITTED, WORKFLOW_RESUBMITTED}
        and not getattr(evaluation, 'level_2_seen_level_1_at', None)
    )


__all__ = [
    'can_level_2_see',
    'can_level_1_edit',
    'can_level_1_withdraw',
]