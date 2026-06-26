# BYS360 Effective Menu Status After Build Hotfix V40A
- Generated at: 2026-06-26T11:12:41
- Status: READY_FOR_WRAPPER_BLOCK_REVIEW
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: a22114c
- Target: app/services/settings/effective_menu.py
- Lines: 1026
- Lines to go under 800: 227
- Top-level functions: 5
- All functions: 9
- Top-level blocks: 77
- Large top-level blocks: 1
- Build wrapper blocks: 5
- Duplicate function names: ['build_menu_visibility_map']
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | all_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/build_context.py | lines=305 | top_funcs=1 | all_funcs=1 | assignments=1
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | all_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29 | assignments=15
- app/services/settings/effective_menu_parts/phase3_constants.py | lines=190 | top_funcs=0 | all_funcs=0 | assignments=7
- app/services/settings/effective_menu_parts/role_constants.py | lines=149 | top_funcs=0 | all_funcs=0 | assignments=2

## Best Next Block Target
- kind: Try
- line: 821
- length: 57
- contains build_menu_visibility_map: True
- nested functions: ['build_menu_visibility_map']
- preview: try:

## Large Top-Level Blocks Top 20
- kind=Try | line=821 | length=57 | nested_funcs=1 | contains_build=True | preview=try:

## Build Wrapper Blocks
- kind=Try | line=821 | length=57 | nested_functions=['build_menu_visibility_map']
- kind=Try | line=881 | length=22 | nested_functions=['build_menu_visibility_map']
- kind=Try | line=906 | length=29 | nested_functions=['build_menu_visibility_map']
- kind=Try | line=938 | length=29 | nested_functions=['build_menu_visibility_map']
- kind=FunctionDef | line=1014 | length=12 | nested_functions=['build_menu_visibility_map']

## Recommended Function Candidates Top 20
- prefix=build | status=GOOD_FUNCTION_REVIEW_CANDIDATE | functions=5 | lines=90 | projected=936 | suggested=app/services/settings/effective_menu_parts/build_context.py

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
