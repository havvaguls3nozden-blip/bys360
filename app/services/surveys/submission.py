"""Anket cevap kaydetme servis köprüsü.

Faz 8 kuralı:
- Route güvenlik kontrolleri, hedef eşleşmesi, tekrar cevap engeli ve form token
  tüketimini yapmaya devam eder.
- Bu servis yalnızca token sonrasındaki yazma işini üstlenir.
- Transaction tek noktadan kapatılır; hata route tarafında rollback ile karşılanır.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Iterable, Mapping
from typing import Any

logger = logging.getLogger(__name__)


def _utcnow():
    from app.communication.shared import _utcnow as _shared_utcnow

    return _shared_utcnow()


def _getlist(form_data: Any, key: str) -> list[str]:
    getter = getattr(form_data, "getlist", None)
    if callable(getter):
        return list(getter(key) or [])
    value = None
    if isinstance(form_data, Mapping):
        value = form_data.get(key)
    else:
        value = getattr(form_data, key, None)
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _get_value(form_data: Any, key: str, *, type_: Callable[[Any], Any] | None = None):
    getter = getattr(form_data, "get", None)
    if callable(getter):
        try:
            if type_ is not None:
                return getter(key, type=type_)
            return getter(key)
        except TypeError:
            value = getter(key)
    elif isinstance(form_data, Mapping):
        value = form_data.get(key)
    else:
        value = getattr(form_data, key, None)

    if value in (None, ""):
        return None if type_ is not None else value
    if type_ is None:
        return value
    try:
        return type_(value)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/submission.py | line=60")
        return None


def _default_question_option_id_set(question: Any) -> set[int]:
    options = getattr(question, "options", None)
    if options is None:
        options = getattr(question, "survey_options", None)
    try:
        if hasattr(options, "all"):
            options = options.all()
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/submission.py | line=71")
        options = []
    option_ids: set[int] = set()
    for option in options or []:
        try:
            option_ids.add(int(option.id))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/surveys/submission.py:75)")
            continue
    return option_ids


def _question_label(question: Any) -> str:
    text = (getattr(question, "question_text", "") or "").strip()
    return text or "Anket sorusu"


def _add_single_choice_answer(*, session: Any, response_id: int, question: Any, form_data: Any, question_option_id_set: Callable[[Any], set[int]]) -> None:
    from app.models import SurveyAnswer

    field_name = f"question_{question.id}"
    selected_option_id = _get_value(form_data, field_name, type_=int)
    allowed_option_ids = question_option_id_set(question)
    if getattr(question, "is_required", False) and not selected_option_id:
        raise ValueError(f'"{_question_label(question)}" sorusu zorunludur.')
    if selected_option_id:
        if int(selected_option_id) not in allowed_option_ids:
            raise ValueError(f'"{_question_label(question)}" için geçersiz seçenek gönderildi.')
        session.add(SurveyAnswer(response_id=response_id, question_id=question.id, selected_option_id=int(selected_option_id)))


def _add_multiple_choice_answers(*, session: Any, response_id: int, question: Any, form_data: Any, question_option_id_set: Callable[[Any], set[int]]) -> None:
    from app.models import SurveyAnswer

    field_name = f"question_{question.id}"
    selected_values = _getlist(form_data, field_name)
    allowed_option_ids = question_option_id_set(question)
    selected_ids = [int(x) for x in selected_values if str(x).strip().isdigit()]
    if getattr(question, "is_required", False) and not selected_ids:
        raise ValueError(f'"{_question_label(question)}" sorusu zorunludur.')
    invalid_ids = [option_id for option_id in selected_ids if option_id not in allowed_option_ids]
    if invalid_ids:
        raise ValueError(f'"{_question_label(question)}" için geçersiz seçenek gönderildi.')
    for option_id in sorted(set(selected_ids)):
        session.add(SurveyAnswer(response_id=response_id, question_id=question.id, selected_option_id=option_id))


def _add_rating_answer(*, session: Any, response_id: int, question: Any, form_data: Any, max_scale: int) -> None:
    from app.models import SurveyAnswer

    field_name = f"question_{question.id}"
    answer_number = _get_value(form_data, field_name, type_=float)
    if getattr(question, "is_required", False) and answer_number is None:
        raise ValueError(f'"{_question_label(question)}" sorusu zorunludur.')
    if answer_number is not None and not (0 <= answer_number <= max_scale):
        raise ValueError(f'"{_question_label(question)}" için puan aralığı 0 ile {max_scale} arasında olmalıdır.')
    session.add(SurveyAnswer(response_id=response_id, question_id=question.id, answer_number=answer_number))


def _add_text_answer(*, session: Any, response_id: int, question: Any, form_data: Any) -> None:
    from app.models import SurveyAnswer

    field_name = f"question_{question.id}"
    answer_text = (_get_value(form_data, field_name) or "").strip()
    if getattr(question, "is_required", False) and not answer_text:
        raise ValueError(f'"{_question_label(question)}" sorusu zorunludur.')
    session.add(SurveyAnswer(response_id=response_id, question_id=question.id, answer_text=answer_text or None))


def submit_survey_response(
    *,
    survey: Any,
    current_user: Any,
    matched_assignment: Any,
    questions: Iterable[Any],
    form_data: Any,
    question_option_id_resolver: Callable[[Any], set[int]] | None = None,
    now_factory: Callable[[], Any] | None = None,
    uuid_factory: Callable[[], Any] | None = None,
    db_session: Any | None = None,
):
    """Token sonrası anket yanıtını kaydeder ve transaction'ı commit eder.

    Route tarafında korunmaya devam edenler:
    - survey erişim durumu
    - hedef kitle eşleşmesi
    - tekil cevap engeli
    - form token tüketimi
    """

    from app.extensions import db
    from app.models import SurveyResponse

    session = db_session or db.session
    question_option_id_set = question_option_id_resolver or _default_question_option_id_set
    now_value = (now_factory or _utcnow)()
    uuid_value = str((uuid_factory or uuid.uuid4)())

    response = SurveyResponse(
        survey_id=survey.id,
        user_id=None if getattr(survey, "is_anonymous", False) else current_user.id,
        assignment_id=matched_assignment.id if matched_assignment else None,
        submitted_at=now_value,
        is_completed=True,
        anonymous_token=uuid_value if getattr(survey, "is_anonymous", False) else None,
    )
    session.add(response)
    session.flush()

    for question in questions:
        qtype = (getattr(question, "question_type", "") or "").strip().lower()
        if qtype in {"single_choice", "yes_no"}:
            _add_single_choice_answer(
                session=session,
                response_id=response.id,
                question=question,
                form_data=form_data,
                question_option_id_set=question_option_id_set,
            )
        elif qtype == "multiple_choice":
            _add_multiple_choice_answers(
                session=session,
                response_id=response.id,
                question=question,
                form_data=form_data,
                question_option_id_set=question_option_id_set,
            )
        elif qtype in {"rating_5", "rating_10"}:
            _add_rating_answer(
                session=session,
                response_id=response.id,
                question=question,
                form_data=form_data,
                max_scale=5 if qtype == "rating_5" else 10,
            )
        else:
            _add_text_answer(session=session, response_id=response.id, question=question, form_data=form_data)

    session.commit()
    return response


__all__ = ["submit_survey_response"]
