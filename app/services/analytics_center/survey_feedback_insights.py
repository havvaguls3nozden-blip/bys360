from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""Anket / geri bildirim / nabiz analiz motoru servis koprusu.

Faz 5 canli davranis degistirmez. Veritabanina yazmaz, commit yapmaz,
runtime dis AI cagrisi yapmaz. Anket, geri bildirim ve nabiz kayitlarindan
toplu, maskelenmis ve karar destek icin guvenli sinyal payload'lari uretir.

Bu dosyanin hedefi acik uclu yanitlari kisisel veri dokmeden tema, katilim,
oncelik ve egilim sinyallerine donusturmektir.
"""

from dataclasses import asdict, dataclass
from typing import Any
from collections.abc import Iterable

try:
    from .summary_pipeline import build_analytics_safe_summary_card
except ImportError:  # python -S gate bagimsiz calistirmasi
    from analytics_center.summary_pipeline import build_analytics_safe_summary_card


@dataclass(frozen=True)
class SurveyFeedbackMetricCard:
    key: str
    title: str
    value: int | float | str
    unit: str = "adet"
    status: str = "neutral"
    description: str = ""
    source_domain: str = "survey_feedback"
    visibility_scope: str = "authorized_report_viewer"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SurveyFeedbackPrioritySignal:
    key: str
    title: str
    summary: str
    priority: str = "normal"
    sentiment_hint: str = "neutral"
    source_domain: str = "survey_feedback"
    action_hint: str = "Insan onayiyla degerlendiriniz."
    visibility_scope: str = "authorized_report_viewer"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_ALLOWED_STATUSES = {"good", "warning", "danger", "neutral", "info"}
_ALLOWED_PRIORITIES = {"low", "normal", "medium", "high", "critical"}
_ALLOWED_SENTIMENTS = {"positive", "neutral", "negative", "mixed", "unknown"}


def coerce_feedback_number(value: Any, default: int = 0) -> int | float:
    """Anket/geri bildirim metrikleri icin guvenli sayi donusturur."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value).strip().replace("%", "").replace(",", ".")
        number = float(text)
        return int(number) if number.is_integer() else number
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/analytics_center/survey_feedback_insights.py | line=71")
        return default


def clamp_feedback_percentage(value: Any) -> int | float:
    """Yuzde degerini 0-100 araliginda tutar."""
    number = coerce_feedback_number(value, default=0)
    try:
        return max(0, min(100, number))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/analytics_center/survey_feedback_insights.py | line=80")
        return 0


def calculate_response_rate(responses: Any, assignments: Any) -> int | float:
    """Atanan anket/geri bildirim sayisina gore katilim oranini hesaplar."""
    response_count = coerce_feedback_number(responses, default=0)
    assignment_count = coerce_feedback_number(assignments, default=0)
    if not assignment_count:
        return 0
    return round(clamp_feedback_percentage((response_count / assignment_count) * 100), 2)


def normalize_feedback_status(status: Any) -> str:
    value = str(status or "neutral").strip().lower()
    return value if value in _ALLOWED_STATUSES else "neutral"


def normalize_feedback_priority(priority: Any) -> str:
    value = str(priority or "normal").strip().lower()
    return value if value in _ALLOWED_PRIORITIES else "normal"


def normalize_sentiment_hint(sentiment_hint: Any) -> str:
    value = str(sentiment_hint or "unknown").strip().lower()
    return value if value in _ALLOWED_SENTIMENTS else "unknown"


def build_survey_feedback_metric_card(
    *,
    key: str,
    title: str,
    value: Any,
    unit: str = "adet",
    status: str = "neutral",
    description: str = "",
    source_domain: str = "survey_feedback",
    visibility_scope: str = "authorized_report_viewer",
) -> dict[str, object]:
    return SurveyFeedbackMetricCard(
        key=str(key or "survey_feedback_metric").strip() or "survey_feedback_metric",
        title=str(title or "Anket / Geri Bildirim Sinyali").strip() or "Anket / Geri Bildirim Sinyali",
        value=coerce_feedback_number(value, default=0),
        unit=str(unit or "adet"),
        status=normalize_feedback_status(status),
        description=str(description or ""),
        source_domain=str(source_domain or "survey_feedback"),
        visibility_scope=str(visibility_scope or "authorized_report_viewer"),
    ).to_dict()


def build_survey_feedback_priority_signal(
    *,
    key: str,
    title: str,
    summary: Any,
    priority: str = "normal",
    sentiment_hint: str = "unknown",
    source_domain: str = "survey_feedback",
    action_hint: str = "Insan onayiyla degerlendiriniz.",
    visibility_scope: str = "authorized_report_viewer",
) -> dict[str, object]:
    safe_summary = build_analytics_safe_summary_card(
        "survey_feedback_pulse",
        [{"summary": str(summary or "")}],
        module_type=source_domain,
    )
    return SurveyFeedbackPrioritySignal(
        key=str(key or "survey_feedback_priority_signal").strip() or "survey_feedback_priority_signal",
        title=str(title or "Anket / Geri Bildirim Oncelik Sinyali").strip() or "Anket / Geri Bildirim Oncelik Sinyali",
        summary=str(safe_summary.get("summary_text") or "Guvenli ozet hazirlanamadi."),
        priority=normalize_feedback_priority(priority),
        sentiment_hint=normalize_sentiment_hint(sentiment_hint),
        source_domain=str(source_domain or "survey_feedback"),
        action_hint=str(action_hint or "Insan onayiyla degerlendiriniz."),
        visibility_scope=str(visibility_scope or "authorized_report_viewer"),
    ).to_dict()


def build_survey_response_insights(survey_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Anket katilim ve yanit kapsamindan toplu kartlar uretir."""
    data = survey_stats or {}
    total_surveys = coerce_feedback_number(data.get("total_surveys", 0))
    active_surveys = coerce_feedback_number(data.get("active_surveys", 0))
    assignments = coerce_feedback_number(data.get("survey_assignments", data.get("assignments", 0)))
    responses = coerce_feedback_number(data.get("survey_responses", data.get("responses", 0)))
    response_rate = calculate_response_rate(responses, assignments)
    open_text_answers = coerce_feedback_number(data.get("open_text_answers", 0))
    low_participation = response_rate < 50 and assignments > 0
    return [
        build_survey_feedback_metric_card(
            key="total_surveys",
            title="Toplam anket kapsami",
            value=total_surveys,
            unit="anket",
            status="info",
            description="Canli anket ailesindeki toplu anket sayisi.",
        ),
        build_survey_feedback_metric_card(
            key="active_surveys",
            title="Aktif anketler",
            value=active_surveys,
            unit="anket",
            status="good" if active_surveys else "neutral",
            description="Yayinda veya izlenen aktif anket sinyali.",
        ),
        build_survey_feedback_metric_card(
            key="survey_response_rate",
            title="Anket katilim orani",
            value=response_rate,
            unit="%",
            status="warning" if low_participation else "good" if response_rate >= 70 else "neutral",
            description="Atanan anketlere verilen yanitlarin toplu orani.",
        ),
        build_survey_feedback_metric_card(
            key="open_text_answers",
            title="Acik uclu yanit hacmi",
            value=open_text_answers,
            unit="yanit",
            status="info" if open_text_answers else "neutral",
            description="Prompt oncesi maskeleme gerektiren acik metin hacmi.",
        ),
    ]


def build_feedback_pulse_insights(feedback_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Geri bildirim / nabiz tarafindan toplu metrik kartlari uretir."""
    data = feedback_stats or {}
    campaigns = coerce_feedback_number(data.get("feedback_campaigns", data.get("campaigns", 0)))
    submissions = coerce_feedback_number(data.get("feedback_submissions", data.get("submissions", 0)))
    pulse_entries = coerce_feedback_number(data.get("feedback_pulse_entries", data.get("pulse_entries", 0)))
    unanswered = coerce_feedback_number(data.get("unanswered_feedback_count", 0))
    negative = coerce_feedback_number(data.get("negative_pulse_count", 0))
    return [
        build_survey_feedback_metric_card(key="feedback_campaigns", title="Geri bildirim kampanyalari", value=campaigns, unit="kampanya", status="info" if campaigns else "neutral", description="Geri bildirim kampanya kapsami icin toplu sinyal.", source_domain="feedback_pulse"),
        build_survey_feedback_metric_card(key="feedback_submissions", title="Geri bildirim yanitlari", value=submissions, unit="yanit", status="good" if submissions else "neutral", description="Kimlik detayi dokmeden toplam geri bildirim yanit hacmi.", source_domain="feedback_pulse"),
        build_survey_feedback_metric_card(key="feedback_pulse_entries", title="Nabiz kayitlari", value=pulse_entries, unit="kayit", status="info" if pulse_entries else "neutral", description="Kurumsal nabiz izleme icin toplu kayit hacmi.", source_domain="feedback_pulse"),
        build_survey_feedback_metric_card(key="unanswered_feedback_count", title="Yanitsiz geri bildirim sinyali", value=unanswered, unit="kayit", status="warning" if unanswered else "good", description="Takip gerektirebilecek yanitsiz geri bildirim izleri.", source_domain="feedback_pulse"),
        build_survey_feedback_metric_card(key="negative_pulse_count", title="Dusuk/negatif nabiz sinyali", value=negative, unit="sinyal", status="danger" if negative else "good", description="Yonetici incelemesi gerektirebilecek toplu nabiz sinyali.", source_domain="feedback_pulse"),
    ]


def build_survey_feedback_priority_signals(survey_stats: dict[str, Any] | None = None, feedback_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Anket/geri bildirim/nabiz icin oncelik sinyalleri uretir."""
    survey = survey_stats or {}
    feedback = feedback_stats or {}
    assignments = coerce_feedback_number(survey.get("survey_assignments", survey.get("assignments", 0)))
    responses = coerce_feedback_number(survey.get("survey_responses", survey.get("responses", 0)))
    response_rate = calculate_response_rate(responses, assignments)
    unanswered = coerce_feedback_number(feedback.get("unanswered_feedback_count", 0))
    negative = coerce_feedback_number(feedback.get("negative_pulse_count", 0))
    open_text_answers = coerce_feedback_number(survey.get("open_text_answers", 0))
    signals: list[dict[str, object]] = []
    if assignments and response_rate < 50:
        signals.append(build_survey_feedback_priority_signal(key="low_survey_response_rate", title="Dusuk anket katilimi", summary="Anket katilim orani dusuk gorunuyor; kurum ici duyuru veya hedef kitle kontrolu onerilir.", priority="high", sentiment_hint="unknown"))
    if unanswered:
        signals.append(build_survey_feedback_priority_signal(key="unanswered_feedback_followup", title="Yanitsiz geri bildirim takibi", summary="Yanitsiz geri bildirim kayitlari icin insan onayli takip plani olusturulabilir.", priority="medium" if unanswered < 5 else "high", sentiment_hint="mixed", source_domain="feedback_pulse"))
    if negative:
        signals.append(build_survey_feedback_priority_signal(key="negative_pulse_review", title="Negatif nabiz inceleme ihtiyaci", summary="Negatif nabiz sinyalleri yetkili yonetici tarafindan toplu ve anonim duzeyde incelenmelidir.", priority="critical" if negative >= 5 else "high", sentiment_hint="negative", source_domain="feedback_pulse"))
    if open_text_answers:
        signals.append(build_survey_feedback_priority_signal(key="open_text_redaction_required", title="Acik uclu yanit maskeleme gereksinimi", summary="Acik uclu yanitlar AI ozetinden once maskeleme ve veri minimizasyonu kapisindan gecmelidir.", priority="medium", sentiment_hint="unknown"))
    if not signals:
        signals.append(build_survey_feedback_priority_signal(key="survey_feedback_no_priority_risk", title="Oncelikli risk sinyali yok", summary="Anket, geri bildirim ve nabiz verilerinde acil oncelik sinyali gorunmuyor.", priority="low", sentiment_hint="neutral"))
    return signals


def build_survey_feedback_theme_summary(themes: Iterable[dict[str, Any]] | None = None, *, source_domain: str = "survey_feedback") -> dict[str, object]:
    """Tema satirlarini guvenli, kisa ve maskelenmis ozet kartina donusturur."""
    theme_rows = list(themes or [])
    if not theme_rows:
        theme_rows = [{"theme": "Genel memnuniyet", "summary": "Tema verisi henuz yeterli degil."}]
    return build_analytics_safe_summary_card("survey_feedback_pulse", theme_rows, module_type=source_domain)


def build_survey_feedback_insight_context(survey_stats: dict[str, Any] | None = None, feedback_stats: dict[str, Any] | None = None, themes: Iterable[dict[str, Any]] | None = None, *, user_scope: str = "authorized_report_viewer") -> dict[str, object]:
    """Anket/geri bildirim/nabiz icin guvenli karar destek context'i uretir."""
    survey_cards = build_survey_response_insights(survey_stats)
    feedback_cards = build_feedback_pulse_insights(feedback_stats)
    priority_signals = build_survey_feedback_priority_signals(survey_stats, feedback_stats)
    theme_summary = build_survey_feedback_theme_summary(themes)
    return {
        "module": "analytics_center",
        "phase": "faz5_survey_feedback_pulse_analysis_engine",
        "source_domains": ["survey_feedback", "feedback_pulse"],
        "user_scope": str(user_scope or "authorized_report_viewer"),
        "survey_cards": survey_cards,
        "feedback_cards": feedback_cards,
        "priority_signals": priority_signals,
        "theme_summary": theme_summary,
        "counts": {"survey_cards": len(survey_cards), "feedback_cards": len(feedback_cards), "priority_signals": len(priority_signals)},
        "privacy_contract": {"pii_policy": "redact_before_prompt", "open_text_policy": "summarize_after_redaction", "raw_answer_dump": False, "export_policy": "authorized_export_only"},
        "external_ai_call": False,
        "human_approval_required": True,
        "database_change": False,
        "route_change": False,
    }


def build_default_survey_feedback_insights() -> dict[str, object]:
    return build_survey_feedback_insight_context(
        survey_stats={"total_surveys": 4, "active_surveys": 2, "survey_assignments": 120, "survey_responses": 84, "open_text_answers": 18},
        feedback_stats={"feedback_campaigns": 3, "feedback_submissions": 45, "feedback_pulse_entries": 28, "unanswered_feedback_count": 2, "negative_pulse_count": 1},
        themes=[{"theme": "Katilim", "summary": "Katilim orani izlenebilir seviyede."}, {"theme": "Nabiz", "summary": "Birkac negatif sinyal insan onayi gerektirir."}],
    )


def build_survey_feedback_readiness_summary() -> dict[str, object]:
    context = build_default_survey_feedback_insights()
    counts = context.get("counts", {})
    privacy = context.get("privacy_contract", {})
    return {
        "ok": context.get("external_ai_call") is False and context.get("human_approval_required") is True and privacy.get("raw_answer_dump") is False and counts.get("survey_cards", 0) >= 4 and counts.get("feedback_cards", 0) >= 4,
        "phase": context.get("phase"),
        "counts": counts,
        "privacy_contract": privacy,
        "message": "Anket / geri bildirim / nabiz analiz motoru hazir.",
        "next_phase": "Faz 6 — Iletisim ve destek kayitlarindan kurumsal sinyal analizi",
    }
