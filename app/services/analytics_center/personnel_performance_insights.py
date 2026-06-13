from __future__ import annotations


import logging

from app.core.datetime_utils import utc_now
"""Personel / performans icgoru motoru servis koprusu.

Faz 4 canli davranis degistirmez. Veritabanina yazmaz, commit yapmaz,
runtime dis AI cagrisi yapmaz. Personel ve performans tarafindan gelen sayisal
ve kural bazli sinyalleri guvenli karar destek payload'larina donusturur.

Bu dosyanin hedefi Analiz Merkezi icin toplu, maskelenmis ve yetkiyle
kullanilabilecek personel / performans icgoru yuzeyi uretmektir.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Iterable
logger = logging.getLogger(__name__)

try:
    from .summary_pipeline import build_analytics_safe_summary_card
except ImportError:  # python -S gate bagimsiz calistirmasi
    from analytics_center.summary_pipeline import build_analytics_safe_summary_card


@dataclass(frozen=True)
class PersonnelInsightCard:
    key: str
    title: str
    value: int | float | str
    unit: str = "adet"
    status: str = "neutral"
    description: str = ""
    source_domain: str = "personnel"
    visibility_scope: str = "manager"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PerformanceInsightSignal:
    key: str
    title: str
    summary: str
    severity: str = "info"
    source_domain: str = "performance"
    action_hint: str = "Insan onayiyla degerlendiriniz."
    visibility_scope: str = "manager"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_ALLOWED_STATUSES = {"good", "warning", "danger", "neutral", "info"}
_ALLOWED_SEVERITIES = {"low", "medium", "high", "critical", "info"}


def coerce_insight_number(value: Any, default: int = 0) -> int | float:
    """Personel/performans icgorusu icin guvenli sayi donusturur."""
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
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def clamp_percentage(value: Any) -> int | float:
    """Yuzde degerini 0-100 araliginda tutar."""
    number = coerce_insight_number(value, default=0)
    try:
        return max(0, min(100, number))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0


def normalize_insight_status(status: Any) -> str:
    value = str(status or "neutral").strip().lower()
    return value if value in _ALLOWED_STATUSES else "neutral"


def normalize_insight_severity(severity: Any) -> str:
    value = str(severity or "info").strip().lower()
    return value if value in _ALLOWED_SEVERITIES else "info"


def calculate_completion_rate(completed: Any, total: Any) -> int | float:
    """Tamamlanma oranini guvenli yuzde olarak hesaplar."""
    completed_number = coerce_insight_number(completed, default=0)
    total_number = coerce_insight_number(total, default=0)
    if not total_number:
        return 0
    return round(clamp_percentage((completed_number / total_number) * 100), 2)


def build_personnel_insight_card(
    *,
    key: str,
    title: str,
    value: Any,
    unit: str = "adet",
    status: str = "neutral",
    description: str = "",
    source_domain: str = "personnel",
    visibility_scope: str = "manager",
) -> dict[str, object]:
    return PersonnelInsightCard(
        key=str(key or "personnel_signal").strip() or "personnel_signal",
        title=str(title or "Personel Sinyali").strip() or "Personel Sinyali",
        value=coerce_insight_number(value, default=0),
        unit=str(unit or "adet"),
        status=normalize_insight_status(status),
        description=str(description or ""),
        source_domain=str(source_domain or "personnel"),
        visibility_scope=str(visibility_scope or "manager"),
    ).to_dict()


def build_performance_signal(
    *,
    key: str,
    title: str,
    summary: Any,
    severity: str = "info",
    source_domain: str = "performance",
    action_hint: str = "Insan onayiyla degerlendiriniz.",
    visibility_scope: str = "manager",
) -> dict[str, object]:
    safe_summary = build_analytics_safe_summary_card(
        "performance_insights",
        [{"summary": str(summary or "")}],
        module_type=source_domain,
    )
    return PerformanceInsightSignal(
        key=str(key or "performance_signal").strip() or "performance_signal",
        title=str(title or "Performans Sinyali").strip() or "Performans Sinyali",
        summary=str(safe_summary.get("summary_text") or "Guvenli ozet hazirlanamadi."),
        severity=normalize_insight_severity(severity),
        source_domain=str(source_domain or "performance"),
        action_hint=str(action_hint or "Insan onayiyla degerlendiriniz."),
        visibility_scope=str(visibility_scope or "manager"),
    ).to_dict()


def build_personnel_structure_insights(personnel_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Personel ve organizasyon yapisi icin toplu icgoru kartlari uretir."""
    data = personnel_stats or {}
    total_personnel = coerce_insight_number(data.get("total_personnel", data.get("personnel_total", 0)))
    active_personnel = coerce_insight_number(data.get("active_personnel", total_personnel))
    missing_manager = coerce_insight_number(data.get("missing_manager_count", 0))
    unit_count = coerce_insight_number(data.get("unit_count", 0))
    assignment_history = coerce_insight_number(data.get("assignment_history_count", 0))
    manager_status = "warning" if missing_manager else "good"
    return [
        build_personnel_insight_card(
            key="total_personnel",
            title="Toplam personel gorunumu",
            value=total_personnel,
            unit="kisi",
            status="info",
            description="Kimlik detayina girmeden toplu personel sayisi.",
        ),
        build_personnel_insight_card(
            key="active_personnel",
            title="Aktif personel",
            value=active_personnel,
            unit="kisi",
            status="good" if active_personnel else "neutral",
            description="Aktif personel havuzu icin toplu sinyal.",
        ),
        build_personnel_insight_card(
            key="missing_manager_count",
            title="Eksik amir/hiyerarsi sinyali",
            value=missing_manager,
            unit="kayit",
            status=manager_status,
            description="Yetkili kontrol gerektirebilecek bos amir/hiyerarsi izleri.",
        ),
        build_personnel_insight_card(
            key="unit_count",
            title="Birim kapsami",
            value=unit_count,
            unit="birim",
            status="info",
            description="Organizasyon birimi dagilimi icin ust ozet.",
        ),
        build_personnel_insight_card(
            key="assignment_history_count",
            title="Organizasyon atama gecmisi",
            value=assignment_history,
            unit="kayit",
            status="neutral",
            description="Personel org atama gecmisi icin toplu izleme sinyali.",
        ),
    ]


def build_performance_process_insights(performance_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Performans sureci icin toplu puan/yayin/gorev icgoru kartlari uretir."""
    data = performance_stats or {}
    total_assignments = coerce_insight_number(data.get("total_assignments", 0))
    completed_assignments = coerce_insight_number(data.get("completed_assignments", 0))
    pending_assignments = coerce_insight_number(data.get("pending_assignments", max(total_assignments - completed_assignments, 0)))
    completion_rate = calculate_completion_rate(completed_assignments, total_assignments)
    unpublished_results = coerce_insight_number(data.get("unpublished_results", 0))
    low_score_count = coerce_insight_number(data.get("low_score_count", 0))
    high_score_count = coerce_insight_number(data.get("high_score_count", 0))
    missing_comment_count = coerce_insight_number(data.get("missing_required_comment_count", 0))
    return [
        build_personnel_insight_card(
            key="performance_completion_rate",
            title="Degerlendirme tamamlanma orani",
            value=completion_rate,
            unit="%",
            status="good" if completion_rate >= 90 else "warning" if completion_rate else "neutral",
            description="Tamamlanan degerlendirme gorevlerinin toplu yuzdesi.",
            source_domain="performance",
        ),
        build_personnel_insight_card(
            key="pending_assignments",
            title="Bekleyen degerlendirme gorevi",
            value=pending_assignments,
            unit="gorev",
            status="warning" if pending_assignments else "good",
            description="Gercek gorev akisi icindeki bekleyen isler.",
            source_domain="performance",
        ),
        build_personnel_insight_card(
            key="unpublished_results",
            title="Yayin bekleyen sonuc",
            value=unpublished_results,
            unit="sonuc",
            status="warning" if unpublished_results else "good",
            description="Personel sonuc gorunurlugu yayin kapisina baglidir.",
            source_domain="performance",
        ),
        build_personnel_insight_card(
            key="score_outlier_count",
            title="Esik puan sinyali",
            value=low_score_count + high_score_count,
            unit="kayit",
            status="warning" if (low_score_count or high_score_count) else "good",
            description="70 alti ve 90 ustu sonuclar icin yonetsel takip sinyali.",
            source_domain="performance",
        ),
        build_personnel_insight_card(
            key="missing_required_comment_count",
            title="Eksik zorunlu aciklama sinyali",
            value=missing_comment_count,
            unit="kayit",
            status="danger" if missing_comment_count else "good",
            description="1/5 puan veya esik disi sonuc aciklamalari icin kontrol sinyali.",
            source_domain="performance",
        ),
    ]


def build_personnel_performance_risk_signals(
    personnel_stats: dict[str, Any] | None = None,
    performance_stats: dict[str, Any] | None = None,
) -> list[dict[str, object]]:
    """Personel ve performans icin insan onayli risk/onceklik sinyalleri uretir."""
    personnel = personnel_stats or {}
    performance = performance_stats or {}
    missing_manager = coerce_insight_number(personnel.get("missing_manager_count", 0))
    pending_assignments = coerce_insight_number(performance.get("pending_assignments", 0))
    unpublished_results = coerce_insight_number(performance.get("unpublished_results", 0))
    low_score_count = coerce_insight_number(performance.get("low_score_count", 0))
    missing_comment_count = coerce_insight_number(performance.get("missing_required_comment_count", 0))
    signals: list[dict[str, object]] = []
    if missing_manager:
        signals.append(
            build_performance_signal(
                key="missing_manager_review",
                title="Hiyerarsi kontrol onceligi",
                summary=f"{missing_manager} kayitta eksik amir/hiyerarsi sinyali var. Personel yonetimi ve performans gorev uretimi once kontrol edilmelidir.",
                severity="high",
                source_domain="personnel",
            )
        )
    if pending_assignments:
        signals.append(
            build_performance_signal(
                key="pending_assignment_followup",
                title="Bekleyen gorev takip onceligi",
                summary=f"{pending_assignments} performans gorevi tamamlanmayi bekliyor. Zincir sirasina gore yonetici takibi onerilir.",
                severity="medium",
            )
        )
    if unpublished_results:
        signals.append(
            build_performance_signal(
                key="publication_readiness_review",
                title="Yayin oncesi kontrol",
                summary=f"{unpublished_results} sonuc yayin bekliyor. Personel gorunurlugu acilmadan once IK/Admin kontrolu korunmalidir.",
                severity="medium",
            )
        )
    if low_score_count or missing_comment_count:
        signals.append(
            build_performance_signal(
                key="threshold_comment_review",
                title="Esik puan ve aciklama kontrolu",
                summary=f"{low_score_count} dusuk puan sinyali ve {missing_comment_count} eksik aciklama sinyali var. Insan onayli detay inceleme gerekir.",
                severity="high" if missing_comment_count else "medium",
            )
        )
    if not signals:
        signals.append(
            build_performance_signal(
                key="personnel_performance_stable",
                title="Personel / performans genel durum",
                summary="Toplu sinyallerde kritik oncelik bulunmadi. Yine de karar oncesi yetkili insan kontrolu korunmalidir.",
                severity="info",
            )
        )
    return signals


def build_personnel_performance_insight_context(
    *,
    personnel_stats: dict[str, Any] | None = None,
    performance_stats: dict[str, Any] | None = None,
    user_scope: str = "manager",
) -> dict[str, object]:
    """Analiz Merkezi icin personel/performans icgoru context'i uretir."""
    personnel_cards = build_personnel_structure_insights(personnel_stats)
    performance_cards = build_performance_process_insights(performance_stats)
    risk_signals = build_personnel_performance_risk_signals(personnel_stats, performance_stats)
    safe_summary = build_analytics_safe_summary_card(
        "performance_insights",
        [
            {"personnel_cards": len(personnel_cards)},
            {"performance_cards": len(performance_cards)},
            {"risk_signals": len(risk_signals)},
        ],
        module_type="performance",
    )
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz4_personnel_performance_insight_engine",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "external_ai_call": False,
        "user_scope": str(user_scope or "manager"),
        "personnel_cards": personnel_cards,
        "performance_cards": performance_cards,
        "risk_signals": risk_signals,
        "safe_summary": safe_summary,
        "counts": {
            "personnel_cards": len(personnel_cards),
            "performance_cards": len(performance_cards),
            "risk_signals": len(risk_signals),
        },
        "visibility_note": "Yetkiye bagli, toplu, maskelenmis personel/performans icgorusu.",
        "human_approval_required": True,
    }


def build_default_personnel_performance_insights() -> dict[str, object]:
    """Faz 4 gate ve UI entegrasyonlari icin ornek guvenli context uretir."""
    return build_personnel_performance_insight_context(
        personnel_stats={
            "total_personnel": 120,
            "active_personnel": 118,
            "missing_manager_count": 2,
            "unit_count": 8,
            "assignment_history_count": 42,
        },
        performance_stats={
            "total_assignments": 180,
            "completed_assignments": 150,
            "pending_assignments": 30,
            "unpublished_results": 12,
            "low_score_count": 3,
            "high_score_count": 5,
            "missing_required_comment_count": 1,
        },
        user_scope="manager",
    )


def build_personnel_performance_readiness_summary() -> dict[str, object]:
    context = build_default_personnel_performance_insights()
    return {
        "ok": context["external_ai_call"] is False
        and context["human_approval_required"] is True
        and context["counts"]["personnel_cards"] >= 4
        and context["counts"]["performance_cards"] >= 4
        and context["counts"]["risk_signals"] >= 1,
        "phase": context["phase"],
        "counts": context["counts"],
        "external_ai_call": context["external_ai_call"],
        "human_approval_required": context["human_approval_required"],
        "message": "Personel / performans icgoru motoru hazir.",
        "next_phase": "Faz 5 — Anket / geri bildirim / nabiz analiz motoru",
    }
