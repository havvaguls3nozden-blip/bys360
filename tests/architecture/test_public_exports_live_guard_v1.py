from importlib import import_module

PUBLIC_EXPORTS = {
    "app.services.mail_service": [
        "send_email",
        "send_published_evaluation_notifications",
        "send_feedback_meeting_created_mail",
        "send_feedback_meeting_status_update_mail",
        "send_feedback_request_mail",
        "send_feedback_response_mail",
        "PERFORMANCE_REMINDER_MAIL_TYPE",
        "PERFORMANCE_RESULT_MAIL_TYPE",
        "build_assignment_reminder_email",
        "build_failed_mail_dashboard",
        "build_pending_assignment_manager_dashboard",
        "build_pending_assignment_manager_rows",
        "build_performance_mail_history_rows",
        "build_mail_system_health_snapshot",
        "build_reminder_activity_dashboard",
        "get_failed_performance_mail_logs",
        "get_performance_mail_automation_settings",
        "get_performance_mail_template_rows",
        "retry_failed_performance_mail_logs",
        "retry_mail_log",
        "run_performance_mail_automation",
        "send_test_performance_mail",
        "save_performance_mail_automation_settings",
        "save_performance_mail_templates",
        "send_bulk_assignment_reminders",
        "send_selected_assignment_reminders",
        "send_single_assignment_reminder",
    ],
    "app.api.mobile.shared": [
        "mobile_api_bp",
        "require_mobile_user",
        "jsonify",
        "request",
        "User",
        "_full_name",
        "_has_global_scope",
        "_safe_count",
        "_safe_scalar",
        "_as_int",
        "_item",
        "_metric",
        "_module_payload",
        "_clean_mobile_text",
    ],
    "app.main_handlers.account_settings_helpers": [
        "account",
        "settings_page",
    ],
}


def test_public_exports_live_guard_v1():
    missing = {}

    for module_name, expected_names in PUBLIC_EXPORTS.items():
        module = import_module(module_name)
        absent = [name for name in expected_names if not hasattr(module, name)]
        if absent:
            missing[module_name] = absent

    assert not missing, f"Public exports broken: {missing!r}"
