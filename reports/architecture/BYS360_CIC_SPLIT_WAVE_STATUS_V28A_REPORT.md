# BYS360 CIC Split Wave Status V28A
- Generated at: 2026-06-25T20:39:56
- Status: READY_FOR_NEXT_SPLIT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 1515296
- Target lines: 1761
- Target functions: 69

## CIC Modules
- app/services/cic/__init__.py | lines=20 | funcs=0
- app/services/cic/celebration_service.py | lines=55 | funcs=8
- app/services/cic/config_context.py | lines=375 | funcs=14
- app/services/cic/facade.py | lines=120 | funcs=0
- app/services/cic/mail_scheduler_service.py | lines=470 | funcs=23
- app/services/cic/misc_context.py | lines=672 | funcs=24
- app/services/cic/query_service.py | lines=45 | funcs=6
- app/services/cic/repository.py | lines=471 | funcs=60
- app/services/cic/task_contract.py | lines=234 | funcs=5
- app/services/cic/template_service.py | lines=137 | funcs=7

## Best Next Target
- prefix: _send
- status: GOOD_NEXT_SPLIT_CANDIDATE
- closure_function_count: 26
- closure_total_lines: 421
- outside_calls: []
- used_assignments: ['BASE_KEY', 'TASK_DEFINITIONS', '_CIC_V40_SPECIAL_DAY_DEFAULTS']
- suggested_module: app/services/cic/send_context.py

## Recommended Candidates Top 20
- prefix=_send | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=26 | closure_lines=421 | outside_calls=0 | suggested=app/services/cic/send_context.py
- prefix=import | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=10 | closure_lines=224 | outside_calls=0 | suggested=app/services/cic/import_context.py
- prefix=celebration | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=17 | closure_lines=222 | outside_calls=0 | suggested=app/services/cic/celebration_context.py
- prefix=save | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=10 | closure_lines=202 | outside_calls=0 | suggested=app/services/cic/save_context.py
- prefix=_recipients | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=15 | closure_lines=142 | outside_calls=0 | suggested=app/services/cic/recipients_context.py
- prefix=_render | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=12 | closure_lines=129 | outside_calls=0 | suggested=app/services/cic/render_context.py
- prefix=_cic | status=POSSIBLE_BUT_LARGE | closure_funcs=55 | closure_lines=777 | outside_calls=0 | suggested=app/services/cic/cic_context.py
- prefix=run | status=POSSIBLE_BUT_LARGE | closure_funcs=34 | closure_lines=659 | outside_calls=0 | suggested=app/services/cic/run_context.py
- prefix=_run | status=POSSIBLE_BUT_LARGE | closure_funcs=32 | closure_lines=610 | outside_calls=0 | suggested=app/services/cic/run_context.py
- prefix=send | status=POSSIBLE_BUT_LARGE | closure_funcs=28 | closure_lines=494 | outside_calls=0 | suggested=app/services/cic/send_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
