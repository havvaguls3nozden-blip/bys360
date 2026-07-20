
"""Public facade for the staged Corporate Information Center split.

Use this module for new internal calls while old imports continue to work.
"""
from __future__ import annotations

from .access_policy import can_manage as can_manage
from .celebration_dates import _cic_v40_bool as _cic_v40_bool
from .celebration_dates import _cic_v40_days_until as _cic_v40_days_until
from .celebration_dates import _cic_v40_mmdd as _cic_v40_mmdd
from .celebration_dates import _cic_v40_parse_date as _cic_v40_parse_date
from .celebration_dates import _cic_v40_setting_bool as _cic_v40_setting_bool
from .celebration_dates import _cic_v40_special_days as _cic_v40_special_days
from .celebration_dates import _cic_v40_special_days_today as _cic_v40_special_days_today
from .celebration_dates import _cic_v40_today as _cic_v40_today
from .celebration_dates import _cic_v40_user_date as _cic_v40_user_date
from .celebration_service import _cic_v40_anniversary_users as _cic_v40_anniversary_users
from .celebration_service import _cic_v40_birthday_users as _cic_v40_birthday_users
from .celebration_service import (
    _cic_v40_run_weekend_celebrations as _cic_v40_run_weekend_celebrations,
)
from .celebration_service import _cic_v40_service_year as _cic_v40_service_year
from .celebration_service import celebration_context as celebration_context
from .celebration_service import ensure_celebration_schema as ensure_celebration_schema
from .celebration_service import (
    import_celebration_dates_from_excel as import_celebration_dates_from_excel,
)
from .celebration_service import save_celebration_settings as save_celebration_settings
from .cic_context import _cic_auto_last_run_key as _cic_auto_last_run_key
from .cic_context import _cic_is_weekend as _cic_is_weekend
from .cic_context import _cic_phase3_actor_label as _cic_phase3_actor_label
from .cic_context import _cic_phase3_last_result as _cic_phase3_last_result
from .cic_context import _cic_phase3_make_result as _cic_phase3_make_result
from .cic_context import _cic_phase3_public_error as _cic_phase3_public_error
from .cic_context import _cic_phase3_store_result as _cic_phase3_store_result
from .cic_context import _cic_phase3_task_label as _cic_phase3_task_label
from .cic_context import _cic_phase5_actor as _cic_phase5_actor
from .cic_context import _cic_phase5_now_label as _cic_phase5_now_label
from .cic_context import _cic_phase5_store_audit as _cic_phase5_store_audit
from .cic_context import _cic_phase6_bool as _cic_phase6_bool
from .cic_context import (
    _cic_v40_create_system_notifications as _cic_v40_create_system_notifications,
)
from .cic_context import _cic_v40_date_input as _cic_v40_date_input
from .cic_context import _cic_v40_upcoming_special_days as _cic_v40_upcoming_special_days
from .cic_context import _cic_v45_bool as _cic_v45_bool
from .cic_context import _cic_v45_build_user_indexes as _cic_v45_build_user_indexes
from .cic_context import _cic_v45_ensure_schema as _cic_v45_ensure_schema
from .cic_context import _cic_v45_existing_user_rows as _cic_v45_existing_user_rows
from .cic_context import _cic_v45_header_key as _cic_v45_header_key
from .cic_context import _cic_v45_norm as _cic_v45_norm
from .cic_context import _cic_v45_norm_name as _cic_v45_norm_name
from .cic_context import _cic_v45_parse_date as _cic_v45_parse_date
from .cic_context import _cic_v45_text as _cic_v45_text
from .cic_context import _cic_weekday_name_tr as _cic_weekday_name_tr
from .config_context import _clean_ids as _clean_ids
from .config_context import _clothing as _clothing
from .config_context import _dumps_json as _dumps_json
from .config_context import _format_weather as _format_weather
from .config_context import _has_settings_table as _has_settings_table
from .config_context import _loads_json as _loads_json
from .config_context import _now as _now
from .config_context import _tomorrow_note as _tomorrow_note
from .config_context import _weather as _weather
from .config_context import ensure_defaults as ensure_defaults
from .config_context import get_config as get_config
from .config_context import get_setting as get_setting
from .config_context import set_setting as set_setting
from .mail_service import _cic_phase5_mail_health as _cic_phase5_mail_health
from .mail_service import _cic_phase6_missing_email_count as _cic_phase6_missing_email_count
from .mail_service import _cic_v11_bool as _cic_v11_bool
from .mail_service import _cic_v11_clean_header as _cic_v11_clean_header
from .mail_service import _cic_v11_get_setting_value as _cic_v11_get_setting_value
from .mail_service import _cic_v11_mail_settings as _cic_v11_mail_settings
from .mail_service import _cic_v11_normalize_email as _cic_v11_normalize_email
from .mail_service import _cic_v11_send_email_direct as _cic_v11_send_email_direct
from .mail_service import _recipients_for_task as _recipients_for_task
from .mail_service import get_recipients as get_recipients
from .mail_service import send_task as send_task
from .misc_context import _cic_auto_bool as _cic_auto_bool
from .misc_context import _cic_phase5_audit_list as _cic_phase5_audit_list
from .misc_context import _cic_phase5_last_result as _cic_phase5_last_result
from .misc_context import _cic_phase5_log_metrics as _cic_phase5_log_metrics
from .misc_context import _cic_phase5_readiness as _cic_phase5_readiness
from .misc_context import _cic_phase5_safe_int as _cic_phase5_safe_int
from .misc_context import _cic_phase5_task_preview as _cic_phase5_task_preview
from .misc_context import _cic_phase6_build as _cic_phase6_build
from .misc_context import _cic_phase6_log_quality as _cic_phase6_log_quality
from .misc_context import context as context
from .misc_context import get_recent_logs as get_recent_logs
from .query_service import _active_staff_users as _active_staff_users
from .query_service import _cic_v40_active_staff_candidates as _cic_v40_active_staff_candidates
from .query_service import _cic_v40_special_day_users as _cic_v40_special_day_users
from .query_service import _cic_v40_upcoming_users as _cic_v40_upcoming_users
from .query_service import _users_by_ids as _users_by_ids
from .query_service import list_users as list_users
from .save_context import save_recipients as save_recipients
from .save_context import save_system as save_system
from .save_context import save_tasks as save_tasks
from .scheduler_service import get_auto_scheduler_config as get_auto_scheduler_config
from .scheduler_service import run_due_tasks as run_due_tasks
from .scheduler_service import set_auto_scheduler_config as set_auto_scheduler_config
from .task_contract import BASE_KEY as BASE_KEY
from .task_contract import TASK_DEFINITIONS as TASK_DEFINITIONS
from .template_service import _cic_phase6_item as _cic_phase6_item
from .template_service import _cic_phase6_status as _cic_phase6_status
from .template_service import _cic_phase6_template_quality as _cic_phase6_template_quality
from .template_service import _dashboard_counts as _dashboard_counts
from .template_service import _render_template_text as _render_template_text
from .template_service import _user_name as _user_name
from .template_service import get_template as get_template
from .template_service import save_templates as save_templates

__all__ = [
    "BASE_KEY",
    "TASK_DEFINITIONS",
    "_active_staff_users",
    "_cic_auto_bool",
    "_cic_auto_last_run_key",
    "_cic_is_weekend",
    "_cic_phase3_actor_label",
    "_cic_phase3_last_result",
    "_cic_phase3_make_result",
    "_cic_phase3_public_error",
    "_cic_phase3_store_result",
    "_cic_phase3_task_label",
    "_cic_phase5_actor",
    "_cic_phase5_audit_list",
    "_cic_phase5_last_result",
    "_cic_phase5_log_metrics",
    "_cic_phase5_mail_health",
    "_cic_phase5_now_label",
    "_cic_phase5_readiness",
    "_cic_phase5_safe_int",
    "_cic_phase5_store_audit",
    "_cic_phase5_task_preview",
    "_cic_phase6_bool",
    "_cic_phase6_build",
    "_cic_phase6_item",
    "_cic_phase6_log_quality",
    "_cic_phase6_missing_email_count",
    "_cic_phase6_status",
    "_cic_phase6_template_quality",
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v11_get_setting_value",
    "_cic_v11_mail_settings",
    "_cic_v11_normalize_email",
    "_cic_v11_send_email_direct",
    "_cic_v40_active_staff_candidates",
    "_cic_v40_anniversary_users",
    "_cic_v40_birthday_users",
    "_cic_v40_bool",
    "_cic_v40_create_system_notifications",
    "_cic_v40_date_input",
    "_cic_v40_days_until",
    "_cic_v40_mmdd",
    "_cic_v40_parse_date",
    "_cic_v40_run_weekend_celebrations",
    "_cic_v40_service_year",
    "_cic_v40_setting_bool",
    "_cic_v40_special_day_users",
    "_cic_v40_special_days",
    "_cic_v40_special_days_today",
    "_cic_v40_today",
    "_cic_v40_upcoming_special_days",
    "_cic_v40_upcoming_users",
    "_cic_v40_user_date",
    "_cic_v45_bool",
    "_cic_v45_build_user_indexes",
    "_cic_v45_ensure_schema",
    "_cic_v45_existing_user_rows",
    "_cic_v45_header_key",
    "_cic_v45_norm",
    "_cic_v45_norm_name",
    "_cic_v45_parse_date",
    "_cic_v45_text",
    "_cic_weekday_name_tr",
    "_clean_ids",
    "_clothing",
    "_dashboard_counts",
    "_dumps_json",
    "_format_weather",
    "_has_settings_table",
    "_loads_json",
    "_now",
    "_recipients_for_task",
    "_render_template_text",
    "_tomorrow_note",
    "_user_name",
    "_users_by_ids",
    "_weather",
    "can_manage",
    "celebration_context",
    "context",
    "ensure_celebration_schema",
    "ensure_defaults",
    "get_auto_scheduler_config",
    "get_config",
    "get_recent_logs",
    "get_recipients",
    "get_setting",
    "get_template",
    "import_celebration_dates_from_excel",
    "list_users",
    "run_due_tasks",
    "save_celebration_settings",
    "save_recipients",
    "save_system",
    "save_tasks",
    "save_templates",
    "send_task",
    "set_auto_scheduler_config",
    "set_setting",
]
