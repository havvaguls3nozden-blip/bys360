# BYS360 CIC Config Context Split V26E
- Generated at: 2026-06-25T20:14:08
- Branch: phase4j-script-reduction-godobject-v1
- HEAD before: 51bfd9e
- Target: app/services/corporate_information_center.py
- New module: app/services/cic/config_context.py
- Moved function count: 14
- Before target lines: 2353
- After target lines: 2184
- New module lines: 375
- Removed line estimate: 169

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

## Copied Assignments
- BASE_KEY
- GROUP_KEY
- TASK_DEFINITIONS
- _CIC_V40_SPECIAL_DAY_DEFAULTS

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: True
- new_module_created: True

## Decision
- 14 fonksiyon app/services/cic/config_context.py modulune alindi.
- corporate_information_center.py dis import uyumlulugu icin facade import ile ayni isimleri sunmaya devam eder.
- Bu uygulama canli sisteme veya veritabanina dokunmaz.
- Sonraki adim compile ve import/smoke dogrulamadir.
