# BYS360 CIC Split Inspect V26A
- Generated at: 2026-06-25T20:07:06
- Status: READY_FOR_SPLIT_PLANNING
- OK: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: b9cfc6a
- Target: app/services/corporate_information_center.py
- Lines: 2353
- Top-level functions: 105
- Top-level classes: 0
- Route count: 0
- Prefix group count: 30
- Dependency component count: 5

## Recommended Strategy
- Dosyanin dis referansi yuksek oldugu icin import yollarini bir anda degistirmek riskli.
- Mevcut dosya facade olarak kalmali; dis dunya ayni modulu import etmeye devam etmeli.
- Fonksiyon gruplari app/services/cic/ altina tasinip facade dosyada re-export edilmelidir.
- Ilk uygulama en az bagimli prefix grubuyla baslamalidir.
- Target package: app/services/cic/
- Facade file: app/services/corporate_information_center.py

## Safe Split Groups Top 20
- prefix=_private | funcs=3 | total_lines=38 | cross_deps=3 | suggested=app/services/cic/_private.py

## Prefix Groups
- prefix=_cic | funcs=61 | total_lines=874 | cross_deps=25 | suggested=app/services/cic/_cic_service.py
- prefix=get | funcs=6 | total_lines=57 | cross_deps=7 | suggested=app/services/cic/get_service.py
- prefix=save | funcs=5 | total_lines=121 | cross_deps=15 | suggested=app/services/cic/save_service.py
- prefix=_private | funcs=3 | total_lines=38 | cross_deps=3 | suggested=app/services/cic/_private.py
- prefix=ensure | funcs=2 | total_lines=57 | cross_deps=4 | suggested=app/services/cic/ensure_service.py
- prefix=set | funcs=2 | total_lines=37 | cross_deps=3 | suggested=app/services/cic/set_service.py
- prefix=_render | funcs=2 | total_lines=32 | cross_deps=7 | suggested=app/services/cic/_render_service.py
- prefix=_recipients | funcs=2 | total_lines=17 | cross_deps=4 | suggested=app/services/cic/_recipients_service.py
- prefix=import | funcs=1 | total_lines=119 | cross_deps=8 | suggested=app/services/cic/import_service.py
- prefix=_run | funcs=1 | total_lines=104 | cross_deps=10 | suggested=app/services/cic/_run_service.py
- prefix=_send | funcs=1 | total_lines=99 | cross_deps=11 | suggested=app/services/cic/_send_service.py
- prefix=_context | funcs=1 | total_lines=53 | cross_deps=15 | suggested=app/services/cic/_context_service.py
- prefix=_ensure | funcs=1 | total_lines=44 | cross_deps=4 | suggested=app/services/cic/_ensure_service.py
- prefix=celebration | funcs=1 | total_lines=40 | cross_deps=13 | suggested=app/services/cic/celebration_service.py
- prefix=send | funcs=1 | total_lines=28 | cross_deps=3 | suggested=app/services/cic/send_service.py
- prefix=list | funcs=1 | total_lines=23 | cross_deps=0 | suggested=app/services/cic/list_service.py
- prefix=misc | funcs=1 | total_lines=22 | cross_deps=3 | suggested=app/services/cic/misc.py
- prefix=run | funcs=1 | total_lines=20 | cross_deps=3 | suggested=app/services/cic/run_service.py
- prefix=_active | funcs=1 | total_lines=15 | cross_deps=0 | suggested=app/services/cic/_active_service.py
- prefix=_format | funcs=1 | total_lines=12 | cross_deps=0 | suggested=app/services/cic/_format_service.py
- prefix=_dashboard | funcs=1 | total_lines=12 | cross_deps=1 | suggested=app/services/cic/_dashboard_service.py
- prefix=_clean | funcs=1 | total_lines=11 | cross_deps=0 | suggested=app/services/cic/_clean_service.py
- prefix=_loads | funcs=1 | total_lines=9 | cross_deps=1 | suggested=app/services/cic/_loads_service.py
- prefix=_has | funcs=1 | total_lines=7 | cross_deps=0 | suggested=app/services/cic/_has_service.py
- prefix=_user | funcs=1 | total_lines=7 | cross_deps=0 | suggested=app/services/cic/_user_service.py
- prefix=_users | funcs=1 | total_lines=6 | cross_deps=0 | suggested=app/services/cic/_users_service.py
- prefix=can | funcs=1 | total_lines=5 | cross_deps=0 | suggested=app/services/cic/can_service.py
- prefix=_save | funcs=1 | total_lines=5 | cross_deps=1 | suggested=app/services/cic/_save_service.py
- prefix=_tomorrow | funcs=1 | total_lines=4 | cross_deps=0 | suggested=app/services/cic/_tomorrow_service.py
- prefix=_dumps | funcs=1 | total_lines=2 | cross_deps=0 | suggested=app/services/cic/_dumps_service.py

## Largest Functions Top 30
- import_celebration_dates_from_excel | prefix=import | line=2234 | length=119 | calls=['_cic_v45_bool', '_cic_v45_build_user_indexes', '_cic_v45_ensure_schema', '_cic_v45_existing_user_rows', '_cic_v45_header_key', '_cic_v45_norm_name', '_cic_v45_parse_date', '_cic_v45_text']
- _run_due_tasks_base | prefix=_run | line=1404 | length=104 | calls=['_cic_auto_last_run_key', '_cic_is_weekend', '_cic_weekday_name_tr', '_now', 'ensure_defaults', 'get_auto_scheduler_config', 'get_config', 'get_setting', 'send_task', 'set_setting']
- _send_task_base | prefix=_send | line=1151 | length=99 | calls=['_cic_v11_mail_settings', '_cic_v11_normalize_email', '_cic_v11_send_email_direct', '_dumps_json', '_now', '_recipients_for_task', '_render_template_text', 'ensure_defaults', 'get_config', 'get_template', 'set_setting']
- _cic_phase6_build | prefix=_cic | line=913 | length=90 | calls=['_cic_phase6_item', '_cic_phase6_log_quality', '_cic_phase6_missing_email_count', '_cic_phase6_template_quality']
- save_celebration_settings | prefix=save | line=1991 | length=56 | calls=['_cic_v40_bool', '_cic_v40_parse_date', '_dumps_json', 'ensure_celebration_schema', 'set_setting']
- _context_base | prefix=_context | line=790 | length=53 | calls=['_cic_phase5_audit_list', '_cic_phase5_last_result', '_cic_phase5_log_metrics', '_cic_phase5_mail_health', '_cic_phase5_readiness', '_cic_phase5_task_preview', '_has_settings_table', '_loads_json', 'ensure_defaults', 'get_config', 'get_recent_logs', 'get_recipients', 'get_setting', 'get_template', 'list_users']
- _cic_v11_send_email_direct | prefix=_cic | line=1097 | length=52 | calls=['_cic_v11_clean_header', '_cic_v11_mail_settings', '_cic_v11_normalize_email']
- _cic_phase5_log_metrics | prefix=_cic | line=686 | length=48 | calls=[]
- _cic_v40_create_system_notifications | prefix=_cic | line=1834 | length=45 | calls=['_cic_v40_setting_bool', '_cic_v40_today', '_render_template_text', 'get_template']
- _ensure_defaults_base | prefix=_ensure | line=220 | length=44 | calls=['_dumps_json', '_loads_json', 'get_setting', 'set_setting']
- celebration_context | prefix=celebration | line=1949 | length=40 | calls=['_cic_v40_anniversary_users', '_cic_v40_birthday_users', '_cic_v40_setting_bool', '_cic_v40_special_days', '_cic_v40_special_days_today', '_cic_v40_upcoming_special_days', '_cic_v40_upcoming_users', '_dumps_json', 'context', 'ensure_celebration_schema', 'ensure_defaults', 'get_setting', 'list_users']
- _cic_v11_get_setting_value | prefix=_cic | line=1023 | length=35 | calls=['get_setting']
- _cic_phase5_readiness | prefix=_cic | line=736 | length=33 | calls=['_cic_phase5_last_result', '_cic_phase5_mail_health']
- save_recipients | prefix=save | line=1254 | length=30 | calls=['_clean_ids', '_dumps_json', '_now', 'set_setting']
- ensure_celebration_schema | prefix=ensure | line=1654 | length=30 | calls=[]
- _cic_v40_run_weekend_celebrations | prefix=_cic | line=2048 | length=29 | calls=['_cic_auto_last_run_key', '_cic_v40_setting_bool', 'get_auto_scheduler_config', 'get_config', 'get_setting', 'send_task', 'set_setting']
- send_task | prefix=send | line=1881 | length=28 | calls=['_cic_v40_create_system_notifications', '_recipients_for_task', '_send_task_base']
- _cic_phase3_make_result | prefix=_cic | line=551 | length=27 | calls=['_cic_phase3_actor_label', '_cic_phase3_task_label', '_now']
- ensure_defaults | prefix=ensure | line=1686 | length=27 | calls=['_dumps_json', '_ensure_defaults_base', 'get_setting', 'set_setting']
- _cic_phase5_mail_health | prefix=_cic | line=658 | length=26 | calls=[]
- _cic_v45_parse_date | prefix=_cic | line=2143 | length=25 | calls=['_cic_v45_text']
- _cic_v11_mail_settings | prefix=_cic | line=1071 | length=24 | calls=['_cic_v11_bool', '_cic_v11_get_setting_value']
- list_users | prefix=list | line=337 | length=23 | calls=[]
- _weather | prefix=_private | line=397 | length=23 | calls=['_clothing', '_format_weather', '_tomorrow_note', 'get_config']
- set_auto_scheduler_config | prefix=set | line=1340 | length=22 | calls=['_cic_auto_bool', 'get_setting', 'set_setting']
- context | prefix=misc | line=1376 | length=22 | calls=['_cic_phase6_build', '_context_base', 'get_auto_scheduler_config']
- _cic_v40_upcoming_users | prefix=_cic | line=1916 | length=20 | calls=['_cic_v40_active_staff_candidates', '_cic_v40_days_until', '_cic_v40_mmdd', '_cic_v40_service_year', '_cic_v40_today', '_cic_v40_user_date']
- run_due_tasks | prefix=run | line=2079 | length=20 | calls=['_cic_v40_run_weekend_celebrations', '_now', '_run_due_tasks_base']
- save_tasks | prefix=save | line=292 | length=19 | calls=['_dumps_json', 'get_config', 'set_setting']
- _render_template_text_base | prefix=_render | line=471 | length=19 | calls=['_dashboard_counts', '_now', '_user_name', '_weather', 'get_config']

## Largest Dependency Components Top 20
- size=92 | prefixes={'_active': 1, '_cic': 50, 'get': 6, '_context': 1, '_recipients': 2, '_users': 1, 'celebration': 1, '_has': 1, '_loads': 1, 'misc': 1, 'ensure': 2, 'list': 1, '_clean': 1, '_render': 2, '_run': 1, '_send': 1, '_private': 3, 'save': 5, 'send': 1, '_dumps': 1, '_dashboard': 1, '_ensure': 1, 'set': 2, 'run': 1, '_user': 1, '_format': 1, '_tomorrow': 1, '_save': 1} | members=['_active_staff_users', '_cic_auto_bool', '_cic_auto_last_run_key', '_cic_is_weekend', '_cic_phase3_actor_label', '_cic_phase3_last_result', '_cic_phase3_make_result', '_cic_phase3_store_result', '_cic_phase3_task_label', '_cic_phase5_actor', '_cic_phase5_audit_list', '_cic_phase5_last_result', '_cic_phase5_log_metrics', '_cic_phase5_mail_health', '_cic_phase5_now_label', '_cic_phase5_readiness', '_cic_phase5_safe_int', '_cic_phase5_store_audit', '_cic_phase5_task_preview', '_cic_phase6_build', '_cic_phase6_item', '_cic_phase6_log_quality', '_cic_phase6_missing_email_count', '_cic_phase6_status', '_cic_phase6_template_quality', '_cic_v11_bool', '_cic_v11_clean_header', '_cic_v11_get_setting_value', '_cic_v11_mail_settings', '_cic_v11_normalize_email', '_cic_v11_send_email_direct', '_cic_v40_active_staff_candidates', '_cic_v40_anniversary_users', '_cic_v40_birthday_users', '_cic_v40_bool', '_cic_v40_create_system_notifications', '_cic_v40_date_input', '_cic_v40_days_until', '_cic_v40_mmdd', '_cic_v40_parse_date']
- size=10 | prefixes={'_cic': 9, 'import': 1} | members=['_cic_v45_bool', '_cic_v45_build_user_indexes', '_cic_v45_ensure_schema', '_cic_v45_existing_user_rows', '_cic_v45_header_key', '_cic_v45_norm', '_cic_v45_norm_name', '_cic_v45_parse_date', '_cic_v45_text', 'import_celebration_dates_from_excel']
- size=1 | prefixes={'_cic': 1} | members=['_cic_phase3_public_error']
- size=1 | prefixes={'_cic': 1} | members=['_cic_phase6_bool']
- size=1 | prefixes={'can': 1} | members=['can_manage']

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False

## Decision
- Bu rapor kaynak kodu degistirmez.
- corporate_information_center.py ilk split hedefi olarak incelendi.
- Dis referans sayisi yuksek oldugu icin facade-preserving split onerildi.
- Bir sonraki adim V26B: en az bagimli prefix grubunu app/services/cic/ altina alip facade re-export ile geriye uyumlulugu korumak.
