# BYS360 Effective Menu Status After BYS360 Split V35A
- Generated at: 2026-06-25T21:17:02
- Status: READY_FOR_NEXT_PREFLIGHT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: aac342a
- Target: app/services/settings/effective_menu.py
- Lines: 1810
- Top-level functions: 21
- Lines to go under 800: 1011

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29

## Best Next Target
- prefix: _apply
- status: GOOD_NEXT_SPLIT_CANDIDATE
- closure_function_count: 15
- closure_total_lines: 236
- projected_target_lines_after_split: 1574
- outside_calls: []
- used_assignments: ['CORE_MENU_VISIBILITY_POLICY', 'PHASE3_2_PERFORMANCE_MENU_POLICY', 'PHASE3_PERFORMANCE_MENU_POLICY', 'ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS']
- used_classes: []
- suggested_module: app/services/settings/effective_menu_parts/apply_context.py

## Recommended Candidates Top 20
- prefix=_apply | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=15 | closure_lines=236 | projected=1574 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/apply_context.py
- prefix=_phase3 | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=19 | projected=1791 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/phase3_context.py
- prefix=_allowed | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=14 | projected=1796 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/allowed_context.py
- prefix=_role | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=11 | projected=1799 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/role_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
