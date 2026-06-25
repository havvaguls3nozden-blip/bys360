# BYS360 CIC Misc Context Split V27C
- Generated at: 2026-06-25T20:36:39
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: f5244fd
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/misc_context.py
- Moved function count: 23
- Before target lines: 2184
- After target lines: 1761
- New module lines: 672
- Removed line estimate: 423
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 23 / 23

## Moved Functions
- _active_staff_users
- _cic_auto_bool
- _cic_phase5_audit_list
- _cic_phase5_last_result
- _cic_phase5_log_metrics
- _cic_phase5_mail_health
- _cic_phase5_readiness
- _cic_phase5_safe_int
- _cic_phase5_task_preview
- _cic_phase6_build
- _cic_phase6_item
- _cic_phase6_log_quality
- _cic_phase6_missing_email_count
- _cic_phase6_status
- _cic_phase6_template_quality
- _context_base
- _users_by_ids
- context
- get_auto_scheduler_config
- get_recent_logs
- get_recipients
- get_template
- list_users

## Copied Assignments
- BASE_KEY
- TASK_DEFINITIONS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
