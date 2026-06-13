# BYS360 Faz 2C1 Wildcard Import Explicit Plan

Tarih: 2026-06-13T11:53:32

## Sonuç

- OK: True
- Karar: PHASE2C1_PLAN_READY
- Wildcard import count: 58
- Ready for explicit import count: 31
- Manual review count: 27
- First apply candidate count: 1
- Compileall returncode: 0
- Contract pytest returncode: 0
- Pytest default returncode: 0

## By Status

```json
{
  "ready_for_explicit_import": 31,
  "manual_review": 27
}
```

## By Risk

```json
{
  "low": 28,
  "medium": 30
}
```

## By Module Top 50

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

## First Apply Candidates

```json
[
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 7,
    "module": "app.api.mobile.shared",
    "level": 0,
    "resolved_module_path": "app/api/mobile/shared.py",
    "status": "ready_for_explicit_import",
    "reason": "used_names_detected",
    "risk": "low",
    "export_source": "top_level_public_names",
    "export_count": 51,
    "used_export_count": 3,
    "used_export_names": [
      "User",
      "jsonify",
      "request"
    ],
    "possible_shadowed_names": [],
    "suggested_import_line": "from app.api.mobile.shared import User, jsonify, request"
  }
]
```

## Manual Review Items Top 80

```json
[
  {
    "file": "app/institutional/hr_leave_attendance_routes.py",
    "line_no": 7,
    "module": "app.institutional.hr_scope_helpers",
    "level": 0,
    "resolved_module_path": "app/institutional/hr_scope_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 1,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/institutional/hr_reports_routes.py",
    "line_no": 7,
    "module": "app.institutional.hr_scope_helpers",
    "level": 0,
    "resolved_module_path": "app/institutional/hr_scope_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 1,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 11,
    "module": "app.institutional.hr_scope_helpers",
    "level": 0,
    "resolved_module_path": "app/institutional/hr_scope_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 1,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 139,
    "module": "app.institutional.org_unit_routes",
    "level": 0,
    "resolved_module_path": "app/institutional/org_unit_routes.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 13,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 141,
    "module": "app.institutional.hr_leave_attendance_routes",
    "level": 0,
    "resolved_module_path": "app/institutional/hr_leave_attendance_routes.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 11,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/main_handlers/account_settings_helpers.py",
    "line_no": 6,
    "module": "app.main_handlers.account_visibility_helpers",
    "level": 0,
    "resolved_module_path": "app/main_handlers/account_visibility_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 3,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/performance/engagement_common.py",
    "line_no": 10,
    "module": "feedback_helpers",
    "level": 1,
    "resolved_module_path": "app/performance/feedback_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 16,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/performance/engagement_common.py",
    "line_no": 11,
    "module": "mail_helpers",
    "level": 1,
    "resolved_module_path": "app/performance/mail_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 1,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/performance/engagement_common.py",
    "line_no": 12,
    "module": "publish_helpers",
    "level": 1,
    "resolved_module_path": "app/performance/publish_helpers.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 5,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/refactor/hotfix_merge_registry.py",
    "line_no": 12,
    "module": "maintenance_merge_registry",
    "level": 1,
    "resolved_module_path": "app/refactor/maintenance_merge_registry.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 2,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/schema_guard_core_repairs.py",
    "line_no": 12,
    "module": "schema_guard_core_maintenances",
    "level": 1,
    "resolved_module_path": "app/schema_guard_core_maintenances.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 3,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/ai/__init__.py",
    "line_no": 8,
    "module": "dashboard_panels",
    "level": 1,
    "resolved_module_path": "app/services/ai/dashboard_panels.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 38,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 9,
    "module": "app.services.ai.dashboard_panel_performance",
    "level": 0,
    "resolved_module_path": "app/services/ai/dashboard_panel_performance.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 16,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 10,
    "module": "app.services.ai.dashboard_panel_personnel",
    "level": 0,
    "resolved_module_path": "app/services/ai/dashboard_panel_personnel.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 16,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 11,
    "module": "app.services.ai.dashboard_panel_hr",
    "level": 0,
    "resolved_module_path": "app/services/ai/dashboard_panel_hr.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 3,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 12,
    "module": "app.services.ai.dashboard_panel_communication",
    "level": 0,
    "resolved_module_path": "app/services/ai/dashboard_panel_communication.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 19,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 13,
    "module": "app.services.ai.dashboard_panel_operations",
    "level": 0,
    "resolved_module_path": "app/services/ai/dashboard_panel_operations.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 4,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 10,
    "module": "app.services.mail_performance_builder",
    "level": 0,
    "resolved_module_path": "app/services/mail_performance_builder.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 6,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 11,
    "module": "app.services.mail_performance_sender",
    "level": 0,
    "resolved_module_path": "app/services/mail_performance_sender.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 17,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 12,
    "module": "app.services.mail_feedback",
    "level": 0,
    "resolved_module_path": "app/services/mail_feedback.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 5,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/performance/common_admin_scope_hotfix.py",
    "line_no": 12,
    "module": "common_admin_scope_maintenance",
    "level": 1,
    "resolved_module_path": "app/services/performance/common_admin_scope_maintenance.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 3,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/performance/performance_rule_engine.py",
    "line_no": 11,
    "module": "app.performance.services.performance_rule_engine",
    "level": 0,
    "resolved_module_path": "app/performance/services/performance_rule_engine.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 17,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/performance/phase3_visibility_permissions.py",
    "line_no": 10,
    "module": "app.services.performance.phase3_role_matrix",
    "level": 0,
    "resolved_module_path": "app/services/performance/phase3_role_matrix.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "top_level_public_names",
    "export_count": 22,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 1,
    "module": "constants",
    "level": 1,
    "resolved_module_path": "app/services/workflow/constants.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 12,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 2,
    "module": "state",
    "level": 1,
    "resolved_module_path": "app/services/workflow/state.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 4,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 3,
    "module": "transitions",
    "level": 1,
    "resolved_module_path": "app/services/workflow/transitions.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 6,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 4,
    "module": "visibility",
    "level": 1,
    "resolved_module_path": "app/services/workflow/visibility.py",
    "status": "manual_review",
    "reason": "no_used_export_name_detected",
    "risk": "medium",
    "export_source": "__all__",
    "export_count": 3,
    "used_export_count": 0,
    "used_export_names": [],
    "possible_shadowed_names": [],
    "suggested_import_line": null
  }
]
```

## Contract Pytest Summary

```json
{
  "passed": 2,
  "failed": 0,
  "errors": 0,
  "skipped": 0,
  "deselected": 0,
  "warnings": 0
}
```

## Pytest Default Summary

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

Faz 2C2 düşük riskli app/api/mobile/shared wildcard import dönüşümü uygulanabilir.