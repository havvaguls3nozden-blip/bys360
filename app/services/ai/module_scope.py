
"""BYS360 AI canlı kapsam sözlüğü.

AI Karar Destek Merkezi, canlıda kalan omurgayı tek kaynaktan okur. Bu dosya
eski fazlardan kalan Eğitim / Strateji / Belge Deposu / Portal izlerinin AI
vitrinine ve operasyon raporlarına karışmasını engeller.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlalchemy import func

LIVE_AI_MODULES: tuple[str, ...] = (
    "dashboard",
    "performance",
    "hr",
    "communication",
    "survey",
    "feedback",
    "support",
    "analysis_center",
    "governance",
)

REMOVED_AI_MODULES: tuple[str, ...] = (
    "education",
    "strategy",
    "repository",
    "portal",
)

SYSTEM_AI_MODULES: tuple[str, ...] = (
    "ai",
    "general",
    "governance",
    "analysis_center",
)

MODULE_ALIASES: dict[str, str] = {
    "hr_management": "hr",
    "personnel": "hr",
    "personel": "hr",
    "leave": "hr",
    "attendance": "hr",
    "izin": "hr",
    "vekalet": "hr",
    "messaging": "communication",
    "messages": "communication",
    "message": "communication",
    "notifications": "communication",
    "announcements": "communication",
    "announcement": "communication",
    "surveys": "survey",
    "anket": "survey",
    "pulse": "feedback",
    "feedback_pulse": "feedback",
    "feedback_campaign": "feedback",
    "ai_center": "analysis_center",
    "analysis": "analysis_center",
    "analytics": "analysis_center",
    "decision_support": "analysis_center",
}

AI_MODULE_LABELS: dict[str, str] = {
    "dashboard": "Genel Dashboard",
    "performance": "Performans Yönetimi",
    "hr": "Personel / İzin–Vekâlet",
    "communication": "İletişim ve Duyurular",
    "survey": "Anket Yönetimi",
    "feedback": "Geri Bildirim / Nabız",
    "support": "Yardım Merkezi / Destek",
    "analysis_center": "AI Karar Destek Merkezi",
    "governance": "AI Yönetişim",
    "ai": "AI Sistem Katmanı",
    "general": "Genel",
    "education": "Eğitim",
    "strategy": "Strateji",
    "repository": "Belge ve Medya Deposu",
    "portal": "İç Portal",
}

AI_MODULE_FOCUS: dict[str, str] = {
    "dashboard": "dashboard_brief, yönetici özeti, operasyon sinyali",
    "performance": "performans özeti, tutarlılık kontrolü, yayın öncesi risk",
    "hr": "izin–vekâlet özeti, devamsızlık sinyali, görev aktarımı",
    "communication": "mesaj önceliği, duyuru görünürlüğü, bildirim sınıflama",
    "survey": "anket yanıt özeti, katılım görünümü, soru bazlı sinyal",
    "feedback": "nabız analizi, geri bildirim yoğunluğu, aksiyon planı takibi",
    "support": "destek talebi triage, önceliklendirme, yanıt hazırlığı",
    "analysis_center": "log, öneri, maskeleme, özet cache ve güvenli raporlama",
    "governance": "görünürlük kapısı, kalite eşiği, insan onayı",
    "ai": "AI sistem günlükleri ve karar destek izleri",
    "general": "genel karar destek istekleri",
}

AI_MODULE_TABLES: dict[str, tuple[str, ...]] = {
    "dashboard": ("notifications", "mail_logs", "audit_logs"),
    "performance": (
        "performance_criteria",
        "performance_periods",
        "performance_weight_configs",
        "evaluation_assignments",
        "performance_evaluations",
        "performance_evaluation_items",
        "performance_result_snapshots",
        "assignment_audit_logs",
        "assignment_coverage_logs",
        "evaluation_publish_logs",
        "performance_publish_logs",
    ),
    "hr": (
        "users",
        "organization_units",
        "organization_unit_versions",
        "employee_org_assignment_history",
        "attendance_events",
        "attendance_exceptions",
        "leave_policies",
        "leave_balances",
        "leave_records",
        "leave_requests",
        "personnel_leaves",
        "delegation_assignments",
    ),
    "communication": (
        "messages",
        "message_threads",
        "message_thread_participants",
        "message_attachments",
        "message_reactions",
        "message_typing_states",
    ),
    "survey": (
        "surveys",
        "survey_questions",
        "survey_question_options",
        "survey_assignments",
        "survey_responses",
        "survey_answers",
    ),
    "feedback": (
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
    ),
    "support": (
        "support_categories",
        "support_tickets",
        "support_ticket_messages",
        "support_ticket_attachments",
        "support_ticket_status_history",
        "support_feedback_ratings",
    ),
    "analysis_center": (
        "ai_feedback_logs",
        "ai_recommendations",
        "ai_redaction_rules",
        "ai_request_logs",
        "ai_summary_cache",
    ),
    "governance": (
        "ai_feedback_logs",
        "ai_recommendations",
        "ai_redaction_rules",
        "ai_request_logs",
        "ai_summary_cache",
        "audit_logs",
        "settings_change_logs",
    ),
}


def normalize_ai_module(value: Any) -> str:
    key = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in key:
        key = key.replace("__", "_")
    return MODULE_ALIASES.get(key, key)


def is_removed_ai_module(value: Any) -> bool:
    return normalize_ai_module(value) in set(REMOVED_AI_MODULES)


def is_live_ai_module(value: Any) -> bool:
    key = normalize_ai_module(value)
    if not key:
        return False
    return key in set(LIVE_AI_MODULES) or key in set(SYSTEM_AI_MODULES)


def live_ai_modules(*, include_system: bool = True) -> tuple[str, ...]:
    modules = list(LIVE_AI_MODULES)
    if include_system:
        for module in SYSTEM_AI_MODULES:
            if module not in modules:
                modules.append(module)
    return tuple(modules)


def hidden_ai_modules() -> tuple[str, ...]:
    return REMOVED_AI_MODULES


def ai_module_label(value: Any) -> str:
    key = normalize_ai_module(value)
    if not key:
        return "Genel"
    return AI_MODULE_LABELS.get(key, str(value or key).replace("_", " ").title())


def ai_module_focus(value: Any) -> str:
    key = normalize_ai_module(value)
    return AI_MODULE_FOCUS.get(key, "AI istek akışı")


def ai_module_tables(value: Any) -> tuple[str, ...]:
    return AI_MODULE_TABLES.get(normalize_ai_module(value), ())


def is_visible_ai_module(module_type: Any) -> bool:
    return is_live_ai_module(module_type)


def filter_visible_values(values: Iterable[Any], *, include_defaults: bool = True) -> list[str]:
    rows: list[str] = []
    seen: set[str] = set()
    source: list[Any] = []
    if include_defaults:
        source.extend(live_ai_modules(include_system=True))
    source.extend(list(values or []))
    for value in source:
        key = normalize_ai_module(value)
        if not key or key in seen or not is_visible_ai_module(key):
            continue
        seen.add(key)
        rows.append(key)
    return rows


def scope_visible_modules(query, column):
    live_modules = list(live_ai_modules(include_system=True))
    return query.filter(func.lower(func.coalesce(column, "")).in_(live_modules))


def visible_module_options(values: Iterable[Any] = ()) -> list[str]:
    return filter_visible_values(values, include_defaults=True)
