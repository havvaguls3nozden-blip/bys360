from __future__ import annotations



from dataclasses import dataclass

from app.models import PerformanceEvaluation

from .constants import (
    WORKFLOW_DRAFT,
    WORKFLOW_LEVEL2_DONE,
    WORKFLOW_LEVEL3_DONE,
    WORKFLOW_RESUBMITTED,
    WORKFLOW_RETURNED,
    WORKFLOW_SEEN,
    WORKFLOW_SUBMITTED,
    WORKFLOW_WAITING_LEVEL3,
    WORKFLOW_WITHDRAWN,
)


@dataclass
class WorkflowState:
    key: str
    label: str
    can_level_1_edit: bool
    can_level_1_withdraw: bool
    can_level_2_return: bool
    can_level_2_complete: bool


WORKFLOW_STATE_MAP = {
    WORKFLOW_WAITING_LEVEL3: WorkflowState(WORKFLOW_WAITING_LEVEL3, "3. amir değerlendirmesi bekleniyor", False, False, False, False),
    WORKFLOW_LEVEL3_DONE: WorkflowState(WORKFLOW_LEVEL3_DONE, "3. amir işlemini tamamladı, şimdi 2. amir aşaması açık", False, False, False, False),
    WORKFLOW_DRAFT: WorkflowState(WORKFLOW_DRAFT, "2. amir ön değerlendirme aşamasında", True, False, False, False),
    WORKFLOW_SUBMITTED: WorkflowState(WORKFLOW_SUBMITTED, "2. amir kaydı 1. amire gönderdi", True, False, True, True),
    WORKFLOW_SEEN: WorkflowState(WORKFLOW_SEEN, "1. amir değerlendirmeyi görüntüledi", True, False, True, True),
    WORKFLOW_RETURNED: WorkflowState(WORKFLOW_RETURNED, "1. amir kaydı 2. amire iade etti", False, False, False, False),
    WORKFLOW_RESUBMITTED: WorkflowState(WORKFLOW_RESUBMITTED, "2. amir düzeltip yeniden 1. amire gönderdi", True, False, True, True),
    WORKFLOW_LEVEL2_DONE: WorkflowState(WORKFLOW_LEVEL2_DONE, "1. amir nihai değerlendirmeyi tamamladı", False, False, False, False),
    WORKFLOW_WITHDRAWN: WorkflowState(WORKFLOW_WITHDRAWN, "2. amir gönderimi geri çekti", False, False, False, False),
}


def normalize_workflow_status(evaluation: PerformanceEvaluation) -> str:
    status = (getattr(evaluation, 'workflow_status', None) or '').strip()
    if status:
        return status
    if getattr(evaluation, 'level_1_completed', False):
        return WORKFLOW_LEVEL2_DONE
    if getattr(evaluation, 'level_1_submitted_to_level_2_at', None):
        if getattr(evaluation, 'level_2_seen_level_1_at', None):
            return WORKFLOW_SEEN
        return WORKFLOW_SUBMITTED
    if getattr(evaluation, 'level_2_returned_to_level_1_at', None):
        return WORKFLOW_RETURNED
    if getattr(evaluation, 'level_3_completed', False):
        return WORKFLOW_LEVEL3_DONE
    if getattr(evaluation, 'level_3_evaluator_id', None):
        return WORKFLOW_WAITING_LEVEL3
    return WORKFLOW_DRAFT


def get_workflow_state(evaluation: PerformanceEvaluation) -> WorkflowState:
    key = normalize_workflow_status(evaluation)
    return WORKFLOW_STATE_MAP.get(key, WORKFLOW_STATE_MAP[WORKFLOW_DRAFT])


__all__ = [
    'WorkflowState',
    'WORKFLOW_STATE_MAP',
    'normalize_workflow_status',
    'get_workflow_state',
]