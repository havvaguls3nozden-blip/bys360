# BYS360 Full God-Object Audit After CIC Exit V33A
- Generated at: 2026-06-25T21:09:17
- Status: NEEDS_MORE_SPLIT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: a02b868
- Python files scanned: 1399
- Syntax errors: 11
- Candidate count total: 49
- Remaining candidates excluding completed targets: 49

## Completed Targets Status
- app/services/corporate_information_center.py | still_candidate=False | lines=763 | funcs=3 | routes=0 | tag=phase4j-cic-godobject-exit-pass-20260625
- app/admin/ops_routes.py | still_candidate=False | lines=291 | funcs=16 | routes=15 | tag=phase4j-ops-routes-split-pass-20260625

## Remaining Candidates Top 50
- app/services/settings/effective_menu.py | lines=2132 | top_funcs=50 | routes=0 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- app/menu_registry.py | lines=1567 | top_funcs=24 | routes=0 | reasons=['line_count_ge_800']
- app/services/performance/low_score_process_service.py | lines=1529 | top_funcs=80 | routes=0 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- scripts/quality/bys360_score100_quality_gate_v1.py | lines=1340 | top_funcs=26 | routes=0 | reasons=['line_count_ge_800']
- app/services/ai_agent/service.py | lines=1336 | top_funcs=49 | routes=0 | reasons=['line_count_ge_800']
- app/services/settings/catalog.py | lines=1331 | top_funcs=0 | routes=0 | reasons=['line_count_ge_800']
- app/institutional/hr_personnel_operations_routes.py | lines=1243 | top_funcs=53 | routes=20 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- app/main_handlers/account_communication_helpers.py | lines=1234 | top_funcs=21 | routes=0 | reasons=['line_count_ge_800']
- app/admin/ai_routes.py | lines=1202 | top_funcs=46 | routes=17 | reasons=['line_count_ge_800']
- app/support/routes.py | lines=1168 | top_funcs=52 | routes=23 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- app/api/mobile/performance_routes.py | lines=1164 | top_funcs=84 | routes=0 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- app/admin/routes.py | lines=1149 | top_funcs=13 | routes=9 | reasons=['line_count_ge_800']
- app/performance/engagement_feedback_routes.py | lines=1135 | top_funcs=23 | routes=23 | reasons=['line_count_ge_800']
- app/communication/surveys_routes.py | lines=1072 | top_funcs=57 | routes=16 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- app/workflow/routes.py | lines=1065 | top_funcs=29 | routes=12 | reasons=['line_count_ge_800']
- app/support/help_center_content.py | lines=1058 | top_funcs=36 | routes=0 | reasons=['line_count_ge_800']
- app/services/ai/dashboard_panel_personnel.py | lines=1039 | top_funcs=15 | routes=0 | reasons=['line_count_ge_800']
- app/services/performance/process_engine_phase6_president_approvals.py | lines=1015 | top_funcs=41 | routes=0 | reasons=['line_count_ge_800']
- app/portal/routes.py | lines=997 | top_funcs=50 | routes=0 | reasons=['line_count_ge_800', 'top_level_function_count_ge_50']
- app/models/hr_models.py | lines=995 | top_funcs=0 | routes=0 | reasons=['line_count_ge_800']
- app/main_handlers/account_settings_helpers.py | lines=972 | top_funcs=14 | routes=0 | reasons=['line_count_ge_800']
- app/services/ai/dashboard_panel_repository.py | lines=965 | top_funcs=17 | routes=0 | reasons=['line_count_ge_800']
- app/services/feedback_service.py | lines=916 | top_funcs=42 | routes=0 | reasons=['line_count_ge_800']
- app/services/dashboard_rebuild_service.py | lines=898 | top_funcs=38 | routes=0 | reasons=['line_count_ge_800']
- app/services/ai_agent/assistant_full_stepwise_tutor_v5.py | lines=887 | top_funcs=15 | routes=0 | reasons=['line_count_ge_800']
- app/services/hr_operations_service.py | lines=881 | top_funcs=22 | routes=0 | reasons=['line_count_ge_800']
- app/services/communication_phase2_service.py | lines=875 | top_funcs=40 | routes=0 | reasons=['line_count_ge_800']
- app/services/ai_agent/assistant_chatgpt_like_v31.py | lines=870 | top_funcs=21 | routes=0 | reasons=['line_count_ge_800']
- app/performance/phase10_development_guidance_ui.py | lines=867 | top_funcs=17 | routes=0 | reasons=['line_count_ge_800']
- app/services/communication_phase3_service.py | lines=859 | top_funcs=34 | routes=0 | reasons=['line_count_ge_800']
- app/services/ai/dashboard_panel_performance.py | lines=847 | top_funcs=15 | routes=0 | reasons=['line_count_ge_800']
- app/services/performance_v2/sync_service.py | lines=835 | top_funcs=22 | routes=0 | reasons=['line_count_ge_800']
- app/menu_registry_data_sections.py | lines=825 | top_funcs=0 | routes=0 | reasons=['line_count_ge_800']
- app/services/performance/task_management_service.py | lines=811 | top_funcs=23 | routes=0 | reasons=['line_count_ge_800']
- app/services/performance/process_engine_phase8_tracking.py | lines=800 | top_funcs=39 | routes=0 | reasons=['line_count_ge_800']
- app/services/mail_performance_sender.py | lines=800 | top_funcs=22 | routes=0 | reasons=['line_count_ge_800']
- app/performance/v2_routes.py | lines=507 | top_funcs=24 | routes=38 | reasons=['route_count_ge_25']
- scripts/quality/bys360_s0f3_pytest_isolated_update_verify.py | lines=487 | top_funcs=None | routes=None | reasons=['syntax_error']
- app/services/cic/repository.py | lines=471 | top_funcs=60 | routes=0 | reasons=['top_level_function_count_ge_50']
- scripts/quality/bys360_a10q_compat_wrapper_rename_apply.py | lines=336 | top_funcs=None | routes=None | reasons=['syntax_error']
- scripts/quality/bys360_phase3d_import_route_smoke_v1.py | lines=243 | top_funcs=None | routes=None | reasons=['syntax_error']
- scripts/quality/bys360_a10d_hard_ui_precision_decision.py | lines=199 | top_funcs=None | routes=None | reasons=['syntax_error']
- scripts/quality/bys360_a10e_hard_ui_false_positive_close.py | lines=152 | top_funcs=None | routes=None | reasons=['syntax_error']
- scripts/maintenance/ensure_message_comments_table_v1.py | lines=147 | top_funcs=None | routes=None | reasons=['syntax_error']
- tests/architecture/test_public_exports_live_guard_v1.py | lines=66 | top_funcs=None | routes=None | reasons=['syntax_error']
- tests/quality/test_code_quality_architecture_score_contract_v1.py | lines=61 | top_funcs=None | routes=None | reasons=['syntax_error']
- scripts/windows/fix_local_admin_display_utf8.py | lines=32 | top_funcs=None | routes=None | reasons=['syntax_error']
- tests/architecture/test_phase3d_import_route_smoke_v1.py | lines=16 | top_funcs=None | routes=None | reasons=['syntax_error']
- tests/critical/conftest.py | lines=11 | top_funcs=None | routes=None | reasons=['syntax_error']

## Syntax Errors
- scripts/maintenance/ensure_message_comments_table_v1.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- scripts/quality/bys360_a10d_hard_ui_precision_decision.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- scripts/quality/bys360_a10e_hard_ui_false_positive_close.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- scripts/quality/bys360_a10q_compat_wrapper_rename_apply.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- scripts/quality/bys360_phase3d_import_route_smoke_v1.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- scripts/quality/bys360_s0f3_pytest_isolated_update_verify.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- scripts/windows/fix_local_admin_display_utf8.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- tests/architecture/test_phase3d_import_route_smoke_v1.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- tests/architecture/test_public_exports_live_guard_v1.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- tests/critical/conftest.py | invalid non-printable character U+FEFF (<unknown>, line 1)
- tests/quality/test_code_quality_architecture_score_contract_v1.py | invalid non-printable character U+FEFF (<unknown>, line 1)

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
