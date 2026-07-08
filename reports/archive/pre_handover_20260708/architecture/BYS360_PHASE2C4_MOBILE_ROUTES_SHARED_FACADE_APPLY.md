# BYS360 Faz 2C4 Mobile Routes Shared Facade Apply

Tarih: 2026-06-13T11:35:35

## Sonuç

- OK: False
- Karar: PHASE2C4_ROUTES_FACADE_RESTORED_OR_REVIEW_REQUIRED
- Target: `app/api/mobile/routes.py`
- Backup root: `C:\bys360\releases\PHASE2C4_MOBILE_ROUTES_SHARED_FACADE_BACKUP_20260613_113301`
- Restore script: `C:\bys360\releases\PHASE2C4_MOBILE_ROUTES_SHARED_FACADE_BACKUP_20260613_113301\RESTORE_PHASE2C4_MOBILE_ROUTES_SHARED_FACADE.ps1`
- Candidate count: 11
- Changed: True
- Rollback performed: True
- Before app AST wildcard count: 62
- After app AST wildcard count: 62
- Before mobile shared remaining: 1
- After mobile shared remaining: 1
- Routes has shared wildcard: True
- Routes has shared explicit: False
- Final default pytest returncode: 0
- Final default pytest summary: `{"passed": 746, "skipped": 2, "deselected": 34, "failed": 0, "errors": 0, "warnings": 0}`

## Candidate

```json
{
  "candidate_names": [
    "User",
    "_full_name",
    "_has_global_scope",
    "_item",
    "_metric",
    "_safe_count",
    "jsonify",
    "mobile_api_bp",
    "request",
    "user",
    "value"
  ],
  "candidate_count": 11,
  "candidate_import_line": "from app.api.mobile.shared import User, _full_name, _has_global_scope, _item, _metric, _safe_count, jsonify, mobile_api_bp, request, user, value"
}
```

## Operation

```json
{
  "changed": true,
  "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - P1B endpoint sözleşmesi için bilinçli facade import",
  "new_line": "from app.api.mobile.shared import User, _full_name, _has_global_scope, _item, _metric, _safe_count, jsonify, mobile_api_bp, request, user, value"
}
```

## After Gate

```json
{
  "label": "after_routes_facade_apply",
  "ok": false,
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
  "auth_guard_pytest_returncode": 1,
  "auth_guard_pytest_summary": {
    "warnings": 0,
    "failed": 1,
    "passed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0
  },
  "default_pytest_returncode": 1,
  "default_pytest_summary": {
    "warnings": 0,
    "failed": 13,
    "passed": 733,
    "skipped": 2,
    "deselected": 34,
    "errors": 0
  },
  "default_pytest_tail": ".performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.\nINFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1\nINFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.\nERROR    app:__init__.py:61 BYS360 optional startup component failed: Mobile real API routes\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 59, in _run_optional_startup\n    callback()\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 188, in <lambda>\n    _run_optional_startup(app, \"Mobile real API routes\", lambda: _register_mobile_api(app))\n                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 158, in _register_mobile_api\n    from app.api.mobile import register_mobile_api_real_v1\n  File \"C:\\bys360\\project\\app\\api\\mobile\\__init__.py\", line 10, in <module>\n    from . import routes  # noqa: E402,F401\n    ^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\routes.py\", line 7, in <module>\n    from app.api.mobile.shared import User, _full_name, _has_global_scope, _item, _metric, _safe_count, jsonify, mobile_api_bp, request, user, value\nImportError: cannot import name 'user' from 'app.api.mobile.shared' (C:\\bys360\\project\\app\\api\\mobile\\shared.py). Did you mean: 'User'?\n_________ test_mobile_support_survey_notifications_response_gate_p3d __________\n\n    def test_mobile_support_survey_notifications_response_gate_p3d() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(\n            root,\n            compile_all=False,\n            app_factory=False,\n            secret_gate_run=False,\n            pytest_gate=False,\n            write_report=False,\n        )\n        assert result[\"direct_contract_ok\"] is True\n>       assert result[\"runtime_route_map_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_api_support_survey_notifications_response_p3d.py:19: AssertionError\n------------------------------ Captured log call ------------------------------\nWARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.\nINFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3\nINFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.\nINFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1\nINFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.\nERROR    app:__init__.py:61 BYS360 optional startup component failed: Mobile real API routes\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 59, in _run_optional_startup\n    callback()\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 188, in <lambda>\n    _run_optional_startup(app, \"Mobile real API routes\", lambda: _register_mobile_api(app))\n                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 158, in _register_mobile_api\n    from app.api.mobile import register_mobile_api_real_v1\n  File \"C:\\bys360\\project\\app\\api\\mobile\\__init__.py\", line 10, in <module>\n    from . import routes  # noqa: E402,F401\n    ^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\routes.py\", line 7, in <module>\n    from app.api.mobile.shared import User, _full_name, _has_global_scope, _item, _metric, _safe_count, jsonify, mobile_api_bp, request, user, value\nImportError: cannot import name 'user' from 'app.api.mobile.shared' (C:\\bys360\\project\\app\\api\\mobile\\shared.py). Did you mean: 'User'?\nWARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.\nINFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3\nINFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.\nINFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1\nINFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.\nERROR    app:__init__.py:61 BYS360 optional startup component failed: Mobile real API routes\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 59, in _run_optional_startup\n    callback()\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 188, in <lambda>\n    _run_optional_startup(app, \"Mobile real API routes\", lambda: _register_mobile_api(app))\n                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 158, in _register_mobile_api\n    from app.api.mobile import register_mobile_api_real_v1\n  File \"C:\\bys360\\project\\app\\api\\mobile\\__init__.py\", line 10, in <module>\n    from . import routes  # noqa: E402,F401\n    ^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\routes.py\", line 7, in <module>\n    from app.api.mobile.shared import User, _full_name, _has_global_scope, _item, _metric, _safe_count, jsonify, mobile_api_bp, request, user, value\nImportError: cannot import name 'user' from 'app.api.mobile.shared' (C:\\bys360\\project\\app\\api\\mobile\\shared.py). Did you mean: 'User'?\nWARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.\nINFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3\nINFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.\nINFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1\nINFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.\nERROR    app:__init__.py:61 BYS360 optional startup component failed: Mobile real API routes\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 59, in _run_optional_startup\n    callback()\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 188, in <lambda>\n    _run_optional_startup(app, \"Mobile real API routes\", lambda: _register_mobile_api(app))\n                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\__init__.py\", line 158, in _register_mobile_api\n    from app.api.mobile import register_mobile_api_real_v1\n  File \"C:\\bys360\\project\\app\\api\\mobile\\__init__.py\", line 10, in <module>\n    from . import routes  # noqa: E402,F401\n    ^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\routes.py\", line 7, in <module>\n    from app.api.mobile.shared import User, _full_name, _has_global_scope, _item, _metric, _safe_count, jsonify, mobile_api_bp, request, user, value\nImportError: cannot import name 'user' from 'app.api.mobile.shared' (C:\\bys360\\project\\app\\api\\mobile\\shared.py). Did you mean: 'User'?\n___________ test_mobile_auth_dashboard_assistant_response_gate_p3b ____________\n\n    def test_mobile_auth_dashboard_assistant_response_gate_p3b() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(root, compile_all=True, app_factory=True, secret_gate=False, pytest_gate=False, write_report=False)\n        assert result[\"direct_contract_ok\"] is True\n>       assert (\n            result[\"runtime_route_map_ok\"] is True\n            or (\n                result.get(\"direct_contract_ok\") is True\n                and result.get(\"response_code_smoke_ok\") is True\n                and result.get(\"total_mobile_route_decorator_count\", 0) >= 24\n            )\n        ), result.get(\"runtime_route_map\", result)\nE       AssertionError: {'cmd': ['C:\\\\bys360\\\\project\\\\.venv\\\\Scripts\\\\python.exe', '-c', '\nE         import json\nE         from app import create_app\nE         app = cr...bile/me', 'GET /api/mobile/dashboard/summary', 'POST /api/mobile/assistant/v2/ask'], 'ok': False, 'returncode': 0, ...}\nE       assert (False is True or (True is True and False is True))\nE        +  where True = <built-in method get of dict object at 0x00000203C211BFC0>('direct_contract_ok')\nE        +    where <built-in method get of dict object at 0x00000203C211BFC0> = {'app_factory_ok': True, 'app_factory_smoke': {'cmd': ['C:\\\\bys360\\\\project\\\\.venv\\\\Scripts\\\\python.exe', '-c', \"from ...pp_factory_ok': True, 'compile_ok': True, 'direct_contract_ok': True, 'pytest_ok': True, ...}, 'compile_ok': True, ...}.get\nE        +  and   False = <built-in method get of dict object at 0x00000203C211BFC0>('response_code_smoke_ok')\nE        +    where <built-in method get of dict object at 0x00000203C211BFC0> = {'app_factory_ok': True, 'app_factory_smoke': {'cmd': ['C:\\\\bys360\\\\project\\\\.venv\\\\Scripts\\\\python.exe', '-c', \"from ...pp_factory_ok': True, 'compile_ok': True, 'direct_contract_ok': True, 'pytest_ok': True, ...}, 'compile_ok': True, ...}.get\n\ntests\\architecture\\test_mobile_auth_dashboard_assistant_response_p3b.py:14: AssertionError\n__________ test_mobile_auth_dashboard_assistant_response_gate_p3b_v2 __________\n\n    def test_mobile_auth_dashboard_assistant_response_gate_p3b_v2() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(root, compile_all=True, app_factory=True, secret_gate=False, pytest_gate=False, write_report=False)\n        assert result[\"direct_contract_ok\"] is True\n>       assert result[\"runtime_route_map_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_auth_dashboard_assistant_response_p3b_v2.py:12: AssertionError\n=========================== short test summary info ===========================\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.\nFAILED tests/architecture/test_mobile_api_auth_dashboard_assistant_response_p3b_v3.py::test_mobile_auth_dashboard_assistant_response_gate_p3b_v3\nFAILED tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py::test_mobile_api_auth_guard_matrix_p4a\nFAILED tests/architecture/test_mobile_api_performance_response_p3e.py::test_mobile_performance_response_gate_p3e\nFAILED tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c.py::test_mobile_personnel_kpi_communication_response_gate_p3c\nFAILED tests/architecture/test_mobile_api_personnel_kpi_communication_response_p3c_v2.py::test_mobile_personnel_kpi_communication_response_gate_p3c_v2\nFAILED tests/architecture/test_mobile_api_request_scenarios_p3a.py::test_mobile_api_request_scenario_gate_p3a\nFAILED tests/architecture/test_mobile_api_response_suite_p3f.py::test_mobile_api_response_suite_p3f\nFAILED tests/architecture/test_mobile_api_role_boundary_matrix_p4b_v3.py::test_mobile_api_role_boundary_matrix_p4b_v3\nFAILED tests/architecture/test_mobile_api_security_suite_p4c.py::test_mobile_security_suite_gate_p4c\nFAILED tests/architecture/test_mobile_api_security_suite_p4c_v2.py::test_mobile_security_suite_gate_p4c_v2\nFAILED tests/architecture/test_mobile_api_support_survey_notifications_response_p3d.py::test_mobile_support_survey_notifications_response_gate_p3d\nFAILED tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b.py::test_mobile_auth_dashboard_assistant_response_gate_p3b\nFAILED tests/architecture/test_mobile_auth_dashboard_assistant_response_p3b_v2.py::test_mobile_auth_dashboard_assistant_response_gate_p3b_v2\n13 failed, 733 passed, 2 skipped, 34 deselected in 42.45s\n\n"
}
```

## Final Gate

```json
{
  "label": "final_after_possible_restore",
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
  "default_pytest_returncode": 0,
  "default_pytest_summary": {
    "passed": 746,
    "skipped": 2,
    "deselected": 34,
    "failed": 0,
    "errors": 0,
    "warnings": 0
  },
  "default_pytest_tail": "......ss................................................................ [  9%]\n........................................................................ [ 19%]\n........................................................................ [ 28%]\n........................................................................ [ 38%]\n........................................................................ [ 48%]\n........................................................................ [ 57%]\n........................................................................ [ 67%]\n........................................................................ [ 77%]\n........................................................................ [ 86%]\n........................................................................ [ 96%]\n............................                                             [100%]\n=========================== short test summary info ===========================\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.\n746 passed, 2 skipped, 34 deselected in 40.81s\n\n"
}
```

## Sonraki Adım

routes.py facade wildcard bilinçli istisna olarak bırakılmalı veya eksik isimler rapordan elle eklenmeli.