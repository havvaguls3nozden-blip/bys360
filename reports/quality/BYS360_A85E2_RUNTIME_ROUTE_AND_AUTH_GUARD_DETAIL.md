# BYS360 A8.5E-2 Runtime Route ve Auth Guard Detay Raporu

Tarih: 2026-06-12T18:09:55

## Runtime Route Map

- Runtime toplam route count: 934
- Runtime /api/mobile route count: 68

### Runtime mobile route listesi

- ['GET'] `/api/mobile/ai/insights` endpoint=`mobile_api.mobile_ai_insights`
- ['GET'] `/api/mobile/assistant/suggestions` endpoint=`mobile_api.mobile_assistant_suggestions`
- ['POST'] `/api/mobile/assistant/v2/ask` endpoint=`mobile_api.mobile_b49_assistant_v2_ask`
- ['POST'] `/api/mobile/auth/login` endpoint=`mobile_api.mobile_login`
- ['POST'] `/api/mobile/auth/refresh` endpoint=`mobile_api.mobile_refresh`
- ['POST'] `/api/mobile/communication/messages/create-thread` endpoint=`mobile_api.mobile_b46_communication_create_thread`
- ['GET'] `/api/mobile/communication/messages/threads` endpoint=`mobile_api.mobile_b46_communication_message_threads`
- ['GET'] `/api/mobile/communication/messages/threads/<int:thread_id>` endpoint=`mobile_api.mobile_b46_communication_thread_detail`
- ['POST'] `/api/mobile/communication/messages/threads/<int:thread_id>/send` endpoint=`mobile_api.mobile_b46_communication_send_message`
- ['GET'] `/api/mobile/communication/messages/users` endpoint=`mobile_api.mobile_b46_communication_users`
- ['GET'] `/api/mobile/communication/threads` endpoint=`mobile_api.mobile_communication_threads`
- ['POST'] `/api/mobile/communication/v2/create-thread` endpoint=`mobile_api.mobile_b48_communication_v2_create_thread`
- ['GET'] `/api/mobile/communication/v2/threads` endpoint=`mobile_api.mobile_b48_communication_v2_threads`
- ['GET'] `/api/mobile/communication/v2/threads/<int:thread_id>` endpoint=`mobile_api.mobile_b48_communication_v2_thread_detail`
- ['POST'] `/api/mobile/communication/v2/threads/<int:thread_id>/send` endpoint=`mobile_api.mobile_b48_communication_v2_send`
- ['GET'] `/api/mobile/communication/v2/users` endpoint=`mobile_api.mobile_b48_communication_v2_users`
- ['GET'] `/api/mobile/dashboard/summary` endpoint=`mobile_api.mobile_dashboard_summary`
- ['GET'] `/api/mobile/health` endpoint=`mobile_api.mobile_health`
- ['GET'] `/api/mobile/kpi/goals` endpoint=`mobile_api.mobile_kpi_goals`
- ['GET'] `/api/mobile/kpi/target-management` endpoint=`mobile_api.mobile_kpi_target_management_v2853`
- ['POST'] `/api/mobile/kpi/target-management` endpoint=`mobile_api.mobile_kpi_target_create_v2853`
- ['POST'] `/api/mobile/kpi/target-management/<int:target_id>/progress` endpoint=`mobile_api.mobile_kpi_target_progress_v2853`
- ['GET'] `/api/mobile/me` endpoint=`mobile_api.mobile_me`
- ['GET'] `/api/mobile/notifications` endpoint=`mobile_api.mobile_notifications`
- ['POST'] `/api/mobile/notifications/<int:notification_id>/read` endpoint=`mobile_api.mobile_notification_mark_read_v2864`
- ['POST'] `/api/mobile/notifications/read-all` endpoint=`mobile_api.mobile_notifications_mark_all_read_v2864`
- ['GET'] `/api/mobile/performance/approvals` endpoint=`mobile_api.mobile_performance_approvals`
- ['GET'] `/api/mobile/performance/categories` endpoint=`mobile_api.mobile_performance_categories`
- ['GET'] `/api/mobile/performance/criteria` endpoint=`mobile_api.mobile_performance_criteria`
- ['GET'] `/api/mobile/performance/development-suggestions` endpoint=`mobile_api.mobile_performance_development_suggestions`
- ['GET'] `/api/mobile/performance/full-feature-summary` endpoint=`mobile_api._bys360_legacy_mobile_performance_full_feature_summary`
- ['GET'] `/api/mobile/performance/history-archive` endpoint=`mobile_api._bys360_prev_mobile_performance_history_archive_v21748`
- ['GET'] `/api/mobile/performance/in-period-note-options` endpoint=`mobile_api.mobile_performance_in_period_note_options_v2853`
- ['GET'] `/api/mobile/performance/in-period-notes` endpoint=`mobile_api._bys360_legacy_mobile_performance_in_period_notes`
- ['GET'] `/api/mobile/performance/in-period-notes/v2` endpoint=`mobile_api._bys360_legacy_mobile_performance_in_period_notes_v2853`
- ['POST'] `/api/mobile/performance/in-period-notes/v2` endpoint=`mobile_api.mobile_performance_create_in_period_note_v2853`
- ['GET'] `/api/mobile/performance/manager-tasks` endpoint=`mobile_api.mobile_performance_manager_tasks`
- ['GET'] `/api/mobile/performance/manager-view` endpoint=`mobile_api.mobile_performance_manager_view_v2852`
- ['GET'] `/api/mobile/performance/note-scorecard` endpoint=`mobile_api._bys360_legacy_mobile_performance_note_scorecard_v2863a`
- ['GET'] `/api/mobile/performance/periods` endpoint=`mobile_api.mobile_performance_periods`
- ['GET'] `/api/mobile/performance/periods/<int:period_id>` endpoint=`mobile_api.mobile_performance_period_detail`
- ['GET'] `/api/mobile/performance/president-approvals` endpoint=`mobile_api._bys360_prev_mobile_performance_president_approvals_alias_v21748`
- ['GET'] `/api/mobile/performance/publish-preapproval` endpoint=`mobile_api.mobile_performance_publish_preapproval`
- ['GET'] `/api/mobile/performance/reminders` endpoint=`mobile_api.mobile_performance_reminders`
- ['GET'] `/api/mobile/performance/reports` endpoint=`mobile_api.mobile_performance_reports`
- ['GET'] `/api/mobile/performance/risk-analysis` endpoint=`mobile_api._bys360_legacy_mobile_performance_risk_analysis_v2852`
- ['GET'] `/api/mobile/performance/rules-summary` endpoint=`mobile_api.mobile_performance_rules_summary`
- ['GET'] `/api/mobile/performance/scorecards` endpoint=`mobile_api.mobile_performance_scorecards`
- ['GET'] `/api/mobile/performance/summary` endpoint=`mobile_api.mobile_performance_summary`
- ['GET'] `/api/mobile/performance/tasks` endpoint=`mobile_api.mobile_performance_tasks`
- ['GET'] `/api/mobile/performance/tasks/<int:assignment_id>` endpoint=`mobile_api.mobile_performance_task_detail`
- ['POST'] `/api/mobile/performance/tasks/<int:assignment_id>/score-action` endpoint=`mobile_api.mobile_performance_task_score_action`
- ['GET'] `/api/mobile/performance/tasks/<int:assignment_id>/score-form` endpoint=`mobile_api.mobile_performance_task_score_form`
- ['POST'] `/api/mobile/performance/tasks/<int:assignment_id>/score-form` endpoint=`mobile_api.mobile_performance_task_score_submit`
- ['GET'] `/api/mobile/performance/third-manager` endpoint=`mobile_api.mobile_performance_third_manager`
- ['GET'] `/api/mobile/performance/weights` endpoint=`mobile_api.mobile_performance_weights`
- ['POST'] `/api/mobile/personnel/add` endpoint=`mobile_api.mobile_personnel_add_alias`
- ['GET'] `/api/mobile/personnel/all` endpoint=`mobile_api.mobile_personnel_all`
- ['POST'] `/api/mobile/personnel/create` endpoint=`mobile_api.mobile_personnel_create`
- ['GET'] `/api/mobile/personnel/list` endpoint=`mobile_api.mobile_personnel_list`
- ['GET'] `/api/mobile/settings/summary` endpoint=`mobile_api.mobile_settings_summary`
- ['POST'] `/api/mobile/support/tickets` endpoint=`mobile_api.mobile_support_ticket_create`
- ['GET'] `/api/mobile/support/tickets` endpoint=`mobile_api.mobile_support_tickets`
- ['GET'] `/api/mobile/support/tickets/<int:ticket_id>` endpoint=`mobile_api.mobile_support_ticket_detail`
- ['POST'] `/api/mobile/support/tickets/<int:ticket_id>/reply` endpoint=`mobile_api.mobile_support_ticket_reply`
- ['GET'] `/api/mobile/surveys` endpoint=`mobile_api.mobile_surveys`
- ['GET'] `/api/mobile/surveys/<int:survey_id>` endpoint=`mobile_api.mobile_survey_detail`
- ['POST'] `/api/mobile/surveys/<int:survey_id>/submit` endpoint=`mobile_api.mobile_survey_submit`

## Gate Sonu?lar?

### P3C personnel/kpi/communication
- Dosya: `tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py`
- Load OK: True
- False keys: `['ok', 'runtime_route_map_ok']`
- ?zet:
  - `direct_contract_ok`: `True`
  - `runtime_route_map_ok`: `False`
  - `response_code_smoke_ok`: `True`
  - `routes_py_lines`: `237`
  - `total_mobile_route_decorator_count`: `24`
- Report keys:
  - `['app_factory_ok', 'app_factory_smoke', 'compile_ok', 'compile_results', 'direct_contract_ok', 'expected_contract_route_count', 'inventory', 'next_actions', 'ok', 'package', 'pytest', 'pytest_mode', 'pytest_ok', 'report', 'response_code_smoke', 'response_code_smoke_ok', 'root', 'routes_py_lines', 'runtime_route_map', 'runtime_route_map_ok', 'secret_gate', 'secret_gate_finding_count', 'secret_gate_ok', 'total_mobile_route_decorator_count']`

### P3B auth/dashboard/assistant
- Dosya: `tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py`
- Load OK: True
- False keys: `['ok', 'runtime_route_map_ok']`
- ?zet:
  - `direct_contract_ok`: `True`
  - `runtime_route_map_ok`: `False`
  - `response_code_smoke_ok`: `True`
  - `compile_ok`: `True`
  - `app_factory_ok`: `True`
- Report keys:
  - `['app_factory_ok', 'app_factory_smoke', 'checks', 'compile_ok', 'compile_results', 'direct_contract_ok', 'inventory', 'next_actions', 'ok', 'package', 'pytest', 'pytest_mode', 'pytest_ok', 'report', 'response_code_smoke', 'response_code_smoke_mode', 'response_code_smoke_ok', 'root', 'routes_py_lines', 'runtime_route_map', 'runtime_route_map_ok', 'secret_gate', 'secret_gate_finding_count', 'secret_gate_ok', 'total_mobile_route_decorator_count']`

### P4C security suite
- Dosya: `scripts/quality/bys360_mobile_security_suite_gate_p4c.py`
- Load OK: True
- False keys: `['ok', 'p4_security_suite_ok', 'auth_guard_matrix_ok', 'role_boundary_matrix_ok']`
- ?zet:
  - `ok`: `False`
  - `p4_security_suite_ok`: `False`
  - `auth_guard_matrix_ok`: `False`
  - `role_boundary_matrix_ok`: `False`
  - `security_gate_count`: `2`
  - `security_gates_passed`: `0`
  - `total_probe_count`: `0`
  - `direct_contract_ok`: `True`
- Report keys:
  - `['app_factory_ok', 'app_factory_smoke', 'auth_guard_matrix_ok', 'ci_commands', 'compile_ok', 'compile_results', 'direct_contract_ok', 'expected_contract_route_count', 'generated_at', 'inventory', 'next_actions', 'ok', 'p4_security_suite_ok', 'package', 'pytest', 'pytest_mode', 'pytest_ok', 'report', 'role_boundary_matrix_ok', 'root', 'routes_py_lines', 'routes_py_under_300_lines', 'secret_gate', 'secret_gate_finding_count', 'secret_gate_ok', 'security_gate_count', 'security_gates_passed', 'security_suite', 'total_mobile_route_decorator_count', 'total_probe_count']`

### P4C V2 security suite
- Dosya: `scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py`
- Load OK: True
- False keys: `['ok', 'p4_security_suite_ok', 'auth_guard_matrix_ok', 'role_boundary_matrix_ok']`
- ?zet:
  - `ok`: `False`
  - `p4_security_suite_ok`: `False`
  - `auth_guard_matrix_ok`: `False`
  - `role_boundary_matrix_ok`: `False`
  - `security_gate_count`: `2`
  - `security_gates_passed`: `0`
  - `total_probe_count`: `0`
  - `direct_contract_ok`: `True`
- Report keys:
  - `['app_factory_ok', 'app_factory_smoke', 'auth_guard_matrix_ok', 'ci_commands', 'compile_ok', 'compile_results', 'direct_contract_ok', 'expected_contract_route_count', 'generated_at', 'inventory', 'next_actions', 'ok', 'p4_security_suite_ok', 'package', 'pytest', 'pytest_mode', 'pytest_ok', 'report', 'role_boundary_matrix_ok', 'root', 'routes_py_lines', 'routes_py_under_300_lines', 'secret_gate', 'secret_gate_finding_count', 'secret_gate_ok', 'security_gate_count', 'security_gates_passed', 'security_suite', 'total_mobile_route_decorator_count', 'total_probe_count']`
