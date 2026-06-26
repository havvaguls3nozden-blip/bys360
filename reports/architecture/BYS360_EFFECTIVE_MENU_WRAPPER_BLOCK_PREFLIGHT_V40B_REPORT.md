# BYS360 Effective Menu Wrapper Block Preflight V40B
- Generated at: 2026-06-26T11:14:47
- Status: READY_FOR_WRAPPER_BLOCK_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 2cf4a9d
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/build_wrapper_context.py
- Wrapper try block count: 4
- Target block line: 821
- Target block length: 57
- Projected target lines after split: 969
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Unknown external names: []
- Used imports: ['is_removed_menu_key', 'logging', 'normalize_role_name']
- Used assignments: ['build_menu_visibility_map']
- Used top-level functions: []

## Target Block
- line: 821
- end_line: 877
- length: 57
- nested_functions: ['build_menu_visibility_map']
- local_assignments: ['_BYS360_V213C_CATEGORY_MENU_KEY', '_BYS360_V213C_CATEGORY_ROLES', '_BYS360_V213C_PREVIOUS_BUILD_MENU_VISIBILITY_MAP', '_current', '_is_admin_like', '_policy', '_role', '_target', 'logger', 'visibility']
- preview: try:

## Wrapper Try Blocks
- line=821 | length=57 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:
- line=906 | length=29 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:
- line=938 | length=29 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:
- line=881 | length=22 | nested_functions=['build_menu_visibility_map'] | unknown=[] | preview=try:

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
