# BYS360 Effective Menu Next Wrapper Preflight V42B
- Generated at: 2026-06-26T11:28:25
- Status: READY_FOR_NEXT_WRAPPER_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 8b54da5
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/build_wrapper_context.py
- Wrapper try block count: 2
- Target block line: 872
- Target block length: 29
- Projected target lines after split: 931
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Traceback seen: False
- Unknown external names: []
- Used imports: ['is_removed_menu_key', 'logging', 'normalize_role_name']
- Used assignments: ['build_menu_visibility_map']
- Used top-level functions: []

## Target Block
- line: 872
- end_line: 900
- length: 29
- nested_functions: ['build_menu_visibility_map']
- local_assignments: ['_BYS360_V216_CATEGORY_PERIOD_INTEGRATION_KEY', '_BYS360_V216_CATEGORY_PERIOD_INTEGRATION_ROLES', '_BYS360_V216_PREVIOUS_BUILD_MENU_VISIBILITY_MAP', '_is_admin_like', '_removed', '_role', 'logger', 'visibility']
- preview: try:

## Wrapper Try Blocks
- line=872 | length=29 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:
- line=834 | length=22 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
