"""BYS360 Claude Faz 7 final canlı kalite sözleşmeleri.

Bu modül runtime davranışını değiştirmez. Amaç, canlıya kalan omurganın ve
Claude Faz 1-6 refactor/guard zincirinin tek yerde izlenebilmesini sağlamaktır.
"""
from __future__ import annotations


from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class GateScript:
    """Önceki Claude fazlarının beklenen kalite kapısı."""

    phase: str
    path: str
    required: bool = True


LIVE_MODULE_FAMILIES: Final[tuple[str, ...]] = (
    "kimlik_kullanici_yetki_ayarlar",
    "genel_bildirim_mail_destek",
    "personel_izin_vekalet",
    "performans_yonetimi",
    "iletisim_ve_anket",
    "geri_bildirim_nabiz",
    "ai_karar_destek",
)

LIVE_CORE_TABLES: Final[tuple[str, ...]] = (
    "alembic_version",
    "users",
    "organization_units",
    "organization_unit_versions",
    "employee_org_assignment_history",
    "user_menu_permissions",
    "role_menu_defaults",
    "unit_menu_profiles",
    "system_settings",
    "module_settings",
    "settings_change_logs",
    "audit_logs",
    "notifications",
    "mail_logs",
    "support_categories",
    "support_tickets",
    "support_ticket_messages",
    "support_ticket_attachments",
    "support_ticket_status_history",
    "support_feedback_ratings",
    "attendance_events",
    "attendance_exceptions",
    "leave_policies",
    "leave_balances",
    "leave_records",
    "leave_requests",
    "personnel_leaves",
    "delegation_assignments",
    "performance_criteria",
    "performance_periods",
    "performance_weight_configs",
    "evaluation_assignments",
    "performance_evaluations",
    "performance_evaluation_items",
    "performance_evaluation_history",
    "performance_import_batches",
    "performance_import_batch_rows",
    "assignment_audit_logs",
    "assignment_coverage_logs",
    "evaluation_publish_logs",
    "performance_publish_logs",
    "performance_result_snapshots",
    "feedback_requests",
    "feedback_meetings",
    "feedback_action_plans",
    "feedback_answers",
    "feedback_campaign_assignments",
    "feedback_campaigns",
    "feedback_pulse_entries",
    "feedback_question_options",
    "feedback_questions",
    "feedback_submissions",
    "messages",
    "message_threads",
    "message_thread_participants",
    "message_attachments",
    "message_reactions",
    "message_typing_states",
    "surveys",
    "survey_questions",
    "survey_question_options",
    "survey_assignments",
    "survey_responses",
    "survey_answers",
    "ai_feedback_logs",
    "ai_recommendations",
    "ai_redaction_rules",
    "ai_request_logs",
    "ai_summary_cache",
)

FINAL_GATE_REQUIRED_PATHS: Final[tuple[str, ...]] = (
    # Faz 2 app factory ayrıştırması
    "app/error_handlers.py",
    "app/template_safety.py",
    "app/blueprint_registry.py",
    "app/startup_checks.py",
    "app/security/startup_audit.py",
    # Faz 3 settings ayrıştırması
    "app/services/settings/catalog.py",
    # Faz 4 performans amir kural kilidi
    "app/services/performance/manager_rule_constitution.py",
    "app/services/performance/manager_rule_guard.py",
    # Faz 6 sorgu sağlığı
    "app/services/query_health/index_contracts.py",
    "app/services/query_health/static_query_guard.py",
)

PREVIOUS_CLAUDE_GATES: Final[tuple[GateScript, ...]] = (
    GateScript("Faz 1", "scripts/quality/check_claude_review_gate.py"),
    GateScript("Faz 2.5", "scripts/quality/check_app_factory_phase2_5_final_gate.py"),
    GateScript("Faz 3", "scripts/quality/check_settings_service_phase3_gate.py"),
    GateScript("Faz 4", "scripts/quality/check_performance_manager_rules_phase4_gate.py"),
    GateScript("Faz 5", "scripts/quality/check_critical_services_phase5_gate.py"),
    GateScript("Faz 6", "scripts/quality/check_sql_performance_phase6_gate.py"),
)

SECURITY_ALIGNMENT_NOTES: Final[tuple[str, ...]] = (
    "KVKK uyumlu veri minimizasyonu ve denetim izi korunmalı.",
    "AI karar destek, insan onayı yerine geçmeyecek kontrollü öneri katmanı olarak kalmalı.",
    "ISO 27001/TS 27001 çizgisinde erişim, kayıt ve değişiklik izleri korunmalı.",
    "ISO 42001 yaklaşımına uygun AI işlem logları ve redaksiyon kuralları korunmalı.",
)
