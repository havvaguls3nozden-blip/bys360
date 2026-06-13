
"""Dashboard sorgu sagligi yardimcilari."""
from __future__ import annotations

from sqlalchemy.orm import joinedload

from app.models import EvaluationAssignment, FeedbackMeeting


def build_dashboard_assignment_query(user_id: int, *, statuses: tuple[str, ...] | None = None):
    query = (
        EvaluationAssignment.query.options(
            joinedload(EvaluationAssignment.employee),
            joinedload(EvaluationAssignment.evaluator),
            joinedload(EvaluationAssignment.period),
        ).filter(EvaluationAssignment.evaluator_id == user_id)
    )
    if statuses:
        query = query.filter(EvaluationAssignment.status.in_(statuses))
    return query


def build_dashboard_meeting_query(user_id: int, today):
    return (
        FeedbackMeeting.query.options(
            joinedload(FeedbackMeeting.employee),
            joinedload(FeedbackMeeting.manager),
        ).filter(
            ((FeedbackMeeting.employee_id == user_id) | (FeedbackMeeting.manager_id == user_id)),
            FeedbackMeeting.meeting_date >= today,
            FeedbackMeeting.status == "planlandi",
        )
    )


# Eski inspect scriptlerinde gecen isim uyumlulugu kalsin.
def build_feedback_meetings_query(user_id: int, today):
    return build_dashboard_meeting_query(user_id, today)