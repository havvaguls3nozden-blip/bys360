# BYS360 Effective Menu Build Context Preflight V39B
- Generated at: 2026-06-26T10:23:43
- Status: NEEDS_MANUAL_REVIEW
- Ready for split: False
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: c78db17
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/build_context.py
- Expected function count: 2
- Selected function count: 2
- Selected total lines: 264
- Projected target lines after split: 1006
- Build function names: ['build_menu_visibility_map', 'build_menu_visibility_map']
- Duplicate function names: ['build_menu_visibility_map']
- Build duplicate names: ['build_menu_visibility_map']
- Alias dependency detected: True
- Assignments using build count: 1
- Used imports: ['Any', 'UserMenuPermission', '_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS', '_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES', '_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS', '_apply_bys360_press_news_admin_only_policy', '_apply_bys360_settings_live_authority_v1', '_apply_core_menu_visibility_policy', '_apply_phase3_2_performance_menu_visibility', '_apply_phase3_performance_menu_policy', '_apply_role_gate', '_apply_role_matrix_closed_guard', '_bys360_admin_period_reminder_is_admin_v1', '_bys360_apply_general_category_visibility_fix_v1', '_bys360_apply_performance_main_switch', '_bys360_apply_performance_shortcut_gate_v4', '_bys360_exec_item_matches', '_bys360_exec_norm', '_bys360_force_home_menu_visible_v1', '_bys360_is_exec_summary_menu_key', '_bys360_perf_rm_v8_apply_aliases', '_bys360_perf_rm_v8_apply_main_gate', '_bys360_perf_rm_v8_norm_role', '_bys360_portal_role_matrix_v2_12_apply', '_bys360_restore_general_section_v4', '_load_role_matrix_state', '_load_unit_profile_state', '_load_user_override_state', '_phase3_2_normalize_role_name', '_role_allowed_for_menu', '_rollback', 'build_effective_user_menu_context', 'get_role_default_menu_keys', 'is_removed_menu_key', 'normalize_role_name']
- Used assignments: ['PORTAL_MENU_VISIBILITY_POLICY', '_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1']
- Used other top-level functions: ['_active_menu_items', '_log_warning', '_user_has_any_assigned_survey']
- Self references: []
- Unknown external names: ['exc', 'load_exc']

## Selected Build Functions
- build_menu_visibility_map | line=224 | length=252 | calls=['__import__', '_active_menu_items', '_apply_bys360_press_news_admin_only_policy', '_apply_bys360_settings_live_authority_v1', '_apply_core_menu_visibility_policy', '_apply_phase3_2_performance_menu_visibility', '_apply_phase3_performance_menu_policy', '_apply_role_gate', '_apply_role_matrix_closed_guard', '_bys360_apply_general_category_visibility_fix_v1', '_bys360_apply_performance_main_switch', '_bys360_apply_performance_shortcut_gate_v4', '_bys360_exec_item_matches', '_bys360_exec_norm', '_bys360_force_home_menu_visible_v1', '_bys360_is_exec_summary_menu_key', '_bys360_perf_rm_v8_apply_aliases', '_bys360_perf_rm_v8_apply_main_gate', '_bys360_perf_rm_v8_norm_role', '_bys360_portal_role_matrix_v2_12_apply', '_bys360_restore_general_section_v4', '_load_role_matrix_state', '_load_unit_profile_state', '_load_user_override_state', '_log_warning', '_phase3_2_normalize_role_name', '_role_allowed_for_menu', '_rollback', '_user_has_any_assigned_survey', 'any', 'bool', 'build_effective_user_menu_context', 'get_role_default_menu_keys', 'getattr', 'globals', 'is_removed_menu_key', 'isinstance', 'list', 'normalize_role_name', 'set', 'str']
- build_menu_visibility_map | line=1258 | length=12 | calls=['_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1', '_bys360_admin_period_reminder_is_admin_v1', 'dict']

## Assignments Using build_menu_visibility_map
- line=1254 | length=1 | targets=['_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1'] | loads=['build_menu_visibility_map']

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
