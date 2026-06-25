# BYS360 CIC Context Split V29C
- Generated at: 2026-06-25T20:52:23
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: 6dcc4e6
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/cic_context.py
- Moved function count: 29
- Before target lines: 1370
- After target lines: 1047
- New module lines: 647
- Removed line estimate: 323
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 29 / 29

## Moved Functions
- _cic_auto_last_run_key
- _cic_is_weekend
- _cic_phase3_actor_label
- _cic_phase3_last_result
- _cic_phase3_make_result
- _cic_phase3_public_error
- _cic_phase3_store_result
- _cic_phase3_task_label
- _cic_phase5_actor
- _cic_phase5_now_label
- _cic_phase5_store_audit
- _cic_phase6_bool
- _cic_v40_create_system_notifications
- _cic_v40_date_input
- _cic_v40_days_until
- _cic_v40_run_weekend_celebrations
- _cic_v40_upcoming_special_days
- _cic_v40_upcoming_users
- _cic_v45_bool
- _cic_v45_build_user_indexes
- _cic_v45_ensure_schema
- _cic_v45_existing_user_rows
- _cic_v45_header_key
- _cic_v45_norm
- _cic_v45_norm_name
- _cic_v45_parse_date
- _cic_v45_text
- _cic_weekday_name_tr
- send_task

## Copied Assignments
- BASE_KEY
- TASK_DEFINITIONS
- VERSION
- _CIC_V40_CELEBRATION_TASKS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
