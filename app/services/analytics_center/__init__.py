from __future__ import annotations

from .live_scope import ANALYTICS_SURFACE_KEYS, ANALYTICS_SURFACES, build_analytics_surface_summary, get_analytics_surfaces
from .service_inventory import (
    build_analytics_center_bridge_summary,
    build_analytics_center_faz0_inventory,
    build_analytics_center_faz1_inventory,
    build_analytics_center_faz2_inventory,
    build_analytics_center_readiness_summary,
    build_analytics_center_summary_cache_summary,
)
from .summary_pipeline import (
    AnalyticsSummarySourceBundle,
    build_analytics_safe_summary_card,
    build_analytics_summary_cache_plan,
    build_analytics_summary_pipeline_summary,
    build_analytics_summary_source_bundle,
    get_analytics_surface,
)

__all__ = [
    "ANALYTICS_SURFACE_KEYS",
    "ANALYTICS_SURFACES",
    "AnalyticsSummarySourceBundle",
    "build_analytics_center_bridge_summary",
    "build_analytics_center_faz0_inventory",
    "build_analytics_center_faz1_inventory",
    "build_analytics_center_faz2_inventory",
    "build_analytics_center_readiness_summary",
    "build_analytics_center_summary_cache_summary",
    "build_analytics_safe_summary_card",
    "build_analytics_summary_cache_plan",
    "build_analytics_summary_pipeline_summary",
    "build_analytics_summary_source_bundle",
    "build_analytics_surface_summary",
    "get_analytics_surface",
    "get_analytics_surfaces",
]

# Faz 3 — Karar Destek Dashboard veri yüzeyi
from .dashboard_surface import (
    DashboardMetricCard,
    DashboardSignalCard,
    build_ai_decision_dashboard_context,
    build_ai_decision_dashboard_readiness_summary,
    build_ai_decision_dashboard_surface,
    build_dashboard_metric_card,
    build_dashboard_signal_card,
    build_dashboard_source_health_cards,
    build_default_dashboard_metrics,
    build_default_dashboard_signals,
    coerce_dashboard_number,
    normalize_dashboard_severity,
    normalize_dashboard_status,
)
from .service_inventory import build_analytics_center_dashboard_surface_summary, build_analytics_center_faz3_inventory

__all__.extend([
    "DashboardMetricCard",
    "DashboardSignalCard",
    "build_ai_decision_dashboard_context",
    "build_ai_decision_dashboard_readiness_summary",
    "build_ai_decision_dashboard_surface",
    "build_analytics_center_dashboard_surface_summary",
    "build_analytics_center_faz3_inventory",
    "build_dashboard_metric_card",
    "build_dashboard_signal_card",
    "build_dashboard_source_health_cards",
    "build_default_dashboard_metrics",
    "build_default_dashboard_signals",
    "coerce_dashboard_number",
    "normalize_dashboard_severity",
    "normalize_dashboard_status",
])

# Faz 4 — Personel / performans içgörü motoru
from .personnel_performance_insights import (
    PerformanceInsightSignal,
    PersonnelInsightCard,
    build_default_personnel_performance_insights,
    build_performance_process_insights,
    build_performance_signal,
    build_personnel_insight_card,
    build_personnel_performance_insight_context,
    build_personnel_performance_readiness_summary,
    build_personnel_performance_risk_signals,
    build_personnel_structure_insights,
    calculate_completion_rate,
    clamp_percentage,
    coerce_insight_number,
    normalize_insight_severity,
    normalize_insight_status,
)
from .service_inventory import build_analytics_center_faz4_inventory, build_analytics_center_personnel_performance_summary

__all__.extend([
    "PerformanceInsightSignal",
    "PersonnelInsightCard",
    "build_analytics_center_faz4_inventory",
    "build_analytics_center_personnel_performance_summary",
    "build_default_personnel_performance_insights",
    "build_performance_process_insights",
    "build_performance_signal",
    "build_personnel_insight_card",
    "build_personnel_performance_insight_context",
    "build_personnel_performance_readiness_summary",
    "build_personnel_performance_risk_signals",
    "build_personnel_structure_insights",
    "calculate_completion_rate",
    "clamp_percentage",
    "coerce_insight_number",
    "normalize_insight_severity",
    "normalize_insight_status",
])

# Faz 5 — Anket / geri bildirim / nabız analiz motoru
from .survey_feedback_insights import (
    SurveyFeedbackMetricCard,
    SurveyFeedbackPrioritySignal,
    build_default_survey_feedback_insights,
    build_feedback_pulse_insights,
    build_survey_feedback_insight_context,
    build_survey_feedback_metric_card,
    build_survey_feedback_priority_signal,
    build_survey_feedback_priority_signals,
    build_survey_feedback_readiness_summary,
    build_survey_feedback_theme_summary,
    build_survey_response_insights,
    calculate_response_rate,
    clamp_feedback_percentage,
    coerce_feedback_number,
    normalize_feedback_priority,
    normalize_feedback_status,
    normalize_sentiment_hint,
)
from .service_inventory import build_analytics_center_faz5_inventory, build_analytics_center_survey_feedback_summary

__all__.extend([
    "SurveyFeedbackMetricCard",
    "SurveyFeedbackPrioritySignal",
    "build_analytics_center_faz5_inventory",
    "build_analytics_center_survey_feedback_summary",
    "build_default_survey_feedback_insights",
    "build_feedback_pulse_insights",
    "build_survey_feedback_insight_context",
    "build_survey_feedback_metric_card",
    "build_survey_feedback_priority_signal",
    "build_survey_feedback_priority_signals",
    "build_survey_feedback_readiness_summary",
    "build_survey_feedback_theme_summary",
    "build_survey_response_insights",
    "calculate_response_rate",
    "clamp_feedback_percentage",
    "coerce_feedback_number",
    "normalize_feedback_priority",
    "normalize_feedback_status",
    "normalize_sentiment_hint",
])

# Faz 6 — İletişim ve destek kayıtlarından kurumsal sinyal analizi
from .communication_support_insights import (
    CommunicationSupportMetricCard,
    CommunicationSupportSignal,
    build_communication_support_insight_context,
    build_communication_support_metric_card,
    build_communication_support_priority_signals,
    build_communication_support_readiness_summary,
    build_communication_support_signal,
    build_communication_support_topic_summary,
    build_default_communication_support_insights,
    build_message_load_insights,
    build_support_ticket_insights,
    calculate_support_resolution_rate,
    clamp_signal_percentage,
    coerce_signal_number,
    normalize_signal_priority,
    normalize_signal_severity,
    normalize_signal_status,
)
from .service_inventory import build_analytics_center_communication_support_summary, build_analytics_center_faz6_inventory

__all__.extend([
    "CommunicationSupportMetricCard",
    "CommunicationSupportSignal",
    "build_analytics_center_communication_support_summary",
    "build_analytics_center_faz6_inventory",
    "build_communication_support_insight_context",
    "build_communication_support_metric_card",
    "build_communication_support_priority_signals",
    "build_communication_support_readiness_summary",
    "build_communication_support_signal",
    "build_communication_support_topic_summary",
    "build_default_communication_support_insights",
    "build_message_load_insights",
    "build_support_ticket_insights",
    "calculate_support_resolution_rate",
    "clamp_signal_percentage",
    "coerce_signal_number",
    "normalize_signal_priority",
    "normalize_signal_severity",
    "normalize_signal_status",
])
