from __future__ import annotations

from app.core.datetime_utils import utc_now
from typing import Optional

from app.extensions import db
from app.models import EvaluationAssignment, PerformanceEvaluation

from .constants import (
    WORKFLOW_LEVEL2_DONE,
    WORKFLOW_LEVEL3_DONE,
    WORKFLOW_RESUBMITTED,
    WORKFLOW_RETURNED,
    WORKFLOW_SEEN,
    WORKFLOW_SUBMITTED,
    WORKFLOW_WITHDRAWN,
)
from .state import normalize_workflow_status
from .visibility import can_level_1_withdraw


def complete_level_3(evaluation: PerformanceEvaluation, level_3_assignment: EvaluationAssignment) -> None:
    evaluation.workflow_status = WORKFLOW_LEVEL3_DONE
    evaluation.level_3_completed = True
    level_3_assignment.status = 'tamamlandi'
    level_3_assignment.completed_at = utc_now()
    db.session.add(level_3_assignment)
    db.session.add(evaluation)


def submit_to_level_2(
    evaluation: PerformanceEvaluation,
    level_1_assignment: EvaluationAssignment,
    level_2_assignment: Optional[EvaluationAssignment],
) -> None:
    # Uyum katmanı adı korunuyor. Güncel akışta bu işlem 2. amirden 1. amire gönderimdir.
    now = utc_now()
    already_submitted = bool(getattr(evaluation, 'level_1_submitted_to_level_2_at', None))
    evaluation.workflow_status = WORKFLOW_RESUBMITTED if already_submitted else WORKFLOW_SUBMITTED
    evaluation.level_1_completed = False
    evaluation.level_2_completed = True
    evaluation.level_1_submitted_to_level_2_at = now
    evaluation.level_2_seen_level_1_at = None
    evaluation.level_2_returned_to_level_1_at = None
    evaluation.level_2_return_note = None
    evaluation.level_2_returned_by_id = None
    evaluation.level_1_last_resubmitted_at = now if already_submitted else None
    if level_2_assignment:
        level_2_assignment.status = 'tamamlandi'
        level_2_assignment.completed_at = now
        db.session.add(level_2_assignment)
    level_1_assignment.status = 'bekliyor'
    level_1_assignment.completed_at = None
    db.session.add(level_1_assignment)
    db.session.add(evaluation)


def withdraw_from_level_2(
    evaluation: PerformanceEvaluation,
    level_1_assignment: EvaluationAssignment,
    level_2_assignment: Optional[EvaluationAssignment],
) -> None:
    if not can_level_1_withdraw(evaluation):
        raise ValueError('1. amir değerlendirmeyi gördüğü için geri çekme yapılamaz.')
    evaluation.workflow_status = WORKFLOW_WITHDRAWN
    evaluation.level_1_completed = False
    evaluation.level_2_completed = False
    evaluation.level_2_seen_level_1_at = None
    evaluation.level_2_returned_to_level_1_at = None
    evaluation.level_2_return_note = None
    evaluation.level_2_returned_by_id = None
    if level_2_assignment:
        level_2_assignment.status = 'kismen_tamamlandi'
        level_2_assignment.completed_at = None
        db.session.add(level_2_assignment)
    level_1_assignment.status = 'bekliyor'
    level_1_assignment.completed_at = None
    db.session.add(level_1_assignment)
    db.session.add(evaluation)


def mark_seen_by_level_2(evaluation: PerformanceEvaluation, level_2_assignment: EvaluationAssignment) -> None:
    if normalize_workflow_status(evaluation) not in {WORKFLOW_SUBMITTED, WORKFLOW_RESUBMITTED}:
        return
    if getattr(evaluation, 'level_2_seen_level_1_at', None):
        return
    evaluation.workflow_status = WORKFLOW_SEEN
    evaluation.level_2_seen_level_1_at = utc_now()
    level_2_assignment.status = 'kismen_tamamlandi'
    db.session.add(level_2_assignment)
    db.session.add(evaluation)


def return_to_level_1(
    evaluation: PerformanceEvaluation,
    level_1_assignment: EvaluationAssignment,
    level_2_assignment: EvaluationAssignment,
    returned_by_user_id: int,
    note: str,
) -> None:
    # Uyum katmanı adı korunuyor. Güncel akışta iade 1. amirden 2. amire yapılır.
    clean_note = (note or '').strip()
    if not clean_note:
        raise ValueError('İade notu boş bırakılamaz.')
    now = utc_now()
    evaluation.workflow_status = WORKFLOW_RETURNED
    evaluation.level_1_completed = False
    evaluation.level_2_completed = False
    evaluation.level_2_returned_to_level_1_at = now
    evaluation.level_2_return_note = clean_note
    evaluation.level_2_returned_by_id = returned_by_user_id
    level_1_assignment.status = 'bekliyor'
    level_1_assignment.completed_at = None
    level_2_assignment.status = 'bekliyor'
    level_2_assignment.completed_at = None
    db.session.add(level_1_assignment)
    db.session.add(level_2_assignment)
    db.session.add(evaluation)


def complete_level_2(evaluation: PerformanceEvaluation, level_2_assignment: EvaluationAssignment) -> None:
    # Uyum katmanı adı korunuyor. Güncel akışta nihai tamamlama 1. amir tarafından yapılır.
    evaluation.workflow_status = WORKFLOW_LEVEL2_DONE
    evaluation.level_1_completed = True
    level_2_assignment.status = 'tamamlandi'
    level_2_assignment.completed_at = utc_now()
    db.session.add(level_2_assignment)
    db.session.add(evaluation)


__all__ = [
    'complete_level_3',
    'submit_to_level_2',
    'withdraw_from_level_2',
    'mark_seen_by_level_2',
    'return_to_level_1',
    'complete_level_2',
]