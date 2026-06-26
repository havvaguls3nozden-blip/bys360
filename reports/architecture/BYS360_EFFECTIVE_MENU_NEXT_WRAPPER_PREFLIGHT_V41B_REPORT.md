# BYS360 Effective Menu Next Wrapper Preflight V41B
- Generated at: 2026-06-26T11:22:43
- Status: READY_FOR_NEXT_WRAPPER_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 44defe4
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/build_wrapper_context.py
- Wrapper try block count: 3
- Target block line: 859
- Target block length: 29
- Projected target lines after split: 950
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
- line: 859
- end_line: 887
- length: 29
- nested_functions: ['build_menu_visibility_map']
- local_assignments: ['_BYS360_V215_CATEGORY_PERIOD_SCOPE_KEY', '_BYS360_V215_CATEGORY_PERIOD_SCOPE_ROLES', '_BYS360_V215_PREVIOUS_BUILD_MENU_VISIBILITY_MAP', '_is_admin_like', '_removed', '_role', 'logger', 'visibility']
- preview: try:

## Wrapper Try Blocks
- line=859 | length=29 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:
- line=891 | length=29 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:
- line=834 | length=22 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
