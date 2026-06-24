"""Anket modülü için savunmacı okuma yardımcıları.

Faz 2'de route dosyası bu fonksiyonları kullanmaz. Faz 3'te küçük sayaç ve
okuma yardımcıları buraya kademeli aktarılabilir.
"""
from __future__ import annotations

from typing import Any
import logging
logger = logging.getLogger(__name__)


def _rollback_session() -> None:
    try:
        from app.extensions import db

        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/repository.py")
def safe_count(model: Any, *filters: Any) -> int:
    try:
        from sqlalchemy import func
        from app.extensions import db

        query = db.session.query(func.count(model.id))
        for condition in filters:
            query = query.filter(condition)
        return int(query.scalar() or 0)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=30")
        _rollback_session()
        return 0


def completed_response_count(survey_id: int) -> int:
    try:
        from app.models import SurveyResponse

        return safe_count(
            SurveyResponse,
            SurveyResponse.survey_id == int(survey_id),
            SurveyResponse.is_completed.is_(True),
        )
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=44")
        _rollback_session()
        return 0


def any_response_count(survey_id: int) -> int:
    try:
        from app.models import SurveyResponse

        return safe_count(SurveyResponse, SurveyResponse.survey_id == int(survey_id))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=54")
        _rollback_session()
        return 0


def assignment_count(survey_id: int) -> int:
    try:
        from app.models import SurveyAssignment

        return safe_count(SurveyAssignment, SurveyAssignment.survey_id == int(survey_id))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=64")
        _rollback_session()
        return 0


def question_count(survey_id: int) -> int:
    try:
        from app.models import SurveyQuestion

        return safe_count(SurveyQuestion, SurveyQuestion.survey_id == int(survey_id))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=74")
        _rollback_session()
        return 0

# Faz 4: Canlı anket okuma/sayaç yardımcıları
# Bu fonksiyonlar yazma işlemi yapmaz; sadece liste/detay/rapor ekranlarının
# güvenli okuma ihtiyacını route dışına taşır.


def safe_completed_response_count(survey_id: int) -> int:
    """Tamamlanmış yanıt sayısını canlı uyumlu ve savunmacı şekilde döndürür."""
    return completed_response_count(survey_id)


def safe_any_response_count(survey_id: int) -> int:
    """Tamamlanmış/tamamlanmamış tüm yanıt sayısını döndürür."""
    return any_response_count(survey_id)


def safe_assignment_count(survey_id: int) -> int:
    """Anket atama sayısını döndürür."""
    return assignment_count(survey_id)


def safe_question_count(survey_id: int) -> int:
    """Ankete bağlı soru sayısını döndürür."""
    return question_count(survey_id)


def survey_question_compat_defaults(question: Any) -> Any:
    """Faz 2 soru alanları modelde yoksa template uyumluluğunu korur."""
    defaults = {
        "helper_text": "",
        "logic_mode": "always",
        "logic_source_question_id": None,
        "logic_operator": "answered",
        "logic_value": "",
    }
    try:
        from .schema import survey_question_phase2_ready

        if survey_question_phase2_ready():
            return question
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/repository.py")
    try:
        state = getattr(question, "__dict__", None)
        if isinstance(state, dict):
            for key, value in defaults.items():
                state.setdefault(key, value)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/repository.py")
    return question


def safe_survey_questions(survey_id: int) -> list[Any]:
    """Anket sorularını canlı şema uyumluluğuyla sıralı döndürür."""
    try:
        from sqlalchemy.orm import load_only
        from app.extensions import db
        from app.models import SurveyQuestion
        from .schema import survey_question_phase2_ready

        query = db.session.query(SurveyQuestion)
        if not survey_question_phase2_ready():
            query = query.options(
                load_only(
                    SurveyQuestion.id,
                    SurveyQuestion.survey_id,
                    SurveyQuestion.question_text,
                    SurveyQuestion.question_type,
                    SurveyQuestion.is_required,
                    SurveyQuestion.sort_order,
                )
            )
        rows = (
            query.filter(SurveyQuestion.survey_id == int(survey_id))
            .order_by(SurveyQuestion.sort_order.asc(), SurveyQuestion.id.asc())
            .all()
        )
        return [survey_question_compat_defaults(row) for row in rows]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=157")
        _rollback_session()
        return []


def safe_question_options(question_id: int) -> list[Any]:
    """Soru seçeneklerini sıralı ve salt-okuma amaçlı döndürür."""
    try:
        from sqlalchemy.orm import load_only
        from app.extensions import db
        from app.models import SurveyQuestionOption

        return (
            db.session.query(SurveyQuestionOption)
            .options(
                load_only(
                    SurveyQuestionOption.id,
                    SurveyQuestionOption.question_id,
                    SurveyQuestionOption.option_text,
                    SurveyQuestionOption.sort_order,
                )
            )
            .filter(SurveyQuestionOption.question_id == int(question_id))
            .order_by(SurveyQuestionOption.sort_order.asc(), SurveyQuestionOption.id.asc())
            .all()
        )
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/repository.py | line=183")
        _rollback_session()
        return []
