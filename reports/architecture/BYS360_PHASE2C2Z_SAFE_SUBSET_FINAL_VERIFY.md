# BYS360 Faz 2C2Z Safe Subset Final Verify

Tarih: 2026-06-13T11:02:52

## Sonuç

- OK: False
- Karar: PHASE2C2Z_REVIEW_REQUIRED
- Target file count: 10
- Target all OK: False
- Intentional skip OK: True
- App AST wildcard import count: 72
- App mobile shared remaining count: 11
- Compileall returncode: 0
- Contract pytest returncode: 0
- Quality smoke returncode: 0
- Default pytest returncode: 0
- Tests green: True

## Target Status

```json
[
  {
    "file": "app/api/mobile/domains/assistant_chat.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1D domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/auth.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1C domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/communication_v1_write.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1D domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/communication_v2_write.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1D domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/dashboard.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1C domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/kpi_target_management.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1E domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/notifications.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1C domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/personnel_read.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1C domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/personnel_write_all.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1E domain endpoint importu"
    ],
    "ok": false
  },
  {
    "file": "app/api/mobile/domains/support_survey_write.py",
    "exists": true,
    "has_shared_wildcard": true,
    "explicit_shared_import_lines": [
      "*  # noqa: F401,F403 - BYS360 P1C domain endpoint importu"
    ],
    "ok": false
  }
]
```

## Intentional Skip

```json
{
  "file": "app/api/mobile/routes.py",
  "exists": true,
  "has_shared_wildcard": true,
  "reason": "Bilinçli facade import; ayrı refactor fazında ele alınacak.",
  "ok": true
}
```

## App Wildcard By Module Top 50

```json
{
  "app.api.mobile.shared": 11,
  "app.services.ai.dashboard_panel_common": 6,
  "app.institutional.hr_common": 5,
  "app.services.mail_core": 4,
  "app.institutional.hr_form_helpers": 3,
  "app.institutional.hr_scope_helpers": 3,
  "app.main_handlers.account_communication_helpers": 3,
  "app.services.mail_performance_builder": 2,
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

## App Mobile Shared Remaining

```json
[
  {
    "file": "app/api/mobile/domains/assistant_chat.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/auth.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/communication_v1_write.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/communication_v2_write.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/dashboard.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/kpi_target_management.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/notifications.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/personnel_read.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/personnel_write_all.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/domains/support_survey_write.py",
    "line_no": 8,
    "module": "app.api.mobile.shared",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 7,
    "module": "app.api.mobile.shared",
    "level": 0
  }
]
```

## Default Pytest Summary

```json
{
  "passed": 746,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Sonraki Adım

Hedef dosya veya test kontrolü incelenmeli.