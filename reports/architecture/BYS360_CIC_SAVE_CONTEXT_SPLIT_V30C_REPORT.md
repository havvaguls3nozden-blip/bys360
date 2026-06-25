# BYS360 CIC Save Context Split V30C
- Generated at: 2026-06-25T21:00:46
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: fba1f00
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/save_context.py
- Moved function count: 8
- Before target lines: 1047
- After target lines: 881
- New module lines: 454
- Removed line estimate: 166
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 8 / 8

## Moved Functions
- _save_system_base
- ensure_celebration_schema
- save_celebration_settings
- save_recipients
- save_system
- save_tasks
- save_templates
- set_auto_scheduler_config

## Copied Assignments
- BASE_KEY
- TASK_DEFINITIONS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
