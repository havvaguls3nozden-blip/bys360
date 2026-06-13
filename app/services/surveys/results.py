"""Anket sonuç/rapor okuma servisleri.

Faz 5 canlı koruma kuralı:
- Bu modül yalnızca okuma, özetleme, oran hesaplama ve CSV metni üretir.
- Cevap kaydetme, yayınlama, kapatma, arşivleme veya silme işlemi yapmaz.
- Flask route dosyasındaki canlı sonuç ekranı davranışını koruyarak hesaplama
  mantığını test edilebilir servis katmanına taşır.
"""
from __future__ import annotations

import csv
import datetime as _dt
import io
from typing import Any, Callable

from .repository import (
    safe_completed_response_count,
    safe_question_options,
    safe_survey_questions,
    _rollback_session,
)
from .time_utils import survey_local_now
import logging
logger = logging.getLogger(__name__)


def safe_question_answers(question_id: int) -> list[Any]:
    """Bir soruya ait yanıtları salt-okuma amaçlı döndürür."""
    try:
        from sqlalchemy.orm import load_only
        from app.extensions import db
        from app.models import SurveyAnswer

        return (
            db.session.query(SurveyAnswer)
            .options(
                load_only(
                    SurveyAnswer.id,
                    SurveyAnswer.question_id,
                    SurveyAnswer.selected_option_id,
                    SurveyAnswer.answer_text,
                    SurveyAnswer.answer_number,
                )
            )
            .filter(SurveyAnswer.question_id == int(question_id))
            .all()
        )
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/results.py | line=48")
        _rollback_session()
        return []


def latest_completed_label_for_survey(survey_id: int) -> str:
    """Son tamamlanan yanıt zamanını ekranda kullanılan etiketle döndürür."""
    try:
        from app.extensions import db
        from app.models import SurveyResponse

        row = (
            db.session.query(SurveyResponse.submitted_at)
            .filter(
                SurveyResponse.survey_id == int(survey_id),
                SurveyResponse.is_completed.is_(True),
                SurveyResponse.submitted_at.isnot(None),
            )
            .order_by(SurveyResponse.submitted_at.desc())
            .first()
        )
        value = row[0] if row else None
        return value.strftime("%d.%m.%Y %H:%M") if value else "Henüz tamamlanan yanıt yok"
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/results.py | line=71")
        _rollback_session()
        return "Henüz tamamlanan yanıt yok"


def simple_completion_trend(survey_id: int) -> list[dict[str, object]]:
    """Son 7 günlük tamamlanma trendini mevcut şablon sözleşmesiyle üretir."""
    points: list[dict[str, object]] = []
    now = survey_local_now().date()
    counts: dict[str, int] = {}
    try:
        from sqlalchemy import func
        from app.extensions import db
        from app.models import SurveyResponse

        start_date = now - _dt.timedelta(days=6)
        rows = (
            db.session.query(func.date(SurveyResponse.submitted_at), func.count(SurveyResponse.id))
            .filter(
                SurveyResponse.survey_id == int(survey_id),
                SurveyResponse.is_completed.is_(True),
                SurveyResponse.submitted_at.isnot(None),
                SurveyResponse.submitted_at >= _dt.datetime.combine(start_date, _dt.time.min),
            )
            .group_by(func.date(SurveyResponse.submitted_at))
            .all()
        )
        counts = {str(day): int(count or 0) for day, count in rows}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/results.py | line=99")
        _rollback_session()
        counts = {}

    max_count = max(counts.values(), default=0)
    for offset in range(6, -1, -1):
        day = now - _dt.timedelta(days=offset)
        count = counts.get(str(day), 0)
        pct = round((count / max_count) * 100, 1) if max_count else 0
        points.append({"label": day.strftime("%d.%m"), "count": count, "pct": pct})
    return points


def _question_type(question: Any) -> str:
    return str(getattr(question, "question_type", "") or "").strip().lower()


def _question_text(question: Any) -> str:
    return str(getattr(question, "question_text", "") or "")


def _option_text(option: Any) -> str:
    return str(getattr(option, "option_text", "") or "")


def _selected_option_id(answer: Any) -> Any:
    return getattr(answer, "selected_option_id", None)


def _answer_number(answer: Any) -> Any:
    return getattr(answer, "answer_number", None)


def _answer_text(answer: Any) -> str:
    return str(getattr(answer, "answer_text", "") or "")


def build_question_summary_row(question: Any) -> dict[str, Any]:
    """Sonuç ekranı için tek soru özetini mevcut template sözleşmesiyle üretir."""
    qtype = _question_type(question)
    answers = safe_question_answers(int(getattr(question, "id", 0) or 0))

    if qtype in {"single_choice", "multiple_choice", "yes_no"}:
        option_stats = []
        total_option_answers = len([a for a in answers if _selected_option_id(a)])
        for option in safe_question_options(int(getattr(question, "id", 0) or 0)):
            option_id = getattr(option, "id", None)
            count = len([a for a in answers if _selected_option_id(a) == option_id])
            option_stats.append(
                {
                    "label": _option_text(option),
                    "count": count,
                    "pct": round((count / total_option_answers) * 100, 1) if total_option_answers else 0,
                }
            )
        top_option = max(option_stats, key=lambda x: x["count"]) if option_stats else None
        return {
            "question": question,
            "mode": "options",
            "option_stats": option_stats,
            "top_option": top_option,
            "answer_count": total_option_answers,
            "helper_text": "",
            "_internal": {"option_answer_total": total_option_answers},
        }

    if qtype in {"rating_5", "rating_10"}:
        numeric_values = [_answer_number(a) for a in answers if _answer_number(a) is not None]
        avg_value = round(sum(numeric_values) / len(numeric_values), 2) if numeric_values else 0
        max_scale = 5 if qtype == "rating_5" else 10
        normalized_score = round((avg_value / max_scale) * 100, 1) if avg_value else 0
        return {
            "question": question,
            "mode": "rating",
            "avg_value": avg_value,
            "count": len(numeric_values),
            "max_scale": max_scale,
            "normalized_score": normalized_score,
            "helper_text": "",
            "_internal": {"has_values": bool(numeric_values)},
        }

    text_answers = [_answer_text(a) for a in answers if _answer_text(a).strip()]
    return {
        "question": question,
        "mode": "text",
        "text_answers": text_answers[:20],
        "text_count": len(text_answers),
        "helper_text": "",
        "_internal": {"text_answer_total": len(text_answers)},
    }


def summarize_question_for_csv(question: Any) -> str:
    """CSV export için mevcut metin özet sözleşmesini korur."""
    qtype = _question_type(question)
    answers = safe_question_answers(int(getattr(question, "id", 0) or 0))
    if qtype in {"single_choice", "multiple_choice", "yes_no"}:
        parts = []
        for option in safe_question_options(int(getattr(question, "id", 0) or 0)):
            option_id = getattr(option, "id", None)
            count = len([a for a in answers if _selected_option_id(a) == option_id])
            parts.append(f"{_option_text(option)}: {count}")
        return " | ".join(parts)
    if qtype in {"rating_5", "rating_10"}:
        values = [_answer_number(a) for a in answers if _answer_number(a) is not None]
        avg_value = round(sum(values) / len(values), 2) if values else 0
        return f"Ortalama: {avg_value} / Kayıt: {len(values)}"
    texts = [_answer_text(a).strip() for a in answers if _answer_text(a).strip()]
    return " | ".join(texts[:10])


def build_survey_results_csv_text(survey: Any, *, estimated_target_count: int = 0) -> str:
    """Anket sonuç CSV içeriğini üretir; HTTP Response route içinde kalır."""
    output = io.StringIO()
    writer = csv.writer(output)
    survey_id = int(getattr(survey, "id", 0) or 0)
    writer.writerow(["Anket", getattr(survey, "title", "") or ""])
    writer.writerow(["Tamamlanan", safe_completed_response_count(survey_id)])
    writer.writerow(["Hedef", int(estimated_target_count or 0)])
    writer.writerow([])
    writer.writerow(["Soru", "Tür", "Yanıt Özeti"])

    for question in safe_survey_questions(survey_id):
        writer.writerow([_question_text(question), getattr(question, "question_type", "") or "", summarize_question_for_csv(question)])

    return output.getvalue()


def build_survey_results_context(
    selected_survey: Any,
    *,
    estimate_target_user_ids: Callable[[Any], list[int]] | None = None,
) -> dict[str, Any]:
    """Sonuç ekranı için hesaplanan tüm metrikleri route dışına taşır."""
    summary: list[dict[str, Any]] = []
    total_completed = 0
    estimated_target_count = 0
    completion_rate = 0
    rating_average = 0
    rating_question_count = 0
    text_response_count = 0
    option_question_count = 0
    text_question_count = 0
    strongest_question = None
    weakest_question = None
    highest_option_question = None
    answer_mix: list[dict[str, Any]] = []

    if selected_survey:
        survey_id = int(getattr(selected_survey, "id", 0) or 0)
        total_completed = safe_completed_response_count(survey_id)
        if estimate_target_user_ids:
            try:
                estimated_target_count = len(estimate_target_user_ids(selected_survey) or [])
            except Exception:
                logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/results.py | line=254")
                estimated_target_count = 0
        completion_rate = round((total_completed / estimated_target_count) * 100, 1) if estimated_target_count else 0
        questions = safe_survey_questions(survey_id)
        rating_averages: list[float] = []
        strongest_score = None
        weakest_score = None
        strongest_label = None
        weakest_label = None
        highest_option_total = -1

        for question in questions:
            row = build_question_summary_row(question)
            row_internal = dict(row.pop("_internal", {}) or {})
            summary.append(row)
            qtype = _question_type(question)
            if row.get("mode") == "options":
                option_question_count += 1
                total_option_answers = int(row_internal.get("option_answer_total") or 0)
                top_option = row.get("top_option")
                if total_option_answers > highest_option_total and top_option:
                    highest_option_total = total_option_answers
                    highest_option_question = {
                        "label": _question_text(question),
                        "detail": f"En baskın seçenek: {top_option['label']} (%{top_option['pct']})",
                    }
            elif row.get("mode") == "rating":
                avg_value = row.get("avg_value") or 0
                max_scale = row.get("max_scale") or (5 if qtype == "rating_5" else 10)
                normalized_score = row.get("normalized_score") or 0
                if row_internal.get("has_values"):
                    rating_averages.append(avg_value)
                    if strongest_score is None or normalized_score > strongest_score:
                        strongest_score = normalized_score
                        strongest_label = f"{_question_text(question)} • {avg_value}/{max_scale}"
                    if weakest_score is None or normalized_score < weakest_score:
                        weakest_score = normalized_score
                        weakest_label = f"{_question_text(question)} • {avg_value}/{max_scale}"
                rating_question_count += 1
            else:
                text_question_count += 1
                text_response_count += int(row_internal.get("text_answer_total") or 0)

        rating_average = round(sum(rating_averages) / len(rating_averages), 2) if rating_averages else 0
        strongest_question = {"label": strongest_label or "Henüz puanlı veri yok", "score": strongest_score or 0}
        weakest_question = {"label": weakest_label or "Henüz puanlı veri yok", "score": weakest_score or 0}
        total_questions = len(questions)
        answer_mix = [
            {"label": "Puan Soruları", "count": rating_question_count, "pct": round((rating_question_count / total_questions) * 100, 1) if total_questions else 0},
            {"label": "Seçimli Sorular", "count": option_question_count, "pct": round((option_question_count / total_questions) * 100, 1) if total_questions else 0},
            {"label": "Metin Soruları", "count": text_question_count, "pct": round((text_question_count / total_questions) * 100, 1) if total_questions else 0},
        ]

    latest_completed_label = latest_completed_label_for_survey(int(getattr(selected_survey, "id", 0) or 0)) if selected_survey else "Henüz tamamlanan yanıt yok"
    completion_trend = simple_completion_trend(int(getattr(selected_survey, "id", 0) or 0)) if selected_survey else []
    draft_count = 0
    avg_draft_progress = 0
    latest_partial_label = "Taslak metriği kapalı"
    executive_notes = [
        {"title": "Katılım görünümü", "text": f"Tamamlanan {total_completed} yanıt, tahmini hedef {estimated_target_count} kişi."},
        {"title": "Puanlı alan özeti", "text": f"Puanlı soru sayısı {rating_question_count}; genel ortalama {rating_average or '—'}."},
        {"title": "Metin katkısı", "text": f"Açık uçlu yanıt sayısı {text_response_count}; seçimli soru sayısı {option_question_count}."},
    ]
    response_health = [
        {"label": "Tamamlanma", "value": f"%{completion_rate}", "detail": "Tamamlanan yanıtların tahmini hedefe oranı."},
        {"label": "Son tamamlanan", "value": latest_completed_label, "detail": "Son kaydedilen tam yanıt zamanı."},
        {"label": "Taslak durumu", "value": "Kapalı", "detail": "Bu sürümde taslak/kısmi yanıt metrikleri devre dışı."},
    ]

    return {
        "total_completed": total_completed,
        "estimated_target_count": estimated_target_count,
        "completion_rate": completion_rate,
        "rating_average": rating_average,
        "rating_question_count": rating_question_count,
        "text_response_count": text_response_count,
        "option_question_count": option_question_count,
        "strongest_question": strongest_question,
        "weakest_question": weakest_question,
        "highest_option_question": highest_option_question,
        "text_question_count": text_question_count,
        "answer_mix": answer_mix,
        "summary": summary,
        "latest_completed_label": latest_completed_label,
        "completion_trend": completion_trend,
        "draft_count": draft_count,
        "avg_draft_progress": avg_draft_progress,
        "latest_partial_label": latest_partial_label,
        "executive_notes": executive_notes,
        "response_health": response_health,
        "dropoff_rows": [],
    }
