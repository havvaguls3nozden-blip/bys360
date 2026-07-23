from __future__ import annotations

from .live_scope import (
    AI_DECISION_PHASES,
    LIVE_AI_DATA_DOMAINS,
    LIVE_AI_DOMAIN_KEYS,
    LIVE_AI_TABLE_NAMES,
    LIVE_AI_TABLES,
    get_live_ai_data_domains,
    get_live_ai_table_contracts,
)
from .logging_bridge import (
    AI_ALLOWED_REQUEST_STATUSES,
    AI_ALLOWED_SEVERITIES,
    AI_ALLOWED_VISIBILITY_FLAGS,
    build_ai_feedback_log_payload,
    build_ai_recommendation_payload,
    build_ai_request_log_payload,
    build_ai_request_log_record,
    build_ai_request_log_update_payload,
    build_ai_safe_log_excerpt,
    coerce_ai_bool,
    normalize_ai_feature_type,
    normalize_ai_module_type,
    normalize_ai_status,
    truncate_ai_log_text,
)
from .redaction_bridge import (
    DEFAULT_REDACTION_REPLACEMENT,
    RedactionRuleSnapshot,
    apply_ai_redaction_rules,
    build_ai_redaction_context,
    build_ai_redaction_rule_payload,
    build_default_redaction_rule_payloads,
    extract_active_redaction_rules,
    redact_text_for_ai_log,
)
from .security_contract import (
    SAFETY_RULES,
    SENSITIVE_FIELD_NAMES,
    get_ai_safety_rules,
    redact_mapping_for_ai,
    should_redact_field,
)
from .service_inventory import (
    build_ai_decision_faz0_inventory,
    build_ai_decision_faz1_inventory,
    build_ai_decision_faz2_inventory,
    build_ai_decision_readiness_summary,
    build_ai_decision_service_bridge_summary,
    build_ai_decision_summary_cache_summary,
)
from .summary_cache import (
    DEFAULT_PROMPT_VERSION,
    DEFAULT_SUMMARY_KIND,
    AISummaryCacheHit,
    AISummaryCachePayload,
    build_ai_safe_summary_text,
    build_ai_source_hash,
    build_ai_summary_cache_contract,
    build_ai_summary_cache_hit,
    build_ai_summary_cache_key,
    build_ai_summary_cache_lookup,
    build_ai_summary_cache_payload,
    build_ai_summary_cache_record,
    flatten_ai_summary_source_text,
    is_ai_summary_cache_fresh,
    summarize_text_safely,
)

__all__ = [
    "AI_ALLOWED_REQUEST_STATUSES",
    "AI_ALLOWED_SEVERITIES",
    "AI_ALLOWED_VISIBILITY_FLAGS",
    "AI_DECISION_PHASES",
    "AISummaryCacheHit",
    "AISummaryCachePayload",
    "DEFAULT_PROMPT_VERSION",
    "DEFAULT_REDACTION_REPLACEMENT",
    "DEFAULT_SUMMARY_KIND",
    "LIVE_AI_DATA_DOMAINS",
    "LIVE_AI_DOMAIN_KEYS",
    "LIVE_AI_TABLE_NAMES",
    "LIVE_AI_TABLES",
    "RedactionRuleSnapshot",
    "SAFETY_RULES",
    "SENSITIVE_FIELD_NAMES",
    "apply_ai_redaction_rules",
    "build_ai_decision_faz0_inventory",
    "build_ai_decision_faz1_inventory",
    "build_ai_decision_faz2_inventory",
    "build_ai_decision_readiness_summary",
    "build_ai_decision_service_bridge_summary",
    "build_ai_decision_summary_cache_summary",
    "build_ai_feedback_log_payload",
    "build_ai_recommendation_payload",
    "build_ai_redaction_context",
    "build_ai_redaction_rule_payload",
    "build_ai_request_log_payload",
    "build_ai_request_log_record",
    "build_ai_request_log_update_payload",
    "build_ai_safe_log_excerpt",
    "build_ai_safe_summary_text",
    "build_ai_source_hash",
    "build_ai_summary_cache_contract",
    "build_ai_summary_cache_hit",
    "build_ai_summary_cache_key",
    "build_ai_summary_cache_lookup",
    "build_ai_summary_cache_payload",
    "build_ai_summary_cache_record",
    "build_default_redaction_rule_payloads",
    "coerce_ai_bool",
    "extract_active_redaction_rules",
    "flatten_ai_summary_source_text",
    "get_ai_safety_rules",
    "get_live_ai_data_domains",
    "get_live_ai_table_contracts",
    "is_ai_summary_cache_fresh",
    "normalize_ai_feature_type",
    "normalize_ai_module_type",
    "normalize_ai_status",
    "redact_mapping_for_ai",
    "redact_text_for_ai_log",
    "should_redact_field",
    "summarize_text_safely",
    "truncate_ai_log_text",
]

# Faz 3 — Karar Destek Dashboard veri yüzeyi
from .service_inventory import (
    build_ai_decision_dashboard_surface_summary,
    build_ai_decision_faz3_inventory,
)

__all__ += [
    "build_ai_decision_dashboard_surface_summary",
    "build_ai_decision_faz3_inventory",
]

# Faz 4 — Personel / performans içgörü motoru
from .service_inventory import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    build_ai_decision_faz4_inventory,
    build_ai_decision_personnel_performance_summary,
)

__all__ += [
    "build_ai_decision_faz4_inventory",
    "build_ai_decision_personnel_performance_summary",
]

# Faz 5 — Anket / geri bildirim / nabız analiz motoru
from .service_inventory import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    build_ai_decision_faz5_inventory,
    build_ai_decision_survey_feedback_summary,
)

__all__ += [
    "build_ai_decision_faz5_inventory",
    "build_ai_decision_survey_feedback_summary",
]

# Faz 6 — İletişim ve destek kayıtlarından kurumsal sinyal analizi
from .service_inventory import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    build_ai_decision_communication_support_summary,
    build_ai_decision_faz6_inventory,
)

__all__ += [
    "build_ai_decision_communication_support_summary",
    "build_ai_decision_faz6_inventory",
]

# Faz 1 — Karar motoru ve performans entegrasyonu
from .decision_support_engine import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    DecisionPolicy,
    DecisionSupportEngine,
    build_performance_decision_support,
)
from .performance_integration import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    build_ai_decision_faz1_health_payload,
    build_ai_decision_policy_from_settings,
    build_performance_decision_support_response,
)

__all__ += [
    "DecisionPolicy",
    "DecisionSupportEngine",
    "build_ai_decision_faz1_health_payload",
    "build_ai_decision_policy_from_settings",
    "build_performance_decision_support",
    "build_performance_decision_support_response",
]
