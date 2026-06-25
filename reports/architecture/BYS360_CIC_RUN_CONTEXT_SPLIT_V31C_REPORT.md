# BYS360 CIC Run Context Split V31C
- Generated at: 2026-06-25T21:05:21
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: 9ed8bc0
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/run_context.py
- Moved function count: 2
- Before target lines: 881
- After target lines: 763
- New module lines: 396
- Removed line estimate: 118
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 2 / 2

## Moved Functions
- _run_due_tasks_base
- run_due_tasks

## Copied Assignments
- TASK_DEFINITIONS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
