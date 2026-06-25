# BYS360 CIC Config Context Split Validation V26F
- Generated at: 2026-06-25T20:15:38
- Status: NEEDS_FIX
- OK: False
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 4688377
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/config_context.py
- Marker present: True
- Facade import present: True
- New module has all moved functions: True
- Target has no local moved function defs: True
- Import smoke new module OK: False
- Import smoke facade OK: False
- Same object count: 0 / 14
- Import smoke error: ModuleNotFoundError("No module named 'app'")

## Moved Functions
- _clean_ids
- _clothing
- _dumps_json
- _ensure_defaults_base
- _format_weather
- _has_settings_table
- _loads_json
- _now
- _tomorrow_note
- _weather
- ensure_defaults
- get_config
- get_setting
- set_setting

## File Sizes
- Target line count: 2184
- Target function count: 93
- New module line count: 375
- New module function count: 14

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
