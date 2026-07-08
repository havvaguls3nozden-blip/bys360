# BYS360 Faz 2C5 Next Low Risk Wildcard Batch Apply

Tarih: 2026-06-13T11:53:33

## Sonuç

- OK: True
- Karar: PHASE2C5_GREEN_LOW_RISK_BATCH_APPLIED
- Candidate count: 5
- Kept count: 4
- Rolled back count: 1
- Rollback all performed: False
- Before app AST wildcard count: 62
- After app AST wildcard count: 58
- Final default pytest returncode: 0
- Final default pytest summary: `{"passed": 746, "skipped": 2, "deselected": 34, "failed": 0, "errors": 0, "warnings": 0}`
- Backup root: `C:\bys360\releases\PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH_BACKUP_20260613_114541`
- Restore script: `C:\bys360\releases\PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH_BACKUP_20260613_114541\RESTORE_PHASE2C5_NEXT_LOW_RISK_WILDCARD_BATCH.ps1`

## Candidates

```json
[
  {
    "file": "app/institutional/hr_form_helpers.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "risk": "low",
    "status": "ready_for_explicit_import",
    "suggested_import_line": "from app.institutional.hr_common import Any, consume_form_token, date, db, flash, redirect, request, url_for, utc_now"
  },
  {
    "file": "app/institutional/hr_reports_routes.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "risk": "low",
    "status": "ready_for_explicit_import",
    "suggested_import_line": "from app.institutional.hr_common import Any, Response, csv, current_app, flash, io, jsonify, login_required, main_bp, manager_required, menu_key_required, or_, redirect, request, safe_db_rollback, safe_render"
  },
  {
    "file": "app/institutional/hr_scope_helpers.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "risk": "low",
    "status": "ready_for_explicit_import",
    "suggested_import_line": "from app.institutional.hr_common import ACTIVE_STATUSES, ATTENDANCE_TYPE_CHOICES, Any, DELEGATION_SCOPE_CHOICES, Iterable, LEAVE_TYPE_CHOICES, PERFORMANCE_MODE_LABELS, SimpleNamespace, current_user, date, datetime, db, request, safe_db_rollback"
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 9,
    "module": "app.institutional.hr_common",
    "risk": "low",
    "status": "ready_for_explicit_import",
    "suggested_import_line": "from app.institutional.hr_common import Any, date, login_required, main_bp, manager_required, menu_key_required, or_, safe_db_rollback, safe_render, timedelta"
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 140,
    "module": "app.institutional.hr_personnel_operations_routes",
    "risk": "low",
    "status": "ready_for_explicit_import",
    "suggested_import_line": "from app.institutional.hr_personnel_operations_routes import login_required, main_bp, manager_required, menu_key_required, safe_db_rollback, safe_render, timedelta"
  }
]
```

## Operations

```json
[
  {
    "file": "app/institutional/hr_form_helpers.py",
    "module": "app.institutional.hr_common",
    "changed": true,
    "old_line": "from app.institutional.hr_common import *  # noqa: F401,F403",
    "new_line": "from app.institutional.hr_common import Any, consume_form_token, date, db, flash, redirect, request, url_for, utc_now",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_returncode": 0,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      }
    }
  },
  {
    "file": "app/institutional/hr_reports_routes.py",
    "module": "app.institutional.hr_common",
    "changed": true,
    "old_line": "from app.institutional.hr_common import *  # noqa: F401,F403",
    "new_line": "from app.institutional.hr_common import Any, Response, csv, current_app, flash, io, jsonify, login_required, main_bp, manager_required, menu_key_required, or_, redirect, request, safe_db_rollback, safe_render",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_returncode": 0,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      }
    }
  },
  {
    "file": "app/institutional/hr_scope_helpers.py",
    "module": "app.institutional.hr_common",
    "changed": true,
    "old_line": "from app.institutional.hr_common import *  # noqa: F401,F403",
    "new_line": "from app.institutional.hr_common import ACTIVE_STATUSES, ATTENDANCE_TYPE_CHOICES, Any, DELEGATION_SCOPE_CHOICES, Iterable, LEAVE_TYPE_CHOICES, PERFORMANCE_MODE_LABELS, SimpleNamespace, current_user, date, datetime, db, request, safe_db_rollback",
    "kept": false,
    "gate": {
      "ok": false,
      "default_pytest_returncode": 1,
      "default_pytest_summary": {
        "errors": 28,
        "failed": 14,
        "passed": 702,
        "skipped": 4,
        "deselected": 34,
        "warnings": 0
      },
      "default_pytest_tail": "t_contract_ok\"] is True\n>       assert result[\"request_scenario_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_api_request_scenarios_p3a.py:17: AssertionError\n_____________________ test_mobile_api_response_suite_p3f ______________________\n\n    def test_mobile_api_response_suite_p3f() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(\n            root,\n            compile_all=False,\n            app_factory=False,\n            secret_gate_run=False,\n            pytest_gate=False,\n            write_report=False,\n        )\n>       assert result[\"p3_suite_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_api_response_suite_p3f.py:18: AssertionError\n_________________ test_mobile_api_role_boundary_matrix_p4b_v3 _________________\n\n    def test_mobile_api_role_boundary_matrix_p4b_v3() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(\n            root,\n            compile_all=True,\n            app_factory=True,\n            secret_gate_enabled=False,\n            pytest_gate_enabled=False,\n            write_report=False,\n        )\n        assert result[\"direct_contract_ok\"] is True\n>       assert result[\"runtime_route_map_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_api_role_boundary_matrix_p4b_v3.py:17: AssertionError\n_____________________ test_mobile_security_suite_gate_p4c _____________________\n\n    def test_mobile_security_suite_gate_p4c():\n        root = Path(__file__).resolve().parents[2]\n        module = _load_gate(root)\n    \n        class Args:\n            compile_all = False\n            app_factory = False\n            secret_gate = False\n            pytest_gate = False\n    \n        report = module.build_report(root, Args())\n>       assert report[\"ok\"], report\nE       AssertionError: {'app_factory_ok': True, 'app_factory_smoke': {'ok': True}, 'auth_guard_matrix_ok': False, 'ci_commands': ['python -m ...ality/bys360_mobile_security_suite_gate_p4c.py --root . --compile-all --app-factory --secret-gate --pytest-gate'], ...}\nE       assert False\n\ntests\\architecture\\test_mobile_api_security_suite_p4c.py:31: AssertionError\n___________________ test_mobile_security_suite_gate_p4c_v2 ____________________\n\n    def test_mobile_security_suite_gate_p4c_v2():\n        root = Path(__file__).resolve().parents[2]\n        module = _load_gate(root)\n    \n        class Args:\n            compile_all = False\n            app_factory = False\n            secret_gate = False\n            pytest_gate = False\n    \n        report = module.build_report(root, Args())\n>       assert report[\"ok\"], report\nE       AssertionError: {'app_factory_ok': True, 'app_factory_smoke': {'ok': True}, 'auth_guard_matrix_ok': False, 'ci_commands': ['python -m ...ty/bys360_mobile_security_suite_gate_p4c_v2.py --root . --compile-all --app-factory --secret-gate --pytest-gate'], ...}\nE       assert False\n\ntests\\architecture\\test_mobile_api_security_suite_p4c_v2.py:31: AssertionError\n_________ test_mobile_support_survey_notifications_response_gate_p3d __________\n\n    def test_mobile_support_survey_notifications_response_gate_p3d() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(\n            root,\n            compile_all=False,\n            app_factory=False,\n            secret_gate_run=False,\n            pytest_gate=False,\n            write_report=False,\n        )\n        assert result[\"direct_contract_ok\"] is True\n>       assert result[\"runtime_route_map_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_api_support_survey_notifications_response_p3d.py:19: AssertionError\n___________ test_mobile_auth_dashboard_assistant_response_gate_p3b ____________\n\n    def test_mobile_auth_dashboard_assistant_response_gate_p3b() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(root, compile_all=True, app_factory=True, secret_gate=False, pytest_gate=False, write_report=False)\n        assert result[\"direct_contract_ok\"] is True\n>       assert (\n            result[\"runtime_route_map_ok\"] is True\n            or (\n                result.get(\"direct_contract_ok\") is True\n                and result.get(\"response_code_smoke_ok\") is True\n                and result.get(\"total_mobile_route_decorator_count\", 0) >= 24\n            )\n        ), result.get(\"runtime_route_map\", result)\nE       AssertionError: {'cmd': ['C:\\\\bys360\\\\project\\\\.venv\\\\Scripts\\\\python.exe', '-c', '\nE         import json\nE         from app import create_app\nE         app = cr...bile/me', 'GET /api/mobile/dashboard/summary', 'POST /api/mobile/assistant/v2/ask'], 'ok': False, 'returncode': 1, ...}\nE       assert (False is True or (True is True and False is True))\nE        +  where True = <built-in method get of dict object at 0x000001D347463F80>('direct_contract_ok')\nE        +    where <built-in method get of dict object at 0x000001D347463F80> = {'app_factory_ok': False, 'app_factory_smoke': {'cmd': ['C:\\\\bys360\\\\project\\\\.venv\\\\Scripts\\\\python.exe', '-c', \"from...p_factory_ok': False, 'compile_ok': True, 'direct_contract_ok': True, 'pytest_ok': True, ...}, 'compile_ok': True, ...}.get\nE        +  and   False = <built-in method get of dict object at 0x000001D347463F80>('response_code_smoke_ok')\nE        +    where <built-in method get of dict object at 0x000001D347463F80> = {'app_factory_ok': False, 'app_factory_smoke': {'cmd': ['C:\\\\bys360\\\\project\\\\.venv\\\\Scripts\\\\python.exe', '-c', \"from...p_factory_ok': False, 'compile_ok': True, 'direct_contract_ok': True, 'pytest_ok': True, ...}, 'compile_ok': True, ...}.get\n\ntests\\architecture\\test_mobile_auth_dashboard_assistant_response_p3b.py:14: AssertionError\n__________ test_mobile_auth_dashboard_assistant_response_gate_p3b_v2 __________\n\n    def test_mobile_auth_dashboard_assistant_response_gate_p3b_v2() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(root, compile_all=True, app_factory=True, secret_gate=False, pytest_gate=False, write_report=False)\n        assert result[\"direct_contract_ok\"] is True\n>       assert result[\"runtime_route_map_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_auth_dashboard_assistant_response_p3b_v2.py:12: AssertionError\n=========================== short test summary info ===========================\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\critical\\test_v59_broad_route_smoke.py:74: BYS360 uygulaması test modunda başlatılamadı: name '_safe_import' is not defined\nSKIPPED [1] tests\\test_sp_routes_smoke.py:37: Flask uygulaması test client için yüklenemedi: name '_safe_import' is not defined\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_assistant_context_processors_are_registered\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/dashboard]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/dashboard/heavy-panels]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/settings]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/feedback-pipeline]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/feedback-corporate-cleanup]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/process-tracking]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/process-reports]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/president-approvals/1/card]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/feedback-aftercare]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_critical_routes_never_return_500[/performance/feedback-final-gate]\nERROR tests/critical/test_v58_claude_roadmap_smoke.py::test_v58_smoke_route_count_contract\nERROR tests/critical/test_v59_4_assistant_shortcut_context.py::test_v59_4_assistant_shortcut_context_keys_are_always_available\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback]\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback/pulse]\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback/pulse/history]\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback/pulse/analytics]\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback/admin/pulse-analytics]\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback/campaigns]\nERROR tests/integration/test_feedback_http_behavior.py::test_feedback_routes_exist_and_do_not_500[/feedback/results]\nERROR tests/performance/test_critical_performance_routes_smoke.py::test_feedback_pipeline_loads_without_500\nERROR tests/performance/test_critical_performance_routes_smoke.py::test_feedback_corporate_cleanup_no_500\nERROR tests/performance/test_critical_performance_routes_smoke.py::test_process_tracking_no_500\nERROR tests/performance/test_critical_performance_routes_smoke.py::test_process_reports_no_500\nERROR tests/performance/test_critical_performance_routes_smoke.py::test_president_approval_card_no_500\nERROR tests/test_ai_routes.py::test_run_json_service_success - NameError: nam...\nERROR tests/test_ai_routes.py::test_run_json_service_maps_403 - NameError: na...\nERROR tests/test_ai_routes.py::test_run_json_service_maps_503 - NameError: na...\nFAILED tests/architecture/test_android_responsive_core_styles_p5b.py::test_android_responsive_core_styles_gate_p5b\nFAILED tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py::test_mobile_auth_dashboard_assistant_response_gate_p3b_v3\nFAILED tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py::test_mobile_api_auth_guard_matrix_p4a\nFAILED tests/architecture/test_mobile_api_performance_response_p3e.py::test_mobile_performance_response_gate_p3e\nFAILED tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py::test_mobile_personnel_kpi_communication_response_gate_p3c\nFAILED tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py::test_mobile_personnel_kpi_communication_response_gate_p3c_v2\nFAILED tests/architecture/test_mobile_api_request_scenarios_p3a.py::test_mobile_api_request_scenario_gate_p3a\nFAILED tests/architecture/test_mobile_api_response_suite_p3f.py::test_mobile_api_response_suite_p3f\nFAILED tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v3.py::test_mobile_api_role_boundary_matrix_p4b_v3\nFAILED tests/architecture/test_mobile_api_security_suite_p4c.py::test_mobile_security_suite_gate_p4c\nFAILED tests/architecture/test_mobile_api_security_suite_p4c_v2.py::test_mobile_security_suite_gate_p4c_v2\nFAILED tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py::test_mobile_support_survey_notifications_response_gate_p3d\nFAILED tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py::test_mobile_auth_dashboard_assistant_response_gate_p3b\nFAILED tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b_v2.py::test_mobile_auth_dashboard_assistant_response_gate_p3b_v2\n14 failed, 702 passed, 4 skipped, 34 deselected, 28 errors in 33.76s\n\n"
    }
  },
  {
    "file": "app/institutional/routes.py",
    "module": "app.institutional.hr_common",
    "changed": true,
    "old_line": "from app.institutional.hr_common import *  # noqa: F401,F403",
    "new_line": "from app.institutional.hr_common import Any, date, login_required, main_bp, manager_required, menu_key_required, or_, safe_db_rollback, safe_render, timedelta",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_returncode": 0,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      }
    }
  },
  {
    "file": "app/institutional/routes.py",
    "module": "app.institutional.hr_personnel_operations_routes",
    "changed": true,
    "old_line": "from app.institutional.hr_personnel_operations_routes import *  # noqa: E402,F401,F403",
    "new_line": "from app.institutional.hr_personnel_operations_routes import login_required, main_bp, manager_required, menu_key_required, safe_db_rollback, safe_render, timedelta",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_returncode": 0,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      }
    }
  }
]
```

## Before Wildcard By Module Top 50

```json
{
  "app.services.ai.dashboard_panel_common": 6,
  "app.institutional.hr_common": 5,
  "app.services.mail_core": 4,
  "app.institutional.hr_form_helpers": 3,
  "app.institutional.hr_scope_helpers": 3,
  "app.main_handlers.account_communication_helpers": 3,
  "app.services.mail_performance_builder": 2,
  "app.api.mobile.shared": 1,
  "app.api.mobile.domains.auth": 1,
  "app.api.mobile.domains.dashboard": 1,
  "app.api.mobile.domains.personnel_read": 1,
  "app.api.mobile.domains.notifications": 1,
  "app.api.mobile.domains.support_survey_write": 1,
  "app.api.mobile.domains.communication_v1_write": 1,
  "app.api.mobile.domains.communication_v2_write": 1,
  "app.api.mobile.domains.assistant_chat": 1,
  "app.api.mobile.domains.personnel_write_all": 1,
  "app.api.mobile.domains.kpi_target_management": 1,
  "app.institutional.org_unit_routes": 1,
  "app.institutional.hr_personnel_operations_routes": 1,
  "app.institutional.hr_leave_attendance_routes": 1,
  "app.institutional.hr_reports_routes": 1,
  "app.main_handlers.account_visibility_helpers": 1,
  "feedback_helpers": 1,
  "mail_helpers": 1,
  "publish_helpers": 1,
  "maintenance_merge_registry": 1,
  "schema_guard_core_maintenances": 1,
  "dashboard_panels": 1,
  "app.services.ai.dashboard_panel_performance": 1,
  "app.services.ai.dashboard_panel_personnel": 1,
  "app.services.ai.dashboard_panel_hr": 1,
  "app.services.ai.dashboard_panel_communication": 1,
  "app.services.ai.dashboard_panel_operations": 1,
  "app.services.mail_performance_sender": 1,
  "app.services.mail_feedback": 1,
  "common_admin_scope_maintenance": 1,
  "app.performance.services.performance_rule_engine": 1,
  "app.services.performance.phase3_role_matrix": 1,
  "constants": 1,
  "state": 1,
  "transitions": 1,
  "visibility": 1
}
```

## After Wildcard By Module Top 50

```json
{
  "app.services.ai.dashboard_panel_common": 6,
  "app.services.mail_core": 4,
  "app.institutional.hr_form_helpers": 3,
  "app.institutional.hr_scope_helpers": 3,
  "app.main_handlers.account_communication_helpers": 3,
  "app.institutional.hr_common": 2,
  "app.services.mail_performance_builder": 2,
  "app.api.mobile.shared": 1,
  "app.api.mobile.domains.auth": 1,
  "app.api.mobile.domains.dashboard": 1,
  "app.api.mobile.domains.personnel_read": 1,
  "app.api.mobile.domains.notifications": 1,
  "app.api.mobile.domains.support_survey_write": 1,
  "app.api.mobile.domains.communication_v1_write": 1,
  "app.api.mobile.domains.communication_v2_write": 1,
  "app.api.mobile.domains.assistant_chat": 1,
  "app.api.mobile.domains.personnel_write_all": 1,
  "app.api.mobile.domains.kpi_target_management": 1,
  "app.institutional.org_unit_routes": 1,
  "app.institutional.hr_leave_attendance_routes": 1,
  "app.institutional.hr_reports_routes": 1,
  "app.main_handlers.account_visibility_helpers": 1,
  "feedback_helpers": 1,
  "mail_helpers": 1,
  "publish_helpers": 1,
  "maintenance_merge_registry": 1,
  "schema_guard_core_maintenances": 1,
  "dashboard_panels": 1,
  "app.services.ai.dashboard_panel_performance": 1,
  "app.services.ai.dashboard_panel_personnel": 1,
  "app.services.ai.dashboard_panel_hr": 1,
  "app.services.ai.dashboard_panel_communication": 1,
  "app.services.ai.dashboard_panel_operations": 1,
  "app.services.mail_performance_sender": 1,
  "app.services.mail_feedback": 1,
  "common_admin_scope_maintenance": 1,
  "app.performance.services.performance_rule_engine": 1,
  "app.services.performance.phase3_role_matrix": 1,
  "constants": 1,
  "state": 1,
  "transitions": 1,
  "visibility": 1
}
```

## Final Gate

```json
{
  "label": "final_after_phase2c5",
  "ok": true,
  "compileall_returncode": 0,
  "contract_pytest_returncode": 0,
  "contract_pytest_summary": {
    "passed": 2,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0,
    "warnings": 0
  },
  "auth_guard_pytest_returncode": 0,
  "auth_guard_pytest_summary": {
    "passed": 1,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0,
    "warnings": 0
  },
  "quality_smoke_returncode": 0,
  "quality_smoke_summary": {
    "passed": 5,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0,
    "warnings": 0
  },
  "default_pytest_returncode": 0,
  "default_pytest_summary": {
    "passed": 746,
    "skipped": 2,
    "deselected": 34,
    "failed": 0,
    "errors": 0,
    "warnings": 0
  },
  "default_pytest_tail": "......ss................................................................ [  9%]\n........................................................................ [ 19%]\n........................................................................ [ 28%]\n........................................................................ [ 38%]\n........................................................................ [ 48%]\n........................................................................ [ 57%]\n........................................................................ [ 67%]\n........................................................................ [ 77%]\n........................................................................ [ 86%]\n........................................................................ [ 96%]\n............................                                             [100%]\n=========================== short test summary info ===========================\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.\n746 passed, 2 skipped, 34 deselected in 41.88s\n\n"
}
```

## Sonraki Adım

Faz 2C6 kalan wildcard sınıflandırma raporuna geçilebilir.