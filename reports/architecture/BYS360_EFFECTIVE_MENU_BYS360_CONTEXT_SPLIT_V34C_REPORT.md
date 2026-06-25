# BYS360 Effective Menu BYS360 Context Split V34C
- Generated at: 2026-06-25T21:15:09
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: 941108b
- Target: app/services/settings/effective_menu.py
- New module: app/services/settings/effective_menu_parts/bys360_context.py
- Moved function count: 29
- Before target lines: 2132
- After target lines: 1810
- New module lines: 517
- Removed line estimate: 322
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 29 / 29
- Unknown external names from preflight: ['UnitMenuProfile']

## Moved Functions
- _bys360_admin_period_reminder_is_admin_v1
- _bys360_admin_period_reminder_norm_v1
- _bys360_apply_general_category_visibility_fix_v1
- _bys360_apply_performance_main_switch
- _bys360_apply_performance_shortcut_gate_v4
- _bys360_exec_item_matches
- _bys360_exec_norm
- _bys360_force_home_menu_visible_v1
- _bys360_general_category_bool_v1
- _bys360_general_category_state_v1
- _bys360_is_exec_summary_menu_key
- _bys360_perf_rm_v8_apply_aliases
- _bys360_perf_rm_v8_apply_main_gate
- _bys360_perf_rm_v8_norm_role
- _bys360_perf_rm_v8_state_for_keys
- _bys360_performance_role_state
- _bys360_person_matrix_can_open_v1
- _bys360_person_matrix_user_is_admin_v1
- _bys360_portal_role_matrix_v2_12_apply
- _bys360_press_news_role
- _bys360_restore_general_section_v4
- _get_unit_name_for_authority
- _load_role_matrix_state
- _load_unit_profile_state
- _load_user_override_state
- _rollback
- _row_map_by_key
- _safe_query_all
- normalize_role_name

## Copied Assignments
- PORTAL_ROLE_MATRIX_V2_12_DEFAULTS
- PORTAL_ROLE_MATRIX_V2_12_KEYS
- _BYS360_EXEC_KNOWN_KEYS
- _BYS360_EXEC_URL_MARKERS
- _BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1
- _BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1
- _BYS360_PERFORMANCE_CHILD_KEYS
- _BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4
- _BYS360_PERFORMANCE_MAIN_KEYS
- _BYS360_PERFORMANCE_MAIN_KEYS_V4
- _BYS360_PERF_RM_V8_ALIAS_GROUPS
- _BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS
- _BYS360_PERF_RM_V8_CHILD_KEYS
- _BYS360_PERF_RM_V8_MAIN_KEYS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
