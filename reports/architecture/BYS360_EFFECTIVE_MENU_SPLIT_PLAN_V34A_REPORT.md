# BYS360 Effective Menu Split Plan V34A
- Generated at: 2026-06-25T21:11:52
- Status: READY_FOR_PREFLIGHT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 0cbc0d6
- Target: app/services/settings/effective_menu.py
- Lines: 2132
- Top-level functions: 50
- Classes: 0

## Best Next Target
- prefix: _bys360
- status: GOOD_NEXT_SPLIT_CANDIDATE
- closure_function_count: 29
- closure_total_lines: 355
- projected_target_lines_after_split: 1777
- outside_calls: []
- used_assignments: ['PORTAL_ROLE_MATRIX_V2_12_DEFAULTS', 'PORTAL_ROLE_MATRIX_V2_12_KEYS', '_BYS360_EXEC_KNOWN_KEYS', '_BYS360_EXEC_URL_MARKERS', '_BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1', '_BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1', '_BYS360_PERFORMANCE_CHILD_KEYS', '_BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4', '_BYS360_PERFORMANCE_MAIN_KEYS', '_BYS360_PERFORMANCE_MAIN_KEYS_V4', '_BYS360_PERF_RM_V8_ALIAS_GROUPS', '_BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS', '_BYS360_PERF_RM_V8_CHILD_KEYS', '_BYS360_PERF_RM_V8_MAIN_KEYS']
- used_classes: []
- suggested_module: app/services/settings/effective_menu_parts/bys360_context.py

## Recommended Candidates Top 20
- prefix=_bys360 | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=29 | closure_lines=355 | projected=1777 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/bys360_context.py
- prefix=_apply | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=26 | closure_lines=328 | projected=1804 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/apply_context.py
- prefix=_load | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=8 | closure_lines=62 | projected=2070 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/load_context.py
- prefix=_get | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=4 | closure_lines=45 | projected=2087 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/get_context.py
- prefix=build | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=3 | closure_lines=44 | projected=2088 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/build_context.py
- prefix=_user | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=38 | projected=2094 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/user_context.py
- prefix=_phase3 | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=3 | closure_lines=21 | projected=2111 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/phase3_context.py
- prefix=_allowed | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=3 | closure_lines=16 | projected=2116 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/allowed_context.py
- prefix=_safe | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=14 | projected=2118 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/safe_context.py
- prefix=_role | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=3 | closure_lines=13 | projected=2119 | outside_calls=0 | suggested=app/services/settings/effective_menu_parts/role_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
