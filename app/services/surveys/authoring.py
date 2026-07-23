"""Anket oluşturma/düzenleme yardımcıları.

Faz 10 kapanışında route dosyasındaki form-state ve soru kalıcılığı
yardımcıları buraya taşındı. Fonksiyonlar transaction başlatmaz; commit/rollback
sorumluluğu canlı route akışında kalır.
"""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping, Sequence
import logging
logger = logging.getLogger(__name__)


def _rollback_session() -> None:
    try:
        from app.extensions import db

        db.session.rollback()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/authoring.py")
def survey_question_attr(question: Any, attr_name: str, default: Any = None) -> Any:
    """Faz 2 soru alanları yoksa eski canlı şemayla uyumlu değer döndürür."""
    try:
        from .schema import survey_question_phase2_ready

        if not survey_question_phase2_ready():
            return default
        value = getattr(question, attr_name, default)
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/surveys/authoring.py | line=30")
        _rollback_session()
        return default
    return default if value is None else value


def _getlist(form_data: Any, key: str) -> list[str]:
    """Flask MultiDict veya düz mapping için getlist uyumluluğu sağlar."""
    if hasattr(form_data, "getlist"):
        try:
            return [str(item) for item in form_data.getlist(key)]
        except Exception:
            logger.exception("BYS360 V6B guarded exception | file=app/services/surveys/authoring.py | line=41")
            return []
    value = None
    value = form_data.get(key) if isinstance(form_data, Mapping) else getattr(form_data, key, None)
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    return [str(value)]


def _get(form_data: Any, key: str, default: str = "") -> str:
    try:
        if hasattr(form_data, "get") or isinstance(form_data, Mapping):
            value = form_data.get(key, default)
        else:
            value = getattr(form_data, key, default)
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/surveys/authoring.py | line=63")
        value = default
    return str(value or default)


def survey_form_state_from_mapping(form_data: Any) -> dict[str, Any]:
    """Anket oluştur/düzenle formunu route dışına taşınabilir state'e çevirir."""
    question_texts = _getlist(form_data, "question_text[]")
    question_types = _getlist(form_data, "question_type[]")
    question_requireds = _getlist(form_data, "question_required[]")
    option_blocks = _getlist(form_data, "question_options[]")
    helper_texts = _getlist(form_data, "question_helper_text[]")
    logic_modes = _getlist(form_data, "question_logic_mode[]")
    logic_sources = _getlist(form_data, "question_logic_source[]")
    logic_operators = _getlist(form_data, "question_logic_operator[]")
    logic_values = _getlist(form_data, "question_logic_value[]")
    questions: list[dict[str, Any]] = []

    max_len = max(
        len(question_texts),
        len(question_types),
        len(question_requireds),
        len(option_blocks),
        len(helper_texts),
        len(logic_modes),
        len(logic_sources),
        len(logic_operators),
        len(logic_values),
        0,
    )
    for idx in range(max_len):
        qtext = (question_texts[idx] if idx < len(question_texts) else "").strip()
        qtype = (question_types[idx] if idx < len(question_types) else "text").strip() or "text"
        qreq = (question_requireds[idx] if idx < len(question_requireds) else "1").strip()
        raw_options = (option_blocks[idx] if idx < len(option_blocks) else "").strip()
        helper_text = (helper_texts[idx] if idx < len(helper_texts) else "").strip()
        logic_mode = (logic_modes[idx] if idx < len(logic_modes) else "always").strip() or "always"
        logic_source = (logic_sources[idx] if idx < len(logic_sources) else "").strip()
        logic_operator = (logic_operators[idx] if idx < len(logic_operators) else "answered").strip() or "answered"
        logic_value = (logic_values[idx] if idx < len(logic_values) else "").strip()
        if not qtext and not raw_options and qtype == "text" and not helper_text:
            continue
        questions.append(
            {
                "question_text": qtext,
                "question_type": qtype,
                "is_required": (qreq == "1"),
                "options_text": raw_options,
                "helper_text": helper_text,
                "logic_mode": logic_mode,
                "logic_source": logic_source,
                "logic_operator": logic_operator,
                "logic_value": logic_value,
            }
        )

    return {
        "title": _get(form_data, "title").strip(),
        "description": _get(form_data, "description").strip(),
        "survey_type": (_get(form_data, "survey_type", "kurum_ici") or "kurum_ici").strip() or "kurum_ici",
        "status": (_get(form_data, "status", "draft") or "draft").strip() or "draft",
        "start_at": _get(form_data, "start_at").strip(),
        "end_at": _get(form_data, "end_at").strip(),
        "is_anonymous": bool(_get(form_data, "is_anonymous")),
        "allow_multiple_submissions": bool(_get(form_data, "allow_multiple_submissions")),
        "target_type": (_get(form_data, "target_type", "all") or "all").strip() or "all",
        "target_values": [str(v).strip() for v in _getlist(form_data, "target_values") if str(v).strip()],
        "questions": questions,
    }


def survey_state_from_db(
    survey: Any,
    current_assignments: Sequence[Any] | None = None,
    current_questions: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Veritabanındaki anketi form_state sözleşmesine dönüştürür."""
    from .repository import safe_question_options

    assignments = list(current_assignments or [])
    questions = list(current_questions or [])
    first_assignment = assignments[0] if assignments else None
    target_type = getattr(first_assignment, "target_type", None) or "all"
    target_values = [
        str(getattr(assignment, "target_value", "") or "")
        for assignment in assignments
        if (getattr(assignment, "target_value", "") or "").strip()
    ]
    question_rows: list[dict[str, Any]] = []
    question_sort_lookup = {
        int(getattr(question, "id", 0) or 0): int(getattr(question, "sort_order", 0) or 0)
        for question in questions
        if getattr(question, "id", None)
    }
    for question in questions:
        try:
            options = [opt.option_text for opt in safe_question_options(int(question.id))]
        except Exception:
            logger.exception("BYS360 V6B guarded exception | file=app/services/surveys/authoring.py | line=160")
            options = [getattr(opt, "option_text", "") for opt in getattr(question, "options", []) or []]
        source_question_id = survey_question_attr(question, "logic_source_question_id", None)
        question_rows.append(
            {
                "question_text": getattr(question, "question_text", "") or "",
                "question_type": getattr(question, "question_type", "") or "text",
                "is_required": bool(getattr(question, "is_required", False)),
                "options_text": "\n".join([str(opt).strip() for opt in options if str(opt).strip()]),
                "helper_text": survey_question_attr(question, "helper_text", "") or "",
                "logic_mode": survey_question_attr(question, "logic_mode", "always") or "always",
                "logic_source": question_sort_lookup.get(int(source_question_id or 0), "") if source_question_id else "",
                "logic_operator": survey_question_attr(question, "logic_operator", "answered") or "answered",
                "logic_value": survey_question_attr(question, "logic_value", "") or "",
            }
        )

    return {
        "title": getattr(survey, "title", "") or "",
        "description": getattr(survey, "description", "") or "",
        "survey_type": getattr(survey, "survey_type", "") or "kurum_ici",
        "status": getattr(survey, "status", "") or "draft",
        "start_at": survey.start_at.strftime("%Y-%m-%dT%H:%M") if getattr(survey, "start_at", None) else "",
        "end_at": survey.end_at.strftime("%Y-%m-%dT%H:%M") if getattr(survey, "end_at", None) else "",
        "is_anonymous": bool(getattr(survey, "is_anonymous", False)),
        "allow_multiple_submissions": bool(getattr(survey, "allow_multiple_submissions", False)),
        "target_type": target_type,
        "target_values": target_values,
        "questions": question_rows,
    }


def persist_survey_questions(*, survey_id: int, question_payloads: Sequence[dict[str, Any]]) -> int:
    """Soru ve seçenek kayıtlarını ekler; commit/rollback yapmaz."""
    from app.extensions import db
    from app.models import SurveyQuestion, SurveyQuestionOption
    from .schema import survey_question_phase2_ready

    inserted: list[tuple[Any, dict[str, Any]]] = []
    sort_order_map: dict[int, int] = {}
    phase2_ready = survey_question_phase2_ready()
    for item in question_payloads:
        question_kwargs: dict[str, Any] = {
            "survey_id": int(survey_id),
            "question_text": item["question_text"],
            "question_type": item["question_type"],
            "is_required": bool(item["is_required"]),
            "sort_order": int(item["sort_order"]),
        }
        if phase2_ready:
            question_kwargs.update(
                {
                    "helper_text": item.get("helper_text") or None,
                    "logic_mode": item.get("logic_mode") or "always",
                    "logic_source_question_id": None,
                    "logic_operator": item.get("logic_operator") or "answered",
                    "logic_value": item.get("logic_value") or None,
                }
            )
        question = SurveyQuestion(**question_kwargs)
        db.session.add(question)
        db.session.flush()
        sort_order_map[int(item["sort_order"])] = int(question.id)
        inserted.append((question, item))
        for opt_idx, option_text in enumerate(item.get("options") or [], start=1):
            db.session.add(SurveyQuestionOption(question_id=question.id, option_text=option_text, sort_order=opt_idx))
    if phase2_ready:
        for question, item in inserted:
            source_order = item.get("logic_source_sort_order")
            if source_order:
                question.logic_source_question_id = sort_order_map.get(int(source_order))
                db.session.add(question)
    return len(inserted)
