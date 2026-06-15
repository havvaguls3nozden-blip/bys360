from __future__ import annotations

from typing import Any

from .dashboard_kpi_bridge import build_dashboard_kpi_summary_for_user
from .performance_bridge import build_performance_summary_for_user
from .policy import AI_AGENT_ASSISTANT_PANEL_NOTICE, AI_AGENT_DECISION_NOTICE
from .repository import collect_safe_counts_for_user, insert_agent_audit_log


def _user_id(user: Any) -> int | None:
    try:
        return int(getattr(user, "id", None) or 0) or None
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None


def _display_name(user: Any) -> str:
    for attr in ("full_name", "name", "ad_soyad", "email", "username"):
        value = getattr(user, attr, None)
        if value:
            return str(value)
    return "BYS360 kullanıcısı"


def _card(title: str, value: Any, description: str, route: str, kind: str = "summary") -> dict[str, Any]:
    return {
        "title": title,
        "value": value,
        "description": description,
        "route": route,
        "kind": kind,
    }


def build_assistant_widget_summary_for_user(user: Any) -> dict[str, Any]:
    """AG-4 sağ alt BYS360 Asistanı paneli için güvenli özet üretir.

    Bu fonksiyon veri değiştirmez, idari karar vermez ve hassas içerik dökmez.
    """
    user_id = _user_id(user)
    counts = collect_safe_counts_for_user(user_id)
    performance_summary = build_performance_summary_for_user(user)
    dashboard_kpi_summary = build_dashboard_kpi_summary_for_user(user)

    perf_counts = performance_summary.get("counts", {}) if isinstance(performance_summary, dict) else {}
    kpi_counts = dashboard_kpi_summary.get("counts", {}) if isinstance(dashboard_kpi_summary, dict) else {}

    cards = [
        _card(
            "Bekleyen Değerlendirme",
            perf_counts.get("pending_assignments", counts.get("pending_performance_assignments", 0)),
            "Yetki kapsamındaki bekleyen performans görevleri.",
            "/performance/dashboard",
            "performance",
        ),
        _card(
            "Başkan/Üst Onay",
            perf_counts.get("president_approval_waiting", counts.get("president_approval_waiting", 0)),
            "70 altı süreçlerde onay bekleyen güvenli sayı özeti.",
            "/performance/president-approvals",
            "approval",
        ),
        _card(
            "Yayın Kilidi",
            perf_counts.get("publish_locked_scorecards", counts.get("publish_locked_scorecards", 0)),
            "Yayın öncesi kontrol gerektiren karne sayısı.",
            "/performance/process-tracking",
            "publish",
        ),
        _card(
            "Riskli Hedef",
            kpi_counts.get("risky_targets", 0),
            "KPI/Hedef bağlantısında takip gerektiren hedef sayısı.",
            "/performans/stratejik/kpi-dashboard",
            "kpi",
        ),
        _card(
            "Ortalama Gerçekleşme",
            f"%{kpi_counts.get('average_completion', 0)}",
            "Yetki kapsamındaki KPI/Hedef ortalama gerçekleşme oranı.",
            "/performans/stratejik/kpi-analiz",
            "kpi",
        ),
        _card(
            "Açık Destek Talebi",
            counts.get("open_support_tickets", 0),
            "Size bağlı açık destek talebi sayısı.",
            "/support",
            "support",
        ),
    ]

    quick_questions = [
        "Bugünkü yönetici özetimi göster",
        "Performansta bekleyenleri özetle",
        "Riskli KPI hedeflerini göster",
        "Başkan onayı bekleyen var mı?",
        "Yayın kilidindeki karneleri özetle",
    ]

    response = {
        "ok": True,
        "version": "AG-4 V1",
        "display_name": _display_name(user),
        "notice": AI_AGENT_DECISION_NOTICE,
        "assistant_notice": AI_AGENT_ASSISTANT_PANEL_NOTICE,
        "cards": cards,
        "quick_questions": quick_questions,
        "counts": counts,
        "performance_summary": performance_summary,
        "dashboard_kpi_summary": dashboard_kpi_summary,
        "routes": {
            "panel": "/ai-agent/panel",
            "ask": "/ai-agent/api/ask",
            "summary": "/ai-agent/api/assistant-widget-summary",
        },
    }

    insert_agent_audit_log(
        user_id=user_id,
        action_key="ag4_assistant_widget_summary",
        detail=f"AG-4 BYS360 Asistanı panel özeti görüntülendi. Kart sayısı: {len(cards)}",
    )
    return response
