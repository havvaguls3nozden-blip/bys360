from __future__ import annotations

from typing import Any

from app.core.datetime_utils import utc_now

from .live_scope import (
    AI_DECISION_PHASES,
    LIVE_AI_DOMAIN_KEYS,
    LIVE_AI_TABLE_NAMES,
    get_live_ai_data_domains,
    get_live_ai_table_contracts,
)
from .logging_bridge import (
    build_ai_feedback_log_payload,
    build_ai_recommendation_payload,
    build_ai_request_log_payload,
    build_ai_safe_log_excerpt,
)
from .redaction_bridge import build_ai_redaction_context, build_default_redaction_rule_payloads
from .security_contract import get_ai_safety_rules
from .summary_cache import (
    build_ai_safe_summary_text,
    build_ai_summary_cache_contract,
    build_ai_summary_cache_lookup,
    build_ai_summary_cache_payload,
)

"""AI Karar Destek servis envanteri."""


def build_ai_decision_faz0_inventory() -> dict[str, Any]:
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz0_inventory_safe_service_skeleton",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "live_ai_tables": list(LIVE_AI_TABLE_NAMES),
        "live_domain_keys": list(LIVE_AI_DOMAIN_KEYS),
        "table_contracts": get_live_ai_table_contracts(),
        "data_domains": get_live_ai_data_domains(),
        "safety_rules": get_ai_safety_rules(),
        "phase_plan": list(AI_DECISION_PHASES),
        "next_phase": "Faz 1 — AI log / request / redaction servis köprüsü",
    }


def build_ai_decision_faz1_inventory() -> dict[str, Any]:
    sample_request_payload = build_ai_request_log_payload(
        module_type="performance",
        feature_type="decision_support",
        target_table="performance_evaluations",
        target_id=1,
        user_id=1,
        request_text={"email": "ornek@kurum.gov.tr", "summary": "kontrollü karar destek"},
        response_text="Güvenli özet hazırlandı.",
        provider_name="internal",
        model_name="configured_model",
        prompt_version="faz1",
        was_masked=True,
    )
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz1_request_log_redaction_bridge",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": [
            "app/services/ai_decision/logging_bridge.py",
            "app/services/ai_decision/redaction_bridge.py",
        ],
        "supported_payloads": [
            "AIRequestLog",
            "AIRecommendation",
            "AIFeedbackLog",
            "AIRedactionRule",
        ],
        "sample_request_payload": sample_request_payload,
        "sample_safe_excerpt": build_ai_safe_log_excerpt(sample_request_payload),
        "sample_recommendation_payload": build_ai_recommendation_payload(
            module_type="performance",
            target_table="performance_evaluations",
            target_id=1,
            recommendation_type="risk_signal",
            title="Yayın öncesi kontrol önerisi",
            body="Bu kayıt insan onayı için karar destek notudur.",
            severity="medium",
        ),
        "sample_feedback_payload": build_ai_feedback_log_payload(ai_request_log_id=1, user_id=1),
        "redaction_context": build_ai_redaction_context([], module_type="performance"),
        "default_redaction_rule_count": len(build_default_redaction_rule_payloads("performance")),
        "safety_rules": get_ai_safety_rules(),
        "next_phase": "Faz 2 — AI özet cache ve güvenli özetleme altyapısı",
    }


def build_ai_decision_faz2_inventory() -> dict[str, Any]:
    sample_source = [
        {"unit": "Örnek Birim", "email": "ornek@kurum.gov.tr", "note": "Risk sinyali insan onayı gerektirir."},
        {"unit": "Örnek Birim", "phone": "+90 555 000 00 00", "note": "Yayın öncesi kontrol önerilir."},
    ]
    cache_payload = build_ai_summary_cache_payload(
        module_type="performance",
        target_table="performance_evaluations",
        target_id=1,
        summary_kind="manager_overview",
        source_data=sample_source,
        prompt_version="faz2",
        visibility_scope="manager",
    )
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz2_summary_cache_safe_summarization",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": [
            "app/services/ai_decision/summary_cache.py",
            "app/services/analytics_center/summary_pipeline.py",
        ],
        "supported_payloads": ["AISummaryCache", "cache_key", "source_hash", "expires_at"],
        "cache_contract": build_ai_summary_cache_contract(),
        "sample_cache_lookup": build_ai_summary_cache_lookup(
            module_type="performance",
            target_table="performance_evaluations",
            target_id=1,
            summary_kind="manager_overview",
            source_data=sample_source,
            prompt_version="faz2",
        ),
        "sample_cache_payload": cache_payload,
        "sample_safe_summary": build_ai_safe_summary_text(sample_source, module_type="performance"),
        "safety_rules": get_ai_safety_rules(),
        "next_phase": "Faz 3 — Karar destek dashboard veri yüzeyi",
    }


def build_ai_decision_readiness_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz0_inventory()
    table_count = len(inventory["live_ai_tables"])
    domain_count = len(inventory["live_domain_keys"])
    safety_count = len(inventory["safety_rules"])
    return {
        "ok": table_count >= 5 and domain_count >= 6 and safety_count >= 5,
        "table_count": table_count,
        "domain_count": domain_count,
        "safety_rule_count": safety_count,
        "message": "AI Karar Destek / Analiz Merkezi Faz 0 envanteri hazır.",
        "next_phase": inventory["next_phase"],
    }


def build_ai_decision_service_bridge_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz1_inventory()
    return {
        "ok": len(inventory["supported_payloads"]) >= 4 and inventory["default_redaction_rule_count"] >= 8,
        "phase": inventory["phase"],
        "supported_payloads": inventory["supported_payloads"],
        "service_bridge_files": inventory["service_bridge_files"],
        "message": "AI log / request / redaction servis köprüsü hazır.",
        "next_phase": inventory["next_phase"],
    }


def build_ai_decision_summary_cache_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz2_inventory()
    cache_contract = inventory["cache_contract"]
    return {
        "ok": cache_contract["table"] == "ai_summary_cache" and len(inventory["supported_payloads"]) >= 4,
        "phase": inventory["phase"],
        "supported_payloads": inventory["supported_payloads"],
        "service_bridge_files": inventory["service_bridge_files"],
        "external_ai_call": False,
        "message": "AI özet cache ve güvenli özetleme altyapısı hazır.",
        "next_phase": inventory["next_phase"],
    }


def build_ai_decision_faz3_inventory() -> dict[str, Any]:
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz3_dashboard_data_surface",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/dashboard_surface.py"],
        "supported_surface_outputs": ["metric_cards", "signal_cards", "source_health_cards"],
        "safety_rules": get_ai_safety_rules(),
        "external_ai_call": False,
        "next_phase": "Faz 4 — Personel / performans içgörü motoru",
    }


def build_ai_decision_dashboard_surface_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz3_inventory()
    return {
        "ok": inventory["external_ai_call"] is False and len(inventory["supported_surface_outputs"]) >= 3,
        "phase": inventory["phase"],
        "supported_surface_outputs": inventory["supported_surface_outputs"],
        "service_bridge_files": inventory["service_bridge_files"],
        "message": "AI Karar Destek dashboard veri yüzeyi hazır.",
        "next_phase": inventory["next_phase"],
    }


def build_ai_decision_faz4_inventory() -> dict[str, Any]:
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz4_personnel_performance_insight_engine",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/personnel_performance_insights.py"],
        "supported_surface_outputs": ["personnel_cards", "performance_cards", "risk_signals", "safe_summary"],
        "source_domains": ["personnel", "performance"],
        "safety_rules": get_ai_safety_rules(),
        "external_ai_call": False,
        "human_approval_required": True,
        "next_phase": "Faz 5 — Anket / geri bildirim / nabiz analiz motoru",
    }


def build_ai_decision_personnel_performance_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz4_inventory()
    return {
        "ok": inventory["external_ai_call"] is False
        and inventory["human_approval_required"] is True
        and len(inventory["supported_surface_outputs"]) >= 4,
        "phase": inventory["phase"],
        "supported_surface_outputs": inventory["supported_surface_outputs"],
        "source_domains": inventory["source_domains"],
        "service_bridge_files": inventory["service_bridge_files"],
        "message": "AI Karar Destek personel / performans icgoru motoru hazir.",
        "next_phase": inventory["next_phase"],
    }


def build_ai_decision_faz5_inventory() -> dict[str, Any]:
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz5_survey_feedback_pulse_analysis_engine",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/survey_feedback_insights.py"],
        "supported_surface_outputs": ["survey_cards", "feedback_cards", "priority_signals", "theme_summary"],
        "source_domains": ["survey_feedback", "feedback_pulse"],
        "safety_rules": get_ai_safety_rules(),
        "external_ai_call": False,
        "human_approval_required": True,
        "raw_answer_dump": False,
        "next_phase": "Faz 6 — Iletisim ve destek kayitlarindan kurumsal sinyal analizi",
    }


def build_ai_decision_survey_feedback_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz5_inventory()
    return {
        "ok": inventory["external_ai_call"] is False and inventory["human_approval_required"] is True and inventory["raw_answer_dump"] is False and len(inventory["supported_surface_outputs"]) >= 4,
        "phase": inventory["phase"],
        "supported_surface_outputs": inventory["supported_surface_outputs"],
        "source_domains": inventory["source_domains"],
        "service_bridge_files": inventory["service_bridge_files"],
        "message": "AI Karar Destek anket / geri bildirim / nabiz analiz motoru hazir.",
        "next_phase": inventory["next_phase"],
    }


def build_ai_decision_faz6_inventory() -> dict[str, Any]:
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz6_communication_support_signal_analysis",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "service_bridge_files": ["app/services/analytics_center/communication_support_insights.py"],
        "supported_surface_outputs": ["message_cards", "support_cards", "priority_signals", "topic_summary"],
        "source_domains": ["communication", "support_center"],
        "safety_rules": get_ai_safety_rules(),
        "external_ai_call": False,
        "human_approval_required": True,
        "raw_message_dump": False,
        "raw_ticket_body_dump": False,
        "personal_content_dump": False,
        "next_phase": "Faz 7 — Analiz Merkezi Excel yukleme ve veri on izleme",
    }


def build_ai_decision_communication_support_summary() -> dict[str, Any]:
    inventory = build_ai_decision_faz6_inventory()
    return {
        "ok": inventory["external_ai_call"] is False
        and inventory["human_approval_required"] is True
        and inventory["raw_message_dump"] is False
        and inventory["raw_ticket_body_dump"] is False
        and inventory["personal_content_dump"] is False
        and len(inventory["supported_surface_outputs"]) >= 4,
        "phase": inventory["phase"],
        "supported_surface_outputs": inventory["supported_surface_outputs"],
        "source_domains": inventory["source_domains"],
        "service_bridge_files": inventory["service_bridge_files"],
        "message": "AI Karar Destek iletisim/destek sinyal analizi hazir.",
        "next_phase": inventory["next_phase"],
    }
