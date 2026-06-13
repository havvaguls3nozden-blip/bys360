from __future__ import annotations



from app.core.datetime_utils import utc_now
"""Analiz Merkezi servis envanteri."""

from datetime import datetime

from .live_scope import ANALYTICS_SURFACE_KEYS, build_analytics_surface_summary, get_analytics_surfaces
from .summary_pipeline import build_analytics_summary_cache_plan, build_analytics_summary_pipeline_summary


def build_analytics_center_faz0_inventory() -> dict[str, object]:
    return {
        "module": "analytics_center",
        "phase": "faz0_inventory_safe_service_skeleton",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "surface_keys": list(ANALYTICS_SURFACE_KEYS),
        "surfaces": get_analytics_surfaces(),
        "summary": build_analytics_surface_summary(),
    }


def build_analytics_center_faz1_inventory() -> dict[str, object]:
    return {
        "module": "analytics_center",
        "phase": "faz1_ai_request_redaction_bridge_ready",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "surface_keys": list(ANALYTICS_SURFACE_KEYS),
        "ai_log_bridge": "app/services/ai_decision/logging_bridge.py",
        "ai_redaction_bridge": "app/services/ai_decision/redaction_bridge.py",
        "safe_mode": True,
        "next_phase": "Faz 2 — AI özet cache ve güvenli özetleme altyapısı",
    }


def build_analytics_center_faz2_inventory() -> dict[str, object]:
    sample_rows = [
        {"topic": "personel", "count": 12, "note": "Toplu görünüm"},
        {"topic": "performans", "count": 5, "note": "Yayın öncesi takip"},
    ]
    return {
        "module": "analytics_center",
        "phase": "faz2_summary_cache_safe_summarization",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "surface_keys": list(ANALYTICS_SURFACE_KEYS),
        "summary_cache_plan": build_analytics_summary_cache_plan("executive_overview", sample_rows),
        "pipeline_summary": build_analytics_summary_pipeline_summary(),
        "safe_mode": True,
        "next_phase": "Faz 3 — Karar destek dashboard veri yüzeyi",
    }


def build_analytics_center_readiness_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz0_inventory()
    return {
        "ok": len(inventory["surface_keys"]) >= 6,
        "surface_count": len(inventory["surface_keys"]),
        "message": "Analiz Merkezi Faz 0 veri yüzeyi envanteri hazır.",
        "next_phase": "Faz 1 — AI log / request / redaction servis köprüsü",
    }


def build_analytics_center_bridge_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz1_inventory()
    return {
        "ok": inventory["safe_mode"] is True and len(inventory["surface_keys"]) >= 6,
        "phase": inventory["phase"],
        "message": "Analiz Merkezi AI log/redaction köprüsüne hazır.",
        "next_phase": inventory["next_phase"],
    }


def build_analytics_center_summary_cache_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz2_inventory()
    return {
        "ok": inventory["safe_mode"] is True and inventory["pipeline_summary"]["ok"] is True,
        "phase": inventory["phase"],
        "message": "Analiz Merkezi güvenli özet cache pipeline hazır.",
        "next_phase": inventory["next_phase"],
    }


def build_analytics_center_faz3_inventory() -> dict[str, object]:
    from .dashboard_surface import build_ai_decision_dashboard_readiness_summary, build_ai_decision_dashboard_surface

    dashboard_surface = build_ai_decision_dashboard_surface(
        raw_metrics={"personnel_total": 24, "performance_pending": 4, "survey_response_rate": 76, "support_open_items": 3},
        source_counts={"personnel": 24, "performance": 4, "survey_feedback": 7, "communication_support": 3, "uploaded_analysis_file": 0},
        user_scope="manager",
    )
    return {
        "module": "analytics_center",
        "phase": "faz3_dashboard_data_surface",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/dashboard_surface.py"],
        "surface_keys": list(ANALYTICS_SURFACE_KEYS),
        "dashboard_surface": dashboard_surface,
        "readiness_summary": build_ai_decision_dashboard_readiness_summary(),
        "safe_mode": True,
        "next_phase": "Faz 4 — Personel / performans içgörü motoru",
    }


def build_analytics_center_dashboard_surface_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz3_inventory()
    summary = inventory["readiness_summary"]
    return {
        "ok": summary["ok"] is True and inventory["dashboard_surface"]["external_ai_call"] is False,
        "phase": inventory["phase"],
        "message": "Karar Destek Dashboard veri yüzeyi hazır.",
        "metric_count": inventory["dashboard_surface"]["counts"]["metric_cards"],
        "signal_count": inventory["dashboard_surface"]["counts"]["signal_cards"],
        "next_phase": inventory["next_phase"],
    }


def build_analytics_center_faz4_inventory() -> dict[str, object]:
    from .personnel_performance_insights import build_personnel_performance_readiness_summary, build_default_personnel_performance_insights

    insight_context = build_default_personnel_performance_insights()
    return {
        "module": "analytics_center",
        "phase": "faz4_personnel_performance_insight_engine",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/personnel_performance_insights.py"],
        "surface_keys": ["personnel_structure", "performance_insights"],
        "supported_outputs": ["personnel_cards", "performance_cards", "risk_signals", "safe_summary"],
        "insight_context": insight_context,
        "readiness_summary": build_personnel_performance_readiness_summary(),
        "safe_mode": True,
        "external_ai_call": False,
        "human_approval_required": True,
        "next_phase": "Faz 5 — Anket / geri bildirim / nabiz analiz motoru",
    }


def build_analytics_center_personnel_performance_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz4_inventory()
    summary = inventory["readiness_summary"]
    return {
        "ok": summary["ok"] is True and inventory["external_ai_call"] is False and inventory["human_approval_required"] is True,
        "phase": inventory["phase"],
        "message": "Personel / performans icgoru motoru hazir.",
        "supported_outputs": inventory["supported_outputs"],
        "counts": summary["counts"],
        "next_phase": inventory["next_phase"],
    }


def build_analytics_center_faz5_inventory() -> dict[str, object]:
    from .survey_feedback_insights import build_default_survey_feedback_insights, build_survey_feedback_readiness_summary

    insight_context = build_default_survey_feedback_insights()
    return {
        "module": "analytics_center",
        "phase": "faz5_survey_feedback_pulse_analysis_engine",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/survey_feedback_insights.py"],
        "surface_keys": ["survey_feedback_pulse"],
        "supported_outputs": ["survey_cards", "feedback_cards", "priority_signals", "theme_summary"],
        "source_domains": ["survey_feedback", "feedback_pulse"],
        "insight_context": insight_context,
        "readiness_summary": build_survey_feedback_readiness_summary(),
        "safe_mode": True,
        "external_ai_call": False,
        "human_approval_required": True,
        "next_phase": "Faz 6 — Iletisim ve destek kayitlarindan kurumsal sinyal analizi",
    }


def build_analytics_center_survey_feedback_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz5_inventory()
    summary = inventory["readiness_summary"]
    return {
        "ok": summary["ok"] is True and inventory["external_ai_call"] is False and inventory["human_approval_required"] is True,
        "phase": inventory["phase"],
        "message": "Anket / geri bildirim / nabiz analiz motoru hazir.",
        "supported_outputs": inventory["supported_outputs"],
        "source_domains": inventory["source_domains"],
        "counts": summary["counts"],
        "next_phase": inventory["next_phase"],
    }


def build_analytics_center_faz6_inventory() -> dict[str, object]:
    from .communication_support_insights import build_communication_support_readiness_summary, build_default_communication_support_insights

    insight_context = build_default_communication_support_insights()
    return {
        "module": "analytics_center",
        "phase": "faz6_communication_support_signal_analysis",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/communication_support_insights.py"],
        "surface_keys": ["communication_support_signal"],
        "supported_outputs": ["message_cards", "support_cards", "priority_signals", "topic_summary"],
        "source_domains": ["communication", "support_center"],
        "insight_context": insight_context,
        "readiness_summary": build_communication_support_readiness_summary(),
        "safe_mode": True,
        "external_ai_call": False,
        "human_approval_required": True,
        "raw_message_dump": False,
        "raw_ticket_body_dump": False,
        "next_phase": "Faz 7 — Analiz Merkezi Excel yukleme ve veri on izleme",
    }


def build_analytics_center_communication_support_summary() -> dict[str, object]:
    inventory = build_analytics_center_faz6_inventory()
    summary = inventory["readiness_summary"]
    return {
        "ok": summary["ok"] is True
        and inventory["external_ai_call"] is False
        and inventory["human_approval_required"] is True
        and inventory["raw_message_dump"] is False
        and inventory["raw_ticket_body_dump"] is False,
        "phase": inventory["phase"],
        "message": "Iletisim ve destek kurumsal sinyal analizi hazir.",
        "supported_outputs": inventory["supported_outputs"],
        "source_domains": inventory["source_domains"],
        "counts": summary["counts"],
        "next_phase": inventory["next_phase"],
    }
