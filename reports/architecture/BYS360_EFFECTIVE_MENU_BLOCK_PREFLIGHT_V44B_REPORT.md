# BYS360 Effective Menu Block Preflight V44B
- Generated at: 2026-06-26T11:53:03
- Status: READY_FOR_BLOCK_SPLIT
- Ready for split: True
- Runtime OK: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: aefc37e
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/block_context.py
- Target block line: 769
- Target block length: 33
- Projected raw target lines after split: 896
- Projected facade estimate: 904
- Unknown external names: []
- Used imports: ['logging']
- Used assignments: []
- Used top-level functions: []
- Local assignments: ['_BYS360_DAILY_WEATHER_DISALLOWED_ROLES', '_BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES', '_policy', '_target']
- Calls: ['globals', 'isinstance', 'set']
- Attribute calls: ['_policy.get', '_policy.setdefault', '_target.add', 'logging.getLogger']

## Runtime Smoke
- returncode: 0
- import_ok_marker: True
- core_callable: True
- alias_callable: True
- public_callable: True
- build_context_core_callable: True
- v213c_callable: True
- v214_callable: True
- v215_callable: True
- v216_callable: True
- all_has_v213c: True
- all_has_v214: True
- all_has_v215: True
- all_has_v216: True
- combined_contains_build_nameerror: False
- combined_contains_force_failed: False
- combined_contains_traceback: False

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
