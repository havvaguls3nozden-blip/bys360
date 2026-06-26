# BYS360 Effective Menu Status After PHASE3 Constants V38A
- Generated at: 2026-06-26T09:11:16
- Status: READY_FOR_CONSTANT_PREFLIGHT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: a4a092c
- Target: app/services/settings/effective_menu.py
- Lines: 1290
- Top-level functions: 6
- Assignments: 7
- Large assignment blocks: 1
- Lines to go under 800: 491

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | assignments=15
- app/services/settings/effective_menu_parts/phase3_constants.py | lines=190 | top_funcs=0 | assignments=7

## Best Next Constant Target
- prefix: ROLE
- status: GOOD_CONSTANT_SPLIT_CANDIDATE
- assignment_count: 1
- total_lines: 25
- projected_target_lines_after_split: 1265
- suggested_module: app/services/settings/effective_menu_parts/role_constants.py
- large_blocks:
  - ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS | line=84 | length=25

## Best Next Function Target
- prefix: build
- status: GOOD_FUNCTION_REVIEW_CANDIDATE
- function_count: 2
- total_lines: 264
- projected_target_lines_after_split: 1026
- suggested_module: app/services/settings/effective_menu_parts/build_context.py

## Recommended Constant Candidates Top 20
- prefix=ROLE | status=GOOD_CONSTANT_SPLIT_CANDIDATE | assignments=1 | lines=25 | large_blocks=1 | projected=1265 | suggested=app/services/settings/effective_menu_parts/role_constants.py

## Recommended Function Candidates Top 20
- prefix=build | status=GOOD_FUNCTION_REVIEW_CANDIDATE | functions=2 | lines=264 | projected=1026 | suggested=app/services/settings/effective_menu_parts/build_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
