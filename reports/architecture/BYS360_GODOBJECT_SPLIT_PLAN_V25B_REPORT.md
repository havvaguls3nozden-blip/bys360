# BYS360 God-Object Split Plan V25B
- Generated at: 2026-06-25T20:03:29
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 65dccd4
- Candidate count: 53

## Bucket Counts
- helper_module_split_review: 6
- model_review: 1
- registry_catalog_review: 2
- route_file_review: 13
- route_split_priority: 1
- service_function_split_priority: 5
- service_module_review: 25

## Recommended First Target
- path: app/services/corporate_information_center.py
- bucket: service_function_split_priority
- reason: Route icermeyen servis dosyasi; fonksiyon gruplarina bolmek icin iyi aday.
- lines: 2353
- functions: 107
- routes: 0
- module references: 243
- stem references: 2926

## Safe First Wave Top 20
- app/services/corporate_information_center.py | bucket=service_function_split_priority | score=8004 | lines=2353 | funcs=107 | routes=0 | module_refs=243 | stem_refs=2926
- app/services/settings/effective_menu.py | bucket=service_function_split_priority | score=6990 | lines=2132 | funcs=54 | routes=0 | module_refs=81 | stem_refs=129
- app/services/performance/low_score_process_service.py | bucket=service_function_split_priority | score=6308 | lines=1529 | funcs=81 | routes=0 | module_refs=123 | stem_refs=126
- app/services/ai_agent/service.py | bucket=service_function_split_priority | score=6123 | lines=1336 | funcs=51 | routes=0 | module_refs=35 | stem_refs=14331
- app/services/cic/repository.py | bucket=service_function_split_priority | score=4579 | lines=471 | funcs=60 | routes=0 | module_refs=14 | stem_refs=245
- app/services/hr_operations_service.py | bucket=service_module_review | score=4475 | lines=881 | funcs=22 | routes=0 | module_refs=31 | stem_refs=32
- app/services/dashboard_rebuild_service.py | bucket=service_module_review | score=4129 | lines=898 | funcs=47 | routes=0 | module_refs=45 | stem_refs=45
- app/services/performance/process_engine_phase6_president_approvals.py | bucket=service_module_review | score=4056 | lines=1015 | funcs=41 | routes=0 | module_refs=49 | stem_refs=104
- app/services/feedback_service.py | bucket=service_module_review | score=3950 | lines=916 | funcs=42 | routes=0 | module_refs=76 | stem_refs=108
- app/services/communication_phase2_service.py | bucket=service_module_review | score=3823 | lines=875 | funcs=40 | routes=0 | module_refs=38 | stem_refs=40
- app/services/communication_phase3_service.py | bucket=service_module_review | score=3710 | lines=859 | funcs=35 | routes=0 | module_refs=29 | stem_refs=32
- app/services/ai_decision/decision_support_engine.py | bucket=service_module_review | score=3684 | lines=407 | funcs=17 | routes=0 | module_refs=9 | stem_refs=14
- app/services/performance_v2/sync_service.py | bucket=service_module_review | score=3681 | lines=835 | funcs=22 | routes=0 | module_refs=39 | stem_refs=108
- app/services/performance/process_engine_phase8_tracking.py | bucket=service_module_review | score=3681 | lines=800 | funcs=39 | routes=0 | module_refs=25 | stem_refs=52
- app/services/performance/task_management_service.py | bucket=service_module_review | score=3594 | lines=811 | funcs=23 | routes=0 | module_refs=45 | stem_refs=46
- app/services/ai/history_compare.py | bucket=service_module_review | score=3401 | lines=647 | funcs=14 | routes=0 | module_refs=8 | stem_refs=8
- app/services/ai/dashboard_panel_personnel.py | bucket=service_module_review | score=3379 | lines=1039 | funcs=16 | routes=0 | module_refs=77 | stem_refs=77
- app/services/ai/quality.py | bucket=service_module_review | score=3312 | lines=363 | funcs=9 | routes=0 | module_refs=11 | stem_refs=8228
- app/services/mail_performance_sender.py | bucket=service_module_review | score=3288 | lines=800 | funcs=24 | routes=0 | module_refs=184 | stem_refs=184
- app/main_handlers/account_settings_helpers.py | bucket=helper_module_split_review | score=3254 | lines=972 | funcs=14 | routes=0 | module_refs=31 | stem_refs=32

## Route Wave Top 20
- app/performance/v2_routes.py | bucket=route_split_priority | lines=507 | funcs=24 | routes=38
- app/support/routes.py | bucket=route_file_review | lines=1168 | funcs=52 | routes=23
- app/performance/engagement_feedback_routes.py | bucket=route_file_review | lines=1135 | funcs=25 | routes=23
- app/api/mobile/performance_routes.py | bucket=route_file_review | lines=1164 | funcs=84 | routes=22
- app/portal/routes.py | bucket=route_file_review | lines=997 | funcs=50 | routes=21
- app/institutional/hr_personnel_operations_routes.py | bucket=route_file_review | lines=1243 | funcs=53 | routes=20
- app/admin/ai_routes.py | bucket=route_file_review | lines=1202 | funcs=46 | routes=17
- app/communication/surveys_routes.py | bucket=route_file_review | lines=1072 | funcs=57 | routes=16
- app/workflow/routes.py | bucket=route_file_review | lines=1065 | funcs=30 | routes=12
- app/admin/routes.py | bucket=route_file_review | lines=1149 | funcs=13 | routes=9
- app/performance/routes.py | bucket=route_file_review | lines=706 | funcs=13 | routes=8
- app/api/mobile/performance_read_routes.py | bucket=route_file_review | lines=219 | funcs=9 | routes=8
- app/performance/interim_notes_manager_routes.py | bucket=route_file_review | lines=413 | funcs=20 | routes=4
- app/performance/history_import_routes.py | bucket=route_file_review | lines=450 | funcs=5 | routes=3

## Review Wave Top 20
- app/menu_registry.py | bucket=registry_catalog_review | lines=1567 | funcs=24 | routes=0
- app/models/hr_models.py | bucket=model_review | lines=995 | funcs=1 | routes=0
- app/menu_registry_data_sections.py | bucket=registry_catalog_review | lines=825 | funcs=0 | routes=0

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False

## Decision
- Bu rapor kaynak kodu degistirmez.
- 53 god-object adayi split dalgalarina ayrildi.
- Ilk dalga icin route icermeyen servis/helper dosyalari tercih edildi.
- Route dosyalari daha sonra testli ve kademeli bolunmelidir.
- Model, registry ve catalog dosyalari otomatik bolunmemeli; once import/veri yapisi incelenmelidir.
