from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""Iletisim ve destek kayitlarindan kurumsal sinyal analizi servis koprusu.

Faz 6 canli davranis degistirmez. Veritabanina yazmaz, commit yapmaz,
route/template degistirmez ve dis AI servisine istek atmaz. Mesajlasma ve
yardim/destek kayitlarindan kisisel icerik dokmeden toplu, maskelenmis ve
insan onayli karar destek sinyalleri uretir.
"""

from dataclasses import asdict, dataclass
from typing import Any
from collections.abc import Iterable

try:
    from .summary_pipeline import build_analytics_safe_summary_card
except ImportError:  # python -S gate bagimsiz calistirmasi
    from analytics_center.summary_pipeline import build_analytics_safe_summary_card


@dataclass(frozen=True)
class CommunicationSupportMetricCard:
    key: str
    title: str
    value: int | float | str
    unit: str = "adet"
    status: str = "neutral"
    description: str = ""
    source_domain: str = "communication_support"
    visibility_scope: str = "authorized_report_viewer"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CommunicationSupportSignal:
    key: str
    title: str
    summary: str
    priority: str = "normal"
    severity: str = "neutral"
    source_domain: str = "communication_support"
    action_hint: str = "Insan onayiyla degerlendiriniz."
    visibility_scope: str = "authorized_report_viewer"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_ALLOWED_STATUSES = {"good", "warning", "danger", "neutral", "info"}
_ALLOWED_PRIORITIES = {"low", "normal", "medium", "high", "critical"}
_ALLOWED_SEVERITIES = {"info", "neutral", "warning", "danger", "critical"}


def coerce_signal_number(value: Any, default: int = 0) -> int | float:
    """Iletisim/destek metrikleri icin guvenli sayi donusturur."""
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
        logger.exception("BYS360 V6C guarded exception | file=app/services/analytics_center/communication_support_insights.py | line=69")
        return default


def clamp_signal_percentage(value: Any) -> int | float:
    number = coerce_signal_number(value, default=0)
    try:
        return max(0, min(100, number))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/analytics_center/communication_support_insights.py | line=77")
        return 0


def calculate_support_resolution_rate(closed_items: Any, total_items: Any) -> int | float:
    closed_count = coerce_signal_number(closed_items, default=0)
    total_count = coerce_signal_number(total_items, default=0)
    if not total_count:
        return 0
    return round(clamp_signal_percentage((closed_count / total_count) * 100), 2)


def normalize_signal_status(status: Any) -> str:
    value = str(status or "neutral").strip().lower()
    return value if value in _ALLOWED_STATUSES else "neutral"


def normalize_signal_priority(priority: Any) -> str:
    value = str(priority or "normal").strip().lower()
    return value if value in _ALLOWED_PRIORITIES else "normal"


def normalize_signal_severity(severity: Any) -> str:
    value = str(severity or "neutral").strip().lower()
    return value if value in _ALLOWED_SEVERITIES else "neutral"


def build_communication_support_metric_card(
    *,
    key: str,
    title: str,
    value: Any,
    unit: str = "adet",
    status: str = "neutral",
    description: str = "",
    source_domain: str = "communication_support",
    visibility_scope: str = "authorized_report_viewer",
) -> dict[str, object]:
    return CommunicationSupportMetricCard(
        key=str(key or "communication_support_metric").strip() or "communication_support_metric",
        title=str(title or "Iletisim / Destek Sinyali").strip() or "Iletisim / Destek Sinyali",
        value=coerce_signal_number(value, default=0),
        unit=str(unit or "adet"),
        status=normalize_signal_status(status),
        description=str(description or ""),
        source_domain=str(source_domain or "communication_support"),
        visibility_scope=str(visibility_scope or "authorized_report_viewer"),
    ).to_dict()


def build_communication_support_signal(
    *,
    key: str,
    title: str,
    summary: Any,
    priority: str = "normal",
    severity: str = "neutral",
    source_domain: str = "communication_support",
    action_hint: str = "Insan onayiyla degerlendiriniz.",
    visibility_scope: str = "authorized_report_viewer",
) -> dict[str, object]:
    safe_summary = build_analytics_safe_summary_card(
        "communication_support_signal",
        [{"summary": str(summary or "")}],
        module_type=source_domain,
    )
    return CommunicationSupportSignal(
        key=str(key or "communication_support_signal").strip() or "communication_support_signal",
        title=str(title or "Iletisim / Destek Oncelik Sinyali").strip() or "Iletisim / Destek Oncelik Sinyali",
        summary=str(safe_summary.get("summary_text") or "Guvenli ozet hazirlanamadi."),
        priority=normalize_signal_priority(priority),
        severity=normalize_signal_severity(severity),
        source_domain=str(source_domain or "communication_support"),
        action_hint=str(action_hint or "Insan onayiyla degerlendiriniz."),
        visibility_scope=str(visibility_scope or "authorized_report_viewer"),
    ).to_dict()


def build_message_load_insights(message_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Mesajlasma tarafindan ham mesaj icerigi dokmeden toplu kartlar uretir."""
    data = message_stats or {}
    threads = coerce_signal_number(data.get("message_threads", data.get("threads", 0)))
    messages = coerce_signal_number(data.get("messages", data.get("message_count", 0)))
    attachments = coerce_signal_number(data.get("message_attachments", data.get("attachments", 0)))
    reactions = coerce_signal_number(data.get("message_reactions", data.get("reactions", 0)))
    unread = coerce_signal_number(data.get("unread_message_count", data.get("unread", 0)))
    return [
        build_communication_support_metric_card(key="message_threads", title="Mesaj konu basliklari", value=threads, unit="konu", status="info" if threads else "neutral", description="Mesajlasma thread hacmi; ham mesaj icerigi gosterilmez."),
        build_communication_support_metric_card(key="messages", title="Mesaj hacmi", value=messages, unit="mesaj", status="info" if messages else "neutral", description="Kisisel mesaj metni yerine toplu hacim sinyali."),
        build_communication_support_metric_card(key="message_attachments", title="Ekli dosya sinyali", value=attachments, unit="ek", status="warning" if attachments >= 20 else "info" if attachments else "neutral", description="Destek veya is akisi yogunluguna isaret edebilecek ek dosya hacmi."),
        build_communication_support_metric_card(key="message_reactions", title="Etkilesim sinyali", value=reactions, unit="tepki", status="good" if reactions else "neutral", description="Mesajlasma etkilesiminin toplu gostergesi."),
        build_communication_support_metric_card(key="unread_message_count", title="Okunmamis mesaj sinyali", value=unread, unit="mesaj", status="warning" if unread else "good", description="Takip gerektirebilecek okunmamis mesaj hacmi."),
    ]


def build_support_ticket_insights(support_stats: dict[str, Any] | None = None) -> list[dict[str, object]]:
    """Yardim merkezi / destek kayitlarindan toplu metrik kartlari uretir."""
    data = support_stats or {}
    tickets = coerce_signal_number(data.get("support_tickets", data.get("tickets", 0)))
    open_items = coerce_signal_number(data.get("open_support_tickets", data.get("open_items", 0)))
    closed_items = coerce_signal_number(data.get("closed_support_tickets", data.get("closed_items", 0)))
    overdue = coerce_signal_number(data.get("overdue_support_tickets", data.get("overdue", 0)))
    attachments = coerce_signal_number(data.get("support_ticket_attachments", data.get("ticket_attachments", 0)))
    resolution_rate = calculate_support_resolution_rate(closed_items, tickets)
    return [
        build_communication_support_metric_card(key="support_tickets", title="Destek talebi hacmi", value=tickets, unit="talep", status="info" if tickets else "neutral", description="Yardim merkezi toplam talep hacmi.", source_domain="support_center"),
        build_communication_support_metric_card(key="open_support_tickets", title="Acik destek talepleri", value=open_items, unit="talep", status="warning" if open_items else "good", description="Takip bekleyen acik destek talepleri.", source_domain="support_center"),
        build_communication_support_metric_card(key="support_resolution_rate", title="Destek kapanma orani", value=resolution_rate, unit="%", status="good" if resolution_rate >= 70 else "warning" if tickets else "neutral", description="Toplu destek kapanma orani.", source_domain="support_center"),
        build_communication_support_metric_card(key="overdue_support_tickets", title="Gecikmis destek sinyali", value=overdue, unit="talep", status="danger" if overdue else "good", description="SLA/yanit suresi acisindan yonetici takibi gerektiren sinyal.", source_domain="support_center"),
        build_communication_support_metric_card(key="support_ticket_attachments", title="Destek eki hacmi", value=attachments, unit="ek", status="info" if attachments else "neutral", description="Destek taleplerindeki ek dosya hacmi.", source_domain="support_center"),
    ]


def build_communication_support_priority_signals(
    message_stats: dict[str, Any] | None = None,
    support_stats: dict[str, Any] | None = None,
) -> list[dict[str, object]]:
    """Iletisim/destek icin karar destek oncelik sinyalleri uretir."""
    message_data = message_stats or {}
    support_data = support_stats or {}
    unread = coerce_signal_number(message_data.get("unread_message_count", message_data.get("unread", 0)))
    messages = coerce_signal_number(message_data.get("messages", message_data.get("message_count", 0)))
    threads = coerce_signal_number(message_data.get("message_threads", message_data.get("threads", 0)))
    open_items = coerce_signal_number(support_data.get("open_support_tickets", support_data.get("open_items", 0)))
    overdue = coerce_signal_number(support_data.get("overdue_support_tickets", support_data.get("overdue", 0)))
    tickets = coerce_signal_number(support_data.get("support_tickets", support_data.get("tickets", 0)))
    closed = coerce_signal_number(support_data.get("closed_support_tickets", support_data.get("closed_items", 0)))
    resolution_rate = calculate_support_resolution_rate(closed, tickets)

    signals: list[dict[str, object]] = []
    if unread:
        signals.append(build_communication_support_signal(key="unread_message_followup", title="Okunmamis mesaj takibi", summary="Okunmamis mesaj hacmi yetkili kullanici tarafindan toplu olarak incelenmelidir.", priority="medium" if unread < 20 else "high", severity="warning"))
    if threads and messages and messages / max(threads, 1) >= 20:
        signals.append(build_communication_support_signal(key="high_message_density", title="Yuksek mesaj yogunlugu", summary="Bazi mesaj konularinda is akisi yogunlugu artmis olabilir; ham mesaj icerigi gosterilmeden konu bazli takip onerilir.", priority="medium", severity="warning"))
    if open_items:
        signals.append(build_communication_support_signal(key="open_support_followup", title="Acik destek talepleri", summary="Acik destek talepleri icin cevap/onceliklendirme takibi gerekebilir.", priority="medium" if open_items < 10 else "high", severity="warning", source_domain="support_center"))
    if overdue:
        signals.append(build_communication_support_signal(key="overdue_support_review", title="Gecikmis destek talebi incelemesi", summary="Gecikmis destek talepleri SLA ve hizmet kalitesi acisindan insan onayli inceleme gerektirir.", priority="critical" if overdue >= 5 else "high", severity="danger", source_domain="support_center"))
    if tickets and resolution_rate < 50:
        signals.append(build_communication_support_signal(key="low_support_resolution_rate", title="Dusuk destek kapanma orani", summary="Destek kapanma orani dusuk gorunuyor; surec darboğazi insan onayiyla incelenmelidir.", priority="high", severity="warning", source_domain="support_center"))
    if not signals:
        signals.append(build_communication_support_signal(key="communication_support_no_priority_risk", title="Oncelikli iletisim/destek riski yok", summary="Iletisim ve destek verilerinde acil oncelik sinyali gorunmuyor.", priority="low", severity="neutral"))
    return signals


def build_communication_support_topic_summary(topics: Iterable[dict[str, Any]] | None = None) -> list[dict[str, object]]:
    """Ham mesaj/destek icerigi yerine konu ozeti uretir."""
    output: list[dict[str, object]] = []
    for index, item in enumerate(topics or [], start=1):
        topic = str(item.get("topic") or item.get("title") or f"Konu {index}").strip()
        summary = str(item.get("summary") or item.get("description") or "Toplu konu sinyali.").strip()
        source_domain = str(item.get("source_domain") or "communication_support").strip()
        output.append(build_communication_support_signal(
            key=f"topic_{index}",
            title=topic[:120] or f"Konu {index}",
            summary=summary,
            priority=str(item.get("priority") or "normal"),
            severity=str(item.get("severity") or "neutral"),
            source_domain=source_domain,
            action_hint="Konu ozeti yetkili kullanici tarafindan incelenmelidir.",
        ))
    if not output:
        output.append(build_communication_support_signal(key="topic_summary_empty", title="Konu ozeti yok", summary="Iletisim/destek icin konu kumesi uretilmedi; ham metin dokulmedi.", priority="low", severity="neutral"))
    return output


def build_communication_support_insight_context(
    message_stats: dict[str, Any] | None = None,
    support_stats: dict[str, Any] | None = None,
    topics: Iterable[dict[str, Any]] | None = None,
) -> dict[str, object]:
    """Iletisim ve destek sinyallerini karar destek context'ine donusturur."""
    message_cards = build_message_load_insights(message_stats)
    support_cards = build_support_ticket_insights(support_stats)
    priority_signals = build_communication_support_priority_signals(message_stats, support_stats)
    topic_summary = build_communication_support_topic_summary(topics)
    safe_summary = build_analytics_safe_summary_card(
        "communication_support_signal",
        [{"message_cards": message_cards, "support_cards": support_cards, "priority_signals": priority_signals, "topic_summary": topic_summary}],
        module_type="communication_support",
    )
    return {
        "module": "analytics_center",
        "phase": "faz6_communication_support_signal_analysis",
        "source_domains": ["communication", "support_center"],
        "message_cards": message_cards,
        "support_cards": support_cards,
        "priority_signals": priority_signals,
        "topic_summary": topic_summary,
        "safe_summary": safe_summary,
        "counts": {
            "message_cards": len(message_cards),
            "support_cards": len(support_cards),
            "priority_signals": len(priority_signals),
            "topic_summary": len(topic_summary),
        },
        "privacy_contract": {
            "raw_message_dump": False,
            "raw_ticket_body_dump": False,
            "personal_content_dump": False,
            "topic_summary_only": True,
            "redact_before_prompt": True,
            "visibility_scope": "authorized_report_viewer",
        },
        "external_ai_call": False,
        "human_approval_required": True,
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
    }


def build_default_communication_support_insights() -> dict[str, object]:
    return build_communication_support_insight_context(
        message_stats={"message_threads": 8, "messages": 132, "message_attachments": 11, "message_reactions": 23, "unread_message_count": 9},
        support_stats={"support_tickets": 18, "open_support_tickets": 5, "closed_support_tickets": 11, "overdue_support_tickets": 2, "support_ticket_attachments": 7},
        topics=[
            {"topic": "Destek yanit suresi", "summary": "Acik destek taleplerinin cevap takibi guclendirilebilir.", "priority": "medium", "severity": "warning", "source_domain": "support_center"},
            {"topic": "Mesaj yogunlugu", "summary": "Bazi iletisim basliklarinda yogunluk artisi var; konu bazli inceleme onerilir.", "priority": "normal", "severity": "info"},
        ],
    )


def build_communication_support_readiness_summary() -> dict[str, object]:
    context = build_default_communication_support_insights()
    privacy = context.get("privacy_contract", {})
    return {
        "ok": context.get("external_ai_call") is False
        and context.get("human_approval_required") is True
        and privacy.get("raw_message_dump") is False
        and privacy.get("raw_ticket_body_dump") is False
        and context.get("counts", {}).get("message_cards", 0) >= 5
        and context.get("counts", {}).get("support_cards", 0) >= 5,
        "phase": context["phase"],
        "counts": context["counts"],
        "privacy_contract": privacy,
        "message": "Iletisim ve destek sinyal analizi hazir.",
        "next_phase": "Faz 7 — Analiz Merkezi Excel yukleme ve veri on izleme",
    }
