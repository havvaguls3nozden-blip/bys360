# BYS360 Effective Menu Apply Context Split V35C
- Generated at: 2026-06-26T08:47:08
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: 250bcb3
- Target: app/services/settings/effective_menu.py
- New module: app/services/settings/effective_menu_parts/apply_context.py
- Moved function count: 15
- Before target lines: 1810
- After target lines: 1593
- New module lines: 415
- Removed line estimate: 217
- Runtime new module import OK: True
- Runtime facade import OK: True
- Same object count: 15 / 15
- Unknown external names from preflight: []

## Moved Functions
- _allowed_by_static_gate
- _apply_bys360_press_news_admin_only_policy
- _apply_bys360_settings_live_authority_v1
- _apply_core_menu_visibility_policy
- _apply_phase3_2_performance_menu_visibility
- _apply_phase3_performance_menu_policy
- _apply_role_gate
- _apply_role_matrix_closed_guard
- _get_role_matrix_closed_keys_for_role
- _menu_item_by_key
- _phase3_2_ascii_tr
- _phase3_2_normalize_role_name
- _role_allowed_for_menu
- _role_matrix_runtime_closed
- _settings_explicitly_controls_key

## Copied Assignments
- CORE_MENU_VISIBILITY_POLICY
- PHASE3_2_PERFORMANCE_MENU_POLICY
- PHASE3_PERFORMANCE_MENU_POLICY
- ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True
