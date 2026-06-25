# BYS360 CIC Weather/_private Closure Preflight V26C
- Generated at: 2026-06-25T20:10:12
- Status: NEEDS_MANUAL_COMPONENT_DESIGN
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 6fdbe3d
- Target: app/services/corporate_information_center.py
- Seed functions: ['_clothing', '_now', '_weather']
- Closure function count: 14
- Closure total lines: 187
- Suggested module: app/services/cic/weather_context.py
- Ready for facade split: False
- Next action: Closure hala dis bagimlilik tasiyor; once used_assignments/classes/outside_calls tasarimi netlestirilmeli.

## Closure Functions

### _clean_ids
- line: 279
- end_line: 289
- length: 11
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: []
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _clothing
- line: 436
- end_line: 448
- length: 13
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: []
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _dumps_json
- line: 209
- end_line: 210
- length: 2
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: ['json']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _ensure_defaults_base
- line: 220
- end_line: 263
- length: 44
- calls_inside_closure: ['_dumps_json', '_loads_json', 'get_setting', 'set_setting']
- calls_outside_closure: []
- uses_imports: ['db']
- uses_assignments: ['BASE_KEY', 'TASK_DEFINITIONS']
- uses_classes: []
- unknown_external_names: []

### _format_weather
- line: 422
- end_line: 433
- length: 12
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: []
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _has_settings_table
- line: 163
- end_line: 169
- length: 7
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: ['db']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: ['sa_inspect']

### _loads_json
- line: 198
- end_line: 206
- length: 9
- calls_inside_closure: ['get_setting']
- calls_outside_closure: []
- uses_imports: ['Any', 'json']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _now
- line: 159
- end_line: 160
- length: 2
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: ['datetime']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _tomorrow_note
- line: 451
- end_line: 454
- length: 4
- calls_inside_closure: []
- calls_outside_closure: []
- uses_imports: []
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _weather
- line: 397
- end_line: 419
- length: 23
- calls_inside_closure: ['_clothing', '_format_weather', '_tomorrow_note', 'get_config']
- calls_outside_closure: []
- uses_imports: ['json', 'ssl', 'urlopen']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: ['exc']

### ensure_defaults
- line: 1686
- end_line: 1712
- length: 27
- calls_inside_closure: ['_dumps_json', '_ensure_defaults_base', 'get_setting', 'set_setting']
- calls_outside_closure: []
- uses_imports: ['db']
- uses_assignments: ['BASE_KEY', '_CIC_V40_SPECIAL_DAY_DEFAULTS']
- uses_classes: []
- unknown_external_names: []

### get_config
- line: 266
- end_line: 276
- length: 11
- calls_inside_closure: ['_clean_ids', '_loads_json', 'ensure_defaults', 'get_setting']
- calls_outside_closure: []
- uses_imports: ['Any']
- uses_assignments: ['BASE_KEY']
- uses_classes: []
- unknown_external_names: []

### get_setting
- line: 172
- end_line: 178
- length: 7
- calls_inside_closure: ['_has_settings_table']
- calls_outside_closure: []
- uses_imports: ['SystemSetting']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### set_setting
- line: 181
- end_line: 195
- length: 15
- calls_inside_closure: ['_has_settings_table']
- calls_outside_closure: []
- uses_imports: ['SystemSetting', 'db']
- uses_assignments: ['GROUP_KEY']
- uses_classes: []
- unknown_external_names: []

## Aggregate Dependencies
- outside_calls: []
- used_imports: ['Any', 'SystemSetting', 'datetime', 'db', 'json', 'ssl', 'urlopen']
- used_assignments: ['BASE_KEY', 'GROUP_KEY', 'TASK_DEFINITIONS', '_CIC_V40_SPECIAL_DAY_DEFAULTS']
- used_classes: []
- unknown_external_names: ['exc', 'sa_inspect']

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False

## Decision
- Bu rapor kaynak kodu degistirmez.
- Seed _private fonksiyonlarinin top-level call closure'i hesaplandi.
- outside_calls bos ise closure kendi icinde kapali demektir.
- ready_for_facade_split True ise bir sonraki adimda kucuk facade-preserving split uygulanabilir.
