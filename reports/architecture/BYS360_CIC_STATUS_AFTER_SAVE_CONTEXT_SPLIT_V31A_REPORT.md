# BYS360 CIC Status After Save Context Split V31A
- Generated at: 2026-06-25T21:02:15
- Status: READY_FOR_NEXT_SPLIT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: e3b0339
- Target lines: 881
- Target functions: 5
- Still god-object candidate: True
- Lines to go under 800: 82

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
- app/services/cic/save_context.py | lines=454 | funcs=9
- app/services/cic/send_context.py | lines=683 | funcs=26
- app/services/cic/task_contract.py | lines=234 | funcs=5
- app/services/cic/template_service.py | lines=137 | funcs=7

## Best Next Target
- prefix: run
- status: GOOD_NEXT_SPLIT_CANDIDATE
- closure_function_count: 2
- closure_total_lines: 124
- projected_target_lines_after_split: 757
- would_go_under_800: True
- outside_calls: []
- used_assignments: ['TASK_DEFINITIONS']
- suggested_module: app/services/cic/run_context.py

## Recommended Candidates Top 20
- prefix=run | status=GOOD_NEXT_SPLIT_CANDIDATE | closure_funcs=2 | closure_lines=124 | projected=757 | under800=True | outside_calls=0 | suggested=app/services/cic/run_context.py

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
