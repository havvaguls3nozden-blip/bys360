"""Anket listeleme yardımcıları.

Faz 10 kapanışında kullanıcıya atanmış anket listesi, durum satırı ve son yanıt
sorguları route dışına taşındı. Bu dosya salt-okuma ağırlıklıdır.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def _rollback_session() -> None:
    try:
        from app.extensions import db

        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/listing.py")
def latest_response_for_user(survey_id: int, user_id: int, *, completed_only: bool = False) -> Any | None:
    """Kullanıcının ilgili anketteki en güncel yanıtını döndürür."""
    try:
        from sqlalchemy.orm import load_only

        from app.extensions import db
        from app.models import SurveyResponse

        from .schema import survey_response_phase2_ready

        query = db.session.query(SurveyResponse)
        if not survey_response_phase2_ready():
            query = query.options(
                load_only(
                    SurveyResponse.id,
                    SurveyResponse.survey_id,
                    SurveyResponse.user_id,
                    SurveyResponse.assignment_id,
                    SurveyResponse.submitted_at,
                    SurveyResponse.is_completed,
                    SurveyResponse.anonymous_token,
                )
            )
        query = query.filter(SurveyResponse.survey_id == int(survey_id), SurveyResponse.user_id == int(user_id))
        if completed_only:
            query = query.filter(SurveyResponse.is_completed.is_(True))
        return query.order_by(
            SurveyResponse.is_completed.desc(),
            SurveyResponse.submitted_at.desc().nullslast(),
            SurveyResponse.id.desc(),
        ).first()
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/listing.py | line=50")
        _rollback_session()
        return None


def build_survey_state_row(survey: Any, response: Any | None, *, now: Any | None = None) -> dict[str, Any]:
    """Anket listesi için durum etiketi ve aksiyon bilgisi üretir."""
    from .time_utils import survey_local_now

    now = now or survey_local_now()
    if response and getattr(response, "is_completed", False):
        return {
            "key": "completed",
            "label": "Tamamlandı",
            "badge_class": "status-done",
            "action_label": "Tamamlandı",
            "action_style": "secondary",
            "is_actionable": False,
            "sort_priority": 4,
        }

    if (getattr(survey, "status", "") or "").strip().lower() != "published":
        return {
            "key": "draft",
            "label": "Taslak",
            "badge_class": "status-draft",
            "action_label": "Henüz Hazır Değil",
            "action_style": "secondary",
            "is_actionable": False,
            "sort_priority": 5,
        }

    if getattr(survey, "start_at", None) and survey.start_at > now:
        return {
            "key": "upcoming",
            "label": "Yakında Başlayacak",
            "badge_class": "status-upcoming",
            "action_label": "Başlangıcı Bekleniyor",
            "action_style": "secondary",
            "is_actionable": False,
            "sort_priority": 2,
        }

    if getattr(survey, "end_at", None) and survey.end_at < now:
        return {
            "key": "expired",
            "label": "Süresi Doldu",
            "badge_class": "status-expired",
            "action_label": "Süre Doldu",
            "action_style": "secondary",
            "is_actionable": False,
            "sort_priority": 3,
        }

    return {
        "key": "active",
        "label": "Açık",
        "badge_class": "status-open",
        "action_label": "Ankete Başla",
        "action_style": "primary",
        "is_actionable": True,
        "sort_priority": 1,
    }


def get_assigned_surveys_for_user(
    user: Any,
    *,
    user_matches_assignment: Callable[[Any, Any], bool] | None = None,
    latest_response_resolver: Callable[..., Any | None] | None = None,
    question_count_resolver: Callable[[int], int] | None = None,
) -> list[dict[str, Any]]:
    """Kullanıcıya atanmış yayınlanmış anketleri liste satırlarına dönüştürür."""
    from app.models import Survey

    from .repository import safe_question_count
    from .targets import assigned_survey_assignment_rows_for_user

    latest_response_resolver = latest_response_resolver or latest_response_for_user
    question_count_resolver = question_count_resolver or safe_question_count

    rows: list[dict[str, Any]] = []

    if user_matches_assignment is None:
        assigned_pairs = assigned_survey_assignment_rows_for_user(user, active_window=False)
        seen_survey_ids: set[int] = set()
        for survey, matched_assignment in assigned_pairs:
            survey_id = int(getattr(survey, "id", 0) or 0)
            if not survey_id or survey_id in seen_survey_ids:
                continue
            seen_survey_ids.add(survey_id)
            response = latest_response_resolver(survey_id, int(user.id))
            state = build_survey_state_row(survey, response)
            rows.append(
                {
                    "survey": survey,
                    "response": response,
                    "matched_assignment": matched_assignment,
                    "state": state,
                    "question_count": question_count_resolver(survey_id),
                }
            )
    else:
        published_surveys = (
            Survey.query
            .filter(Survey.status == "published")
            .order_by(Survey.created_at.desc(), Survey.id.desc())
            .all()
        )
        for survey in published_surveys:
            assignments = survey.assignments.all()
            if not assignments:
                continue

            matched_assignment = next((assignment for assignment in assignments if user_matches_assignment(assignment, user)), None)
            if not matched_assignment:
                continue

            survey_id = int(survey.id)
            response = latest_response_resolver(survey_id, int(user.id))
            state = build_survey_state_row(survey, response)
            rows.append(
                {
                    "survey": survey,
                    "response": response,
                    "matched_assignment": matched_assignment,
                    "state": state,
                    "question_count": question_count_resolver(survey_id),
                }
            )

    rows.sort(
        key=lambda row: (
            row["state"]["sort_priority"],
            -(row["survey"].start_at.timestamp()) if getattr(row["survey"], "start_at", None) else 0,
            -(row["survey"].id or 0),
        )
    )
    return rows
