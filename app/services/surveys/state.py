"""Anket durum/yayın servis köprüsü.

Faz 9 kuralı:
- Route yetki, anket var/yok ve ekran yönlendirme dilini korur.
- Bu servis yalnızca onaylanmış durum değişikliği ve toplu işlem yazımlarını üstlenir.
- Transaction tek noktadan kapatılır; hata durumunda route rollback yapmaya devam eder.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any


def _utcnow():
    from app.communication.shared import _utcnow as _shared_utcnow

    return _shared_utcnow()


@dataclass(frozen=True)
class SurveyStateResult:
    """Tekil anket durum işlemi sonucu."""

    affected: int = 1
    notified: int = 0
    skipped_with_responses: int = 0


@dataclass(frozen=True)
class SurveyBulkActionResult:
    """Toplu anket işlem sonucu."""

    affected: int = 0
    skipped_with_responses: int = 0


def _ensure_state_change(*, current_value: str | None, target_value: str, entity_label: str = "Anket", allow_same: bool = False) -> None:
    from app.route_support import ensure_state_change

    ensure_state_change(current_value=current_value, target_value=target_value, entity_label=entity_label, allow_same=allow_same)


def publish_survey(
    survey: Any,
    *,
    target_user_ids: Iterable[int],
    notify_user: Callable[..., Any] | None,
    link_url: str,
    now_factory: Callable[[], Any] | None = None,
    db_session: Any | None = None,
) -> SurveyStateResult:
    """Anketi yayımlar ve ilk yayında hedef kullanıcılara bildirim üretir."""

    from app.extensions import db

    session = db_session or db.session
    was_published = (getattr(survey, "status", None) == "published")
    _ensure_state_change(current_value=getattr(survey, "status", None), target_value="published")
    survey.status = "published"
    if not getattr(survey, "start_at", None):
        survey.start_at = (now_factory or _utcnow)()

    notified = 0
    if not was_published and notify_user is not None:
        for user_id in target_user_ids or []:
            notify_user(
                user_id=int(user_id),
                title="Yeni anket atandı",
                body=f'"{getattr(survey, "title", "Anket")}" başlıklı ankete yanıt vermeniz bekleniyor.',
                notification_type="survey_assigned",
                source_type="survey",
                source_id=survey.id,
                link_url=link_url,
                priority="normal",
            )
            notified += 1
    session.commit()
    return SurveyStateResult(affected=1, notified=notified)


def unpublish_survey(survey: Any, *, db_session: Any | None = None) -> SurveyStateResult:
    from app.extensions import db

    session = db_session or db.session
    _ensure_state_change(current_value=getattr(survey, "status", None), target_value="draft")
    survey.status = "draft"
    session.commit()
    return SurveyStateResult(affected=1)


def close_survey(survey: Any, *, now_factory: Callable[[], Any] | None = None, db_session: Any | None = None) -> SurveyStateResult:
    from app.extensions import db

    session = db_session or db.session
    _ensure_state_change(current_value=getattr(survey, "status", None), target_value="closed")
    survey.status = "closed"
    if not getattr(survey, "end_at", None):
        survey.end_at = (now_factory or _utcnow)()
    session.commit()
    return SurveyStateResult(affected=1)


def archive_survey(survey: Any, *, db_session: Any | None = None) -> SurveyStateResult:
    from app.extensions import db

    session = db_session or db.session
    _ensure_state_change(current_value=getattr(survey, "status", None), target_value="archived")
    survey.status = "archived"
    session.commit()
    return SurveyStateResult(affected=1)


def restore_survey(survey: Any, *, db_session: Any | None = None) -> SurveyStateResult:
    from app.extensions import db

    session = db_session or db.session
    if (getattr(survey, "status", None) or "") != "archived":
        raise ValueError("Anket yalnızca arşivden geri alınabilir.")
    survey.status = "draft"
    session.commit()
    return SurveyStateResult(affected=1)


def _detach_survey_references(survey: Any) -> None:
    from app.models import Notification

    Notification.query.filter_by(source_type="survey", source_id=survey.id).delete(synchronize_session=False)
    # Ic Portal modulu canlı omurgadan çıkarıldığı için eski portal bağlantısı artık temizlenmez.
def delete_survey_if_allowed(survey: Any, *, any_response_count: Callable[[int], int] | None = None, db_session: Any | None = None) -> SurveyStateResult:
    from app.extensions import db
    from app.services.surveys.repository import safe_any_response_count

    session = db_session or db.session
    response_counter = any_response_count or safe_any_response_count
    if response_counter(int(survey.id)) > 0:
        raise ValueError("Yanıt almış anket kalıcı olarak silinemez. Arşivlemeyi tercih edin.")
    _detach_survey_references(survey)
    session.delete(survey)
    session.commit()
    return SurveyStateResult(affected=1)


def bulk_survey_action(
    surveys: Iterable[Any],
    action: str,
    *,
    completed_response_count: Callable[[int], int] | None = None,
    db_session: Any | None = None,
) -> SurveyBulkActionResult:
    from app.extensions import db
    from app.services.surveys.repository import safe_completed_response_count

    session = db_session or db.session
    response_counter = completed_response_count or safe_completed_response_count
    normalized_action = (action or "").strip().lower()
    affected = 0
    skipped_with_responses = 0

    if normalized_action == "archive":
        for survey in surveys:
            if (getattr(survey, "status", None) or "") != "archived":
                survey.status = "archived"
                affected += 1
    elif normalized_action == "restore":
        for survey in surveys:
            if (getattr(survey, "status", None) or "") == "archived":
                survey.status = "draft"
                affected += 1
    elif normalized_action == "delete":
        for survey in surveys:
            if response_counter(int(survey.id)) > 0:
                skipped_with_responses += 1
                continue
            _detach_survey_references(survey)
            session.delete(survey)
            affected += 1
    else:
        raise ValueError("Toplu işlem seçimi geçersiz.")

    session.commit()
    return SurveyBulkActionResult(affected=affected, skipped_with_responses=skipped_with_responses)


__all__ = [
    "SurveyBulkActionResult",
    "SurveyStateResult",
    "archive_survey",
    "bulk_survey_action",
    "close_survey",
    "delete_survey_if_allowed",
    "publish_survey",
    "restore_survey",
    "unpublish_survey",
]
