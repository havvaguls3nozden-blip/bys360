# BYS360 Effective Menu Status After Apply Split V36A
- Generated at: 2026-06-26T08:49:37
- Status: READY_FOR_CONSTANT_PREFLIGHT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 6c64833
- Target: app/services/settings/effective_menu.py
- Lines: 1593
- Top-level functions: 6
- Assignments: 59
- Large assignment blocks: 6
- Lines to go under 800: 794

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | all_funcs=15
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29

## Best Next Constant Target
- prefix: _BYS360
- status: GOOD_CONSTANT_SPLIT_CANDIDATE
- assignment_count: 47
- total_lines: 300
- projected_target_lines_after_split: 1293
- suggested_module: app/services/settings/effective_menu_parts/BYS360_constants.py
- large_blocks:
  - _BYS360_ALL_MENU_ROLE_MATRIX_POLICY | line=837 | length=59
  - _BYS360_PERF_RM_V8_ROLE_POLICY | line=1147 | length=47
  - _BYS360_PERFORMANCE_MAIN_SWITCH_POLICY | line=958 | length=42
  - _BYS360_PERF_RM_V8_ALIAS_GROUPS | line=1101 | length=36

## Best Next Function Target
- none

## Recommended Constant Candidates Top 20
- prefix=_BYS360 | status=GOOD_CONSTANT_SPLIT_CANDIDATE | assignments=47 | lines=300 | large_blocks=4 | projected=1293 | suggested=app/services/settings/effective_menu_parts/BYS360_constants.py
- prefix=PHASE3 | status=GOOD_CONSTANT_SPLIT_CANDIDATE | assignments=6 | lines=64 | large_blocks=1 | projected=1529 | suggested=app/services/settings/effective_menu_parts/PHASE3_constants.py
- prefix=ROLE | status=GOOD_CONSTANT_SPLIT_CANDIDATE | assignments=1 | lines=25 | large_blocks=1 | projected=1568 | suggested=app/services/settings/effective_menu_parts/ROLE_constants.py

## Recommended Function Candidates Top 20

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
