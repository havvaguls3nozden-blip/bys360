# BYS360 CIC Send Context Split V28C
- Generated at: 2026-06-25T20:45:17
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: 2543586
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/send_context.py
- Moved function count: 26
- Before target lines: 1761
- After target lines: 1370
- New module lines: 683
- Removed line estimate: 391
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 26 / 26

## Moved Functions
- _cic_v11_bool
- _cic_v11_clean_header
- _cic_v11_get_setting_value
- _cic_v11_mail_settings
- _cic_v11_normalize_email
- _cic_v11_send_email_direct
- _cic_v40_active_staff_candidates
- _cic_v40_anniversary_users
- _cic_v40_birthday_users
- _cic_v40_bool
- _cic_v40_mmdd
- _cic_v40_parse_date
- _cic_v40_service_year
- _cic_v40_setting_bool
- _cic_v40_special_day_users
- _cic_v40_special_days
- _cic_v40_special_days_today
- _cic_v40_today
- _cic_v40_user_date
- _dashboard_counts
- _recipients_for_task
- _recipients_for_task_base
- _render_template_text
- _render_template_text_base
- _send_task_base
- _user_name

## Copied Assignments
- BASE_KEY
- TASK_DEFINITIONS
- _CIC_V40_SPECIAL_DAY_DEFAULTS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
