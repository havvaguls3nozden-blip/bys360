# BYS360 Effective Menu Status After BYS360 Constants V37A
- Generated at: 2026-06-26T08:59:10
- Status: READY_FOR_CONSTANT_PREFLIGHT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: bb93d09
- Target: app/services/settings/effective_menu.py
- Lines: 1344
- Top-level functions: 6
- Assignments: 13
- Large assignment blocks: 2
- Lines to go under 800: 545

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | assignments=15

## Best Next Constant Target
- prefix: PHASE3
- status: GOOD_CONSTANT_SPLIT_CANDIDATE
- assignment_count: 6
- total_lines: 64
- projected_target_lines_after_split: 1280
- suggested_module: app/services/settings/effective_menu_parts/phase3_constants.py
- large_blocks:
  - PHASE3_2_PERFORMANCE_MENU_POLICY | line=207 | length=36

## Recommended Constant Candidates Top 20
- prefix=PHASE3 | status=GOOD_CONSTANT_SPLIT_CANDIDATE | assignments=6 | lines=64 | large_blocks=1 | projected=1280 | suggested=app/services/settings/effective_menu_parts/phase3_constants.py
- prefix=ROLE | status=GOOD_CONSTANT_SPLIT_CANDIDATE | assignments=1 | lines=25 | large_blocks=1 | projected=1319 | suggested=app/services/settings/effective_menu_parts/role_constants.py

## Recommended Function Candidates Top 20
- prefix=build | status=GOOD_FUNCTION_REVIEW_CANDIDATE | functions=2 | lines=264 | projected=1080 | suggested=app/services/settings/effective_menu_parts/build_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
