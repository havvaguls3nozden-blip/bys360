# BYS360 CIC Status After CIC Context Split V30A
- Generated at: 2026-06-25T20:54:26
- Status: READY_FOR_NEXT_SPLIT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 9a3730a
- Target lines: 1047
- Target functions: 14
- Still god-object candidate: True
- Lines to go under 800: 248

## CIC Modules
- app/services/cic/__init__.py | lines=20 | funcs=0
- app/services/cic/celebration_service.py | lines=55 | funcs=8
- app/services/cic/cic_context.py | lines=647 | funcs=29
- app/services/cic/config_context.py | lines=375 | funcs=14
- app/services/cic/facade.py | lines=120 | funcs=0
- app/services/cic/mail_scheduler_service.py | lines=470 | funcs=23
- app/services/cic/misc_context.py | lines=672 | funcs=24
- app/services/cic/query_service.py | lines=45 | funcs=6
- app/services/cic/repository.py | lines=471 | funcs=60
- app/services/cic/send_context.py | lines=683 | funcs=26
- app/services/cic/task_contract.py | lines=234 | funcs=5
- app/services/cic/template_service.py | lines=137 | funcs=7

## Best Next Target
- prefix: save
- status: GOOD_NEXT_SPLIT_CANDIDATE
- closure_function_count: 8
- closure_total_lines: 178
- outside_calls: []
- used_assignments: ['BASE_KEY', 'TASK_DEFINITIONS']
- suggested_module: app/services/cic/save_context.py

## Recommended Candidates Top 20
- prefix=save | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=8 | closure_lines=178 | outside_calls=0 | suggested=app/services/cic/save_context.py
- prefix=run | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=124 | outside_calls=0 | suggested=app/services/cic/run_context.py
- prefix=celebration | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=70 | outside_calls=0 | suggested=app/services/cic/celebration_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
