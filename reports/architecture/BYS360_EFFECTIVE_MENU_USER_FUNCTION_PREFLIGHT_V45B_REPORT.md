# BYS360 Effective Menu User Function Preflight V45B
- Generated at: 2026-06-26T12:25:41
- Status: NEEDS_MANUAL_REVIEW
- Ready for split: False
- Runtime OK: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 0e11ef8
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/user_context.py
- Target function: _user_has_any_assigned_survey
- Function line: 124
- Function length: 30
- Projected raw target lines after split: 871
- Projected import estimate: 875
- Unknown external names: ['Survey', 'user_matches_assignment']
- Used imports: ['_rollback']
- Used assignments: []
- Used top-level functions: []
- Local assignments: ['assignments', 'logger', 'rows', 'surveys']
- Calls: ['__import__', '_rollback', 'any', 'getattr', 'user_matches_assignment']
- Attribute calls: ['Survey.id.desc', 'Survey.query.filter', 'assignments.all', 'logger.exception']

## Runtime Smoke
- returncode: 0
- import_ok_marker: True
- core_callable: True
- alias_callable: True
- public_callable: True
- user_func_callable: True
- build_context_core_callable: True
- apply_block_callable: True
- block_all_has_apply_block: True
- v213c_callable: True
- v214_callable: True
- v215_callable: True
- v216_callable: True
- all_has_v213c: True
- all_has_v214: True
- all_has_v215: True
- all_has_v216: True
- combined_contains_build_nameerror: False
- combined_contains_force_failed: False
- combined_contains_traceback: False

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
