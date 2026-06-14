"""BYS360 AI servis dışa aktarımları.

Güncel canlı omurga; performans, personel/izin, iletişim, anket, geri bildirim,
yardım merkezi, dashboard ve AI yönetişim katmanını esas alır. Eğitim,
Strateji, Belge Deposu ve Portal AI servisleri canlı vitrinde kapalı tutulur.
"""

from .dashboard_panels import (
    build_repository_dashboard_ai_panel,
    build_dashboard_ai_panel,
    build_management_ai_panel,
    build_scorecard_ai_panel,
    build_publish_ai_panel,
    build_periods_ai_panel,
    build_period_form_ai_panel,
    build_task_generation_ai_panel,
    build_task_preflight_ai_panel,
    build_hierarchy_ai_panel,
    build_mail_reminder_ai_panel,
    build_feedback_requests_ai_panel,
    build_feedback_schedule_ai_panel,
    build_feedback_meetings_ai_panel,
    build_personnel_profile_chain_ai_panel,
    build_admin_user_form_ai_panel,
    build_excel_fix_preview_ai_panel,
    build_personnel_list_ai_panel,
    build_admin_users_risk_ai_panel,
    build_import_health_priority_ai_panel,
    build_org_unit_detail_ai_panel,
    build_personnel_density_ai_panel,
    build_import_health_simulation_ai_panel,
    build_hierarchy_tree_ai_panel,
    build_hierarchy_bulk_edit_ai_panel,
    build_hierarchy_assignment_person_ai_panel,
    build_org_units_risk_map_ai_panel,
    build_assignment_recommendation_center_ai_panel,
    build_assignment_delegation_pressure_ai_panel,
    build_hr_leave_ai_panel,
    build_hr_attendance_ai_panel,
    build_message_compose_ai_panel,
    build_message_inbox_ai_panel,
    build_message_thread_ai_panel,
    build_notification_priority_ai_panel,
    build_announcements_ai_panel,
    build_announcement_form_ai_panel,
    build_dashboard_ai_operations_bridge,
)
from .performance import (  # noqa: F401
    build_performance_consistency_response,
    build_performance_summary_response,
)
from .audit import (  # noqa: F401
    cache_summary,
    ensure_recommendation_rows,
    log_ai_feedback,
    log_ai_request,
    mark_recommendation,
    upsert_ai_summary_cache,
)
from .recommendation_actions import (  # noqa: F401
    apply_recommendation,
    bulk_apply_recommendations,
    is_recommendation_supported,
    list_target_recommendation_payloads,
)
from .support import build_support_ticket_triage_response  # noqa: F401
from .hr import build_hr_leave_brief_response  # noqa: F401


def build_dashboard_brief_response(*args, **kwargs):
    """Dashboard AI özetini import anında değil çağrı anında yükler."""
    from .dashboard_runtime import build_dashboard_brief_response as _impl

    return _impl(*args, **kwargs)


def _module_disabled_response(*args, **kwargs):
    module_label = kwargs.get("module_label") or "Canlı kapsam dışı modül"
    return {
        "ok": False,
        "disabled": True,
        "module": module_label,
        "summary": f"{module_label} için AI uçları güncel canlı omurga dışında bırakıldı.",
        "data": {},
    }


def build_education_report_overview_response(*args, **kwargs):
    return _module_disabled_response(module_label="Eğitim")


def build_education_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Eğitim")


def build_education_video_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Eğitim")


def build_album_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Belge / Medya Deposu")


def build_document_classification_response(*args, **kwargs):
    return _module_disabled_response(module_label="Belge / Medya Deposu")


def build_document_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Belge / Medya Deposu")


def build_repository_dashboard_brief_response(*args, **kwargs):
    return _module_disabled_response(module_label="Belge / Medya Deposu")


def build_strategy_action_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Strateji")


def build_strategy_goal_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Strateji")


def build_strategy_meeting_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Strateji")


def build_strategy_plan_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Strateji")


def build_portal_feed_brief_response(*args, **kwargs):
    return _module_disabled_response(module_label="Portal")


def build_portal_post_summary_response(*args, **kwargs):
    return _module_disabled_response(module_label="Portal")


def _generic_ai_panel(*args, **kwargs):
    title = kwargs.get("title") or "AI Karar Destek"
    return {
        "badge": "Yedek panel",
        "title": title,
        "headline": title,
        "summary": "Bu ekran için özel AI paneli henüz tanımlı değil. Güvenli yedek panel gösteriliyor.",
        "status": "info",
        "bullets": [],
        "highlights": [],
        "metrics": [],
        "actions": [],
        "spotlight": [],
        "meta": {
            "fallback": True,
            "auto_write": False,
        },
    }


def __getattr__(name):
    if name.startswith("build_") and name.endswith("_ai_panel"):
        return _generic_ai_panel
    raise AttributeError(f"module 'app.services.ai' has no attribute {name!r}")
