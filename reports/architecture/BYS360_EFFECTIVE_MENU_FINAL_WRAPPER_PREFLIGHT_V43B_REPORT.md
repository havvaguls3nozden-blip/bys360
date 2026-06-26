# BYS360 Effective Menu Final Wrapper Preflight V43B
- Generated at: 2026-06-26T11:37:37
- Status: READY_FOR_FINAL_WRAPPER_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: d2b85c4
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/build_wrapper_context.py
- Wrapper try block count: 1
- Target block line: 834
- Target block length: 22
- Projected target lines after split: 919
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
- line: 834
- end_line: 855
- length: 22
- nested_functions: ['build_menu_visibility_map']
- local_assignments: ['_BYS360_V214_CATEGORY_SCOPE_KEY', '_BYS360_V214_CATEGORY_SCOPE_ROLES', '_BYS360_V214_PREVIOUS_BUILD_MENU_VISIBILITY_MAP', '_is_admin_like', '_role', 'logger', 'visibility']
- preview: try:

## Wrapper Try Blocks
- line=834 | length=22 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
