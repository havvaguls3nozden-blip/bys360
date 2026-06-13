# BYS360 Faz 2C2D One-by-One Full Gate Apply

Tarih: 2026-06-13T11:15:11

## Sonuç

- OK: True
- Karar: PHASE2C2D_GREEN_PARTIAL_SAFE_APPLY
- Backup root: `C:\bys360\releases\PHASE2C2D_ONE_BY_ONE_FULL_GATE_BACKUP_20260613_110534`
- Restore script: `C:\bys360\releases\PHASE2C2D_ONE_BY_ONE_FULL_GATE_BACKUP_20260613_110534\RESTORE_PHASE2C2D_ONE_BY_ONE_FULL_GATE.ps1`
- Skipped files: `app/api/mobile/routes.py`
- Candidate count: 10
- Kept count: 9
- Rolled back count: 1
- Final default pytest returncode: 0

## Operations

```json
[
  {
    "file": "app/api/mobile/domains/assistant_chat.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu",
    "new_line": "from app.api.mobile.shared import EvaluationAssignment, Notification, SupportTicket, User, jsonify, mobile_api_bp, request, require_mobile_user",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/auth.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import User, mobile_api_bp, mobile_login_response, mobile_me_response, mobile_refresh_response, request, require_mobile_user",
    "kept": false,
    "gate": {
      "ok": false,
      "default_pytest_summary": {
        "warnings": 0,
        "errors": 500,
        "failed": 1,
        "passed": 745,
        "skipped": 2,
        "deselected": 34
      },
      "default_pytest_returncode": 1,
      "default_pytest_tail": "......ss...............................................F................ [  9%]\n........................................................................ [ 19%]\n........................................................................ [ 28%]\n........................................................................ [ 38%]\n........................................................................ [ 48%]\n........................................................................ [ 57%]\n........................................................................ [ 67%]\n........................................................................ [ 77%]\n........................................................................ [ 86%]\n........................................................................ [ 96%]\n............................                                             [100%]\n================================== FAILURES ===================================\n____________________ test_mobile_api_auth_guard_matrix_p4a ____________________\n\n    def test_mobile_api_auth_guard_matrix_p4a() -> None:\n        root = Path(__file__).resolve().parents[2]\n        result = run_checks(\n            root,\n            compile_all=True,\n            app_factory=True,\n            secret_gate_enabled=False,\n            pytest_gate_enabled=False,\n            write_report=False,\n        )\n        assert result[\"direct_contract_ok\"] is True\n        assert result[\"runtime_route_map_ok\"] is True\n>       assert result[\"auth_guard_matrix_ok\"] is True\nE       assert False is True\n\ntests\\architecture\\test_mobile_api_auth_guard_matrix_p4a.py:18: AssertionError\n------------------------------ Captured log call ------------------------------\nWARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.\nINFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3\nINFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.\nINFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1\nINFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.\nWARNING  app:monitoring.py:44 Sentry DSN tanimli degil; hata izleme kapali.\nINFO     app:startup.py:46 Startup ozeti | env=testing | db=sqlite | maintenance=off | route_count=6 | schema_errors=0 | core_scope=7 | removed_scope=3\nINFO     app.services.performance.feedback_followup_scheduler:feedback_followup_scheduler.py:51 BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.\nINFO     app:audit.py:196 Guvenlik ozeti | critical=0 warning=0 info=1\nINFO     app:startup_checks.py:62 Schema validation SQLite duman/test ortamında pas geçildi.\nERROR    app:error_handlers.py:308 Beklenmeyen hata yakalandi: name '_issue_token' is not defined | detay={'request_id': 'c2bba0b719775b10', 'method': 'POST', 'path': '/api/mobile/auth/login', 'full_path': '/api/mobile/auth/login?', 'endpoint': 'mobile_api.mobile_login', 'ip': '127.0.0.1', 'remote_addr': '127.0.0.1', 'referer': '-', 'origin': '-', 'user_agent': 'Werkzeug/3.1.8', 'content_type': 'application/json', 'content_length': 30}\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\.venv\\Lib\\site-packages\\flask\\app.py\", line 917, in full_dispatch_request\n    rv = self.dispatch_request()\n         ^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\.venv\\Lib\\site-packages\\flask\\app.py\", line 902, in dispatch_request\n    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\domains\\auth.py\", line 14, in mobile_login\n    return delegate_mobile_login(_bys360_legacy_mobile_login)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\services\\auth_service.py\", line 108, in delegate_mobile_login\n    return _run_legacy_route(legacy_fn, *args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\services\\auth_service.py\", line 102, in _run_legacy_route\n    return legacy_fn(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\domains\\auth.py\", line 17, in _bys360_legacy_mobile_login\n    return mobile_login_response(_issue_token, _issue_refresh_token, _full_name)\n                                 ^^^^^^^^^^^^\nNameError: name '_issue_token' is not defined\nERROR    app:operational_guards.py:196 5xx yanit verildi: POST /api/mobile/auth/login -> 500\nERROR    app:error_handlers.py:308 Beklenmeyen hata yakalandi: name '_load_refresh_token_user' is not defined | detay={'request_id': 'f53b3dfe9039b51f', 'method': 'POST', 'path': '/api/mobile/auth/refresh', 'full_path': '/api/mobile/auth/refresh?', 'endpoint': 'mobile_api.mobile_refresh', 'ip': '127.0.0.1', 'remote_addr': '127.0.0.1', 'referer': '-', 'origin': '-', 'user_agent': 'Werkzeug/3.1.8', 'content_type': 'application/json', 'content_length': 30}\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\.venv\\Lib\\site-packages\\flask\\app.py\", line 917, in full_dispatch_request\n    rv = self.dispatch_request()\n         ^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\.venv\\Lib\\site-packages\\flask\\app.py\", line 902, in dispatch_request\n    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\domains\\auth.py\", line 23, in mobile_refresh\n    return delegate_mobile_refresh(_bys360_legacy_mobile_refresh)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\services\\auth_service.py\", line 114, in delegate_mobile_refresh\n    return _run_legacy_route(legacy_fn, *args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\services\\auth_service.py\", line 102, in _run_legacy_route\n    return legacy_fn(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\domains\\auth.py\", line 28, in _bys360_legacy_mobile_refresh\n    return mobile_refresh_response(refresh_token, _load_refresh_token_user, _issue_token, _issue_refresh_token, _full_name)\n                                                  ^^^^^^^^^^^^^^^^^^^^^^^^\nNameError: name '_load_refresh_token_user' is not defined\nERROR    app:operational_guards.py:196 5xx yanit verildi: POST /api/mobile/auth/refresh -> 500\nERROR    app:error_handlers.py:308 Beklenmeyen hata yakalandi: name '_load_refresh_token_user' is not defined | detay={'request_id': '3bac21799c65e455', 'method': 'POST', 'path': '/api/mobile/auth/refresh', 'full_path': '/api/mobile/auth/refresh?', 'endpoint': 'mobile_api.mobile_refresh', 'ip': '127.0.0.1', 'remote_addr': '127.0.0.1', 'referer': '-', 'origin': '-', 'user_agent': 'Werkzeug/3.1.8', 'content_type': 'application/json', 'content_length': 30}\nTraceback (most recent call last):\n  File \"C:\\bys360\\project\\.venv\\Lib\\site-packages\\flask\\app.py\", line 917, in full_dispatch_request\n    rv = self.dispatch_request()\n         ^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\.venv\\Lib\\site-packages\\flask\\app.py\", line 902, in dispatch_request\n    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\domains\\auth.py\", line 23, in mobile_refresh\n    return delegate_mobile_refresh(_bys360_legacy_mobile_refresh)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\services\\auth_service.py\", line 114, in delegate_mobile_refresh\n    return _run_legacy_route(legacy_fn, *args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\services\\auth_service.py\", line 102, in _run_legacy_route\n    return legacy_fn(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"C:\\bys360\\project\\app\\api\\mobile\\domains\\auth.py\", line 28, in _bys360_legacy_mobile_refresh\n    return mobile_refresh_response(refresh_token, _load_refresh_token_user, _issue_token, _issue_refresh_token, _full_name)\n                                                  ^^^^^^^^^^^^^^^^^^^^^^^^\nNameError: name '_load_refresh_token_user' is not defined\nERROR    app:operational_guards.py:196 5xx yanit verildi: POST /api/mobile/auth/refresh -> 500\n=========================== short test summary info ===========================\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.\nFAILED tests/architecture/test_mobile_api_auth_guard_matrix_p4a.py::test_mobile_api_auth_guard_matrix_p4a\n1 failed, 745 passed, 2 skipped, 34 deselected in 41.23s\n\n"
    }
  },
  {
    "file": "app/api/mobile/domains/communication_v1_write.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu",
    "new_line": "from app.api.mobile.shared import MessageThread, MessageThreadParticipant, User, datetime, db, jsonify, mobile_api_bp, request, require_mobile_user, timezone",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/communication_v2_write.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu",
    "new_line": "from app.api.mobile.shared import MessageThread, MessageThreadParticipant, User, current_app, datetime, db, jsonify, mobile_api_bp, request, require_mobile_user, timezone",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/dashboard.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import AIRecommendation, EvaluationAssignment, MessageThreadParticipant, Notification, PerformancePresidentApproval, SupportTicket, User, db, jsonify, mean, mobile_api_bp, require_mobile_user",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/kpi_target_management.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1E domain endpoint importu",
    "new_line": "from app.api.mobile.shared import User, db, jsonify, mean, mobile_api_bp, request, require_mobile_user",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/notifications.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import Notification, User, datetime, db, jsonify, mobile_api_bp, require_mobile_user, timezone",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/personnel_read.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import User, mobile_api_bp, require_mobile_user",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/personnel_write_all.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1E domain endpoint importu",
    "new_line": "from app.api.mobile.shared import Any, IntegrityError, User, current_app, db, get_default_first_login_password, jsonify, mobile_api_bp, request, require_mobile_user",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  },
  {
    "file": "app/api/mobile/domains/support_survey_write.py",
    "changed": true,
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import Any, SupportTicket, SupportTicketMessage, SupportTicketStatusHistory, Survey, SurveyAnswer, SurveyResponse, User, datetime, db, jsonify, mobile_api_bp, notify_support_ticket_comment, notify_support_ticket_created, request, require_mobile_user, timezone",
    "kept": true,
    "gate": {
      "ok": true,
      "default_pytest_summary": {
        "passed": 746,
        "skipped": 2,
        "deselected": 34,
        "failed": 0,
        "errors": 0,
        "warnings": 0
      },
      "default_pytest_returncode": 0
    }
  }
]
```

## Final Target Status

```json
[
  {
    "file": "app/api/mobile/domains/assistant_chat.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/auth.py",
    "has_mobile_shared_wildcard": true,
    "has_explicit_mobile_shared_import": false
  },
  {
    "file": "app/api/mobile/domains/communication_v1_write.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/communication_v2_write.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/dashboard.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/kpi_target_management.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/notifications.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/personnel_read.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/personnel_write_all.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  },
  {
    "file": "app/api/mobile/domains/support_survey_write.py",
    "has_mobile_shared_wildcard": false,
    "has_explicit_mobile_shared_import": true
  }
]
```

## Final Gate After Possible Restore

```json
{
  "label": "final_after_phase2c2d",
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
  "default_pytest_tail": "......ss................................................................ [  9%]\n........................................................................ [ 19%]\n........................................................................ [ 28%]\n........................................................................ [ 38%]\n........................................................................ [ 48%]\n........................................................................ [ 57%]\n........................................................................ [ 67%]\n........................................................................ [ 77%]\n........................................................................ [ 86%]\n........................................................................ [ 96%]\n............................                                             [100%]\n=========================== short test summary info ===========================\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b.py:14: P6B report is generated by the repair/quality gate before targeted pytest.\nSKIPPED [1] tests\\architecture\\test_android_responsive_visual_regression_evidence_suite_p6b_v2.py:14: P6B V2 report is generated by the repair/quality gate before targeted pytest.\n746 passed, 2 skipped, 34 deselected in 39.99s\n\n"
}
```

## Sonraki Adım

Faz 2C3 için kalan güvenli paket planlanabilir.