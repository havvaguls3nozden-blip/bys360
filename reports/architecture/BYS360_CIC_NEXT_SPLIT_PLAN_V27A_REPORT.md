# BYS360 CIC Next Split Plan V27A
- Generated at: 2026-06-25T20:21:09
- Status: READY_FOR_NEXT_SPLIT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: b2ea366
- Target: app/services/corporate_information_center.py
- Lines: 2184
- Functions: 91
- Routes: 0
- Prefix groups: 22
- V26F2 status: PASS

## Best Next Target
- prefix: misc
- seed_function_count: 1
- seed_total_lines: 22
- closure_function_count: 23
- closure_total_lines: 450
- closure_functions: ['_active_staff_users', '_cic_auto_bool', '_cic_phase5_audit_list', '_cic_phase5_last_result', '_cic_phase5_log_metrics', '_cic_phase5_mail_health', '_cic_phase5_readiness', '_cic_phase5_safe_int', '_cic_phase5_task_preview', '_cic_phase6_build', '_cic_phase6_item', '_cic_phase6_log_quality', '_cic_phase6_missing_email_count', '_cic_phase6_status', '_cic_phase6_template_quality', '_context_base', '_users_by_ids', 'context', 'get_auto_scheduler_config', 'get_recent_logs', 'get_recipients', 'get_template', 'list_users']
- outside_calls: []
- used_imports: ['Any', 'User', '_has_settings_table', '_loads_json', 'current_app', 'ensure_defaults', 'get_config', 'get_setting', 'or_']
- used_assignments: ['BASE_KEY', 'TASK_DEFINITIONS']
- unknown_external_names: ['MailLog', 'add', 'send_email']
- risk_score: 170
- benefit_score: 680
- priority_score: 510
- recommended_status: GOOD_NEXT_SPLIT_CANDIDATE
- suggested_module: app/services/cic/misc_context.py

## Recommended Candidates Top 20
- prefix=misc | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=1 | closure_funcs=23 | closure_lines=450 | outside_calls=0 | assignments=2 | suggested=app/services/cic/misc_context.py
- prefix=_context | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=1 | closure_funcs=14 | closure_lines=263 | outside_calls=0 | assignments=2 | suggested=app/services/cic/context_context.py
- prefix=_recipients | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=2 | closure_funcs=18 | closure_lines=171 | outside_calls=0 | assignments=3 | suggested=app/services/cic/recipients_context.py
- prefix=import | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=1 | closure_funcs=10 | closure_lines=224 | outside_calls=0 | assignments=0 | suggested=app/services/cic/import_context.py
- prefix=save | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=5 | closure_funcs=11 | closure_lines=209 | outside_calls=0 | assignments=2 | suggested=app/services/cic/save_context.py
- prefix=_render | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=2 | closure_funcs=12 | closure_lines=129 | outside_calls=0 | assignments=2 | suggested=app/services/cic/render_context.py
- prefix=get | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=4 | closure_funcs=7 | closure_lines=67 | outside_calls=0 | assignments=2 | suggested=app/services/cic/get_context.py
- prefix=set | status=GOOD_NEXT_SPLIT_CANDIDATE | seed_funcs=1 | closure_funcs=2 | closure_lines=29 | outside_calls=0 | assignments=1 | suggested=app/services/cic/set_context.py
- prefix=_cic | status=POSSIBLE_BUT_LARGE | seed_funcs=61 | closure_funcs=74 | closure_lines=1122 | outside_calls=0 | assignments=5 | suggested=app/services/cic/cic_context.py
- prefix=celebration | status=POSSIBLE_BUT_LARGE | seed_funcs=1 | closure_funcs=40 | closure_lines=672 | outside_calls=0 | assignments=3 | suggested=app/services/cic/celebration_context.py
- prefix=run | status=POSSIBLE_BUT_LARGE | seed_funcs=1 | closure_funcs=40 | closure_lines=719 | outside_calls=0 | assignments=4 | suggested=app/services/cic/run_context.py
- prefix=_run | status=POSSIBLE_BUT_LARGE | seed_funcs=1 | closure_funcs=38 | closure_lines=670 | outside_calls=0 | assignments=4 | suggested=app/services/cic/run_context.py
- prefix=_send | status=POSSIBLE_BUT_LARGE | seed_funcs=1 | closure_funcs=30 | closure_lines=456 | outside_calls=0 | assignments=3 | suggested=app/services/cic/send_context.py
- prefix=send | status=POSSIBLE_BUT_LARGE | seed_funcs=1 | closure_funcs=32 | closure_lines=529 | outside_calls=0 | assignments=4 | suggested=app/services/cic/send_context.py

## Review Candidates Top 20
- none

## Largest Functions Top 30
- import_celebration_dates_from_excel | prefix=import | line=2065 | length=119 | calls=['_cic_v45_bool', '_cic_v45_build_user_indexes', '_cic_v45_ensure_schema', '_cic_v45_existing_user_rows', '_cic_v45_header_key', '_cic_v45_norm_name', '_cic_v45_parse_date', '_cic_v45_text']
- _run_due_tasks_base | prefix=_run | line=1262 | length=104 | calls=['_cic_auto_last_run_key', '_cic_is_weekend', '_cic_weekday_name_tr', 'get_auto_scheduler_config', 'send_task']
- _send_task_base | prefix=_send | line=1009 | length=99 | calls=['_cic_v11_mail_settings', '_cic_v11_normalize_email', '_cic_v11_send_email_direct', '_recipients_for_task', '_render_template_text', 'get_template']
- _cic_phase6_build | prefix=_cic | line=771 | length=90 | calls=['_cic_phase6_item', '_cic_phase6_log_quality', '_cic_phase6_missing_email_count', '_cic_phase6_template_quality']
- save_celebration_settings | prefix=save | line=1822 | length=56 | calls=['_cic_v40_bool', '_cic_v40_parse_date', 'ensure_celebration_schema']
- _context_base | prefix=_context | line=648 | length=53 | calls=['_cic_phase5_audit_list', '_cic_phase5_last_result', '_cic_phase5_log_metrics', '_cic_phase5_mail_health', '_cic_phase5_readiness', '_cic_phase5_task_preview', 'get_recent_logs', 'get_recipients', 'get_template', 'list_users']
- _cic_v11_send_email_direct | prefix=_cic | line=955 | length=52 | calls=['_cic_v11_clean_header', '_cic_v11_mail_settings', '_cic_v11_normalize_email']
- _cic_phase5_log_metrics | prefix=_cic | line=544 | length=48 | calls=[]
- _cic_v40_create_system_notifications | prefix=_cic | line=1665 | length=45 | calls=['_cic_v40_setting_bool', '_cic_v40_today', '_render_template_text', 'get_template']
- celebration_context | prefix=celebration | line=1780 | length=40 | calls=['_cic_v40_anniversary_users', '_cic_v40_birthday_users', '_cic_v40_setting_bool', '_cic_v40_special_days', '_cic_v40_special_days_today', '_cic_v40_upcoming_special_days', '_cic_v40_upcoming_users', 'context', 'ensure_celebration_schema', 'list_users']
- _cic_v11_get_setting_value | prefix=_cic | line=881 | length=35 | calls=[]
- _cic_phase5_readiness | prefix=_cic | line=594 | length=33 | calls=['_cic_phase5_last_result', '_cic_phase5_mail_health']
- save_recipients | prefix=save | line=1112 | length=30 | calls=[]
- ensure_celebration_schema | prefix=ensure | line=1512 | length=30 | calls=[]
- _cic_v40_run_weekend_celebrations | prefix=_cic | line=1879 | length=29 | calls=['_cic_auto_last_run_key', '_cic_v40_setting_bool', 'get_auto_scheduler_config', 'send_task']
- send_task | prefix=send | line=1712 | length=28 | calls=['_cic_v40_create_system_notifications', '_recipients_for_task', '_send_task_base']
- _cic_phase3_make_result | prefix=_cic | line=409 | length=27 | calls=['_cic_phase3_actor_label', '_cic_phase3_task_label']
- _cic_phase5_mail_health | prefix=_cic | line=516 | length=26 | calls=[]
- _cic_v45_parse_date | prefix=_cic | line=1974 | length=25 | calls=['_cic_v45_text']
- _cic_v11_mail_settings | prefix=_cic | line=929 | length=24 | calls=['_cic_v11_bool', '_cic_v11_get_setting_value']
- list_users | prefix=list | line=247 | length=23 | calls=[]
- set_auto_scheduler_config | prefix=set | line=1198 | length=22 | calls=['_cic_auto_bool']
- context | prefix=misc | line=1234 | length=22 | calls=['_cic_phase6_build', '_context_base', 'get_auto_scheduler_config']
- _cic_v40_upcoming_users | prefix=_cic | line=1747 | length=20 | calls=['_cic_v40_active_staff_candidates', '_cic_v40_days_until', '_cic_v40_mmdd', '_cic_v40_service_year', '_cic_v40_today', '_cic_v40_user_date']
- run_due_tasks | prefix=run | line=1910 | length=20 | calls=['_cic_v40_run_weekend_celebrations', '_run_due_tasks_base']
- save_tasks | prefix=save | line=202 | length=19 | calls=[]
- _render_template_text_base | prefix=_render | line=329 | length=19 | calls=['_dashboard_counts', '_user_name']
- _cic_v40_special_days | prefix=_cic | line=1546 | length=19 | calls=['_cic_v40_bool']
- _cic_phase5_task_preview | prefix=_cic | line=629 | length=18 | calls=['_cic_phase5_safe_int']
- get_auto_scheduler_config | prefix=get | line=1178 | length=18 | calls=['_cic_auto_bool']

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
