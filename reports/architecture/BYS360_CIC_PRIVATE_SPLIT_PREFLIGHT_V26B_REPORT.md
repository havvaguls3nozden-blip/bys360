# BYS360 CIC _private Split Preflight V26B
- Generated at: 2026-06-25T20:08:51
- Status: NEEDS_WRAPPER_OR_DEPENDENCY_PLAN
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 7ffba53
- Target: app/services/corporate_information_center.py
- Selected prefix: _private
- Selected function count: 3
- Selected total lines: 38
- Direct move safe: False
- Next action: V26C'de dogrudan tasima yerine once bagimli fonksiyonlar/assignments icin wrapper veya ayni component tasima plani yapilmali.

## Selected Functions

### _now
- line: 159
- end_line: 160
- length: 2
- calls_inside_selected_group: []
- calls_outside_selected_group: []
- uses_imports: ['datetime']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

### _weather
- line: 397
- end_line: 419
- length: 23
- calls_inside_selected_group: ['_clothing']
- calls_outside_selected_group: ['_format_weather', '_tomorrow_note', 'get_config']
- uses_imports: ['json', 'ssl', 'urlopen']
- uses_assignments: []
- uses_classes: []
- unknown_external_names: ['exc']

### _clothing
- line: 436
- end_line: 448
- length: 13
- calls_inside_selected_group: []
- calls_outside_selected_group: []
- uses_imports: []
- uses_assignments: []
- uses_classes: []
- unknown_external_names: []

## Aggregate Dependencies
- outside_calls: ['_format_weather', '_tomorrow_note', 'get_config']
- used_assignments: []
- used_classes: []
- used_imports: ['datetime', 'json', 'ssl', 'urlopen']
- unknown_external_names: ['exc']

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False

## Decision
- Bu rapor kaynak kodu degistirmez.
- _private prefix grubunun dogrudan tasinabilir olup olmadigini inceler.
- outside_calls bos degilse dogrudan tasima yapilmaz.
- direct_move_safe True ise bir sonraki adimda kucuk ve guvenli split uygulanabilir.
