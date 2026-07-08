# BYS360 Faz 2C4 Facade Exception Closure Evidence

Tarih: 2026-06-13T11:39:31

## Sonuç

- OK: True
- Karar: PHASE2C4_CLOSED_ROUTES_FACADE_WILDCARD_INTENTIONAL_EXCEPTION
- Routes file: `app/api/mobile/routes.py`
- Routes has mobile shared wildcard: True
- Routes has mobile shared explicit: False
- App AST wildcard count: 62
- Mobile shared remaining count: 1
- Compileall returncode: 0
- Contract pytest returncode: 0
- Auth guard pytest returncode: 0
- Default pytest returncode: 0
- Tests green: True

## İstisna Gerekçesi

routes.py mobil facade/aggregator rolünde olduğu için app.api.mobile.shared wildcard import C4 sonunda bilinçli istisna olarak bırakıldı.

## Mobile Shared Remaining

```json
[
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 7,
    "module": "app.api.mobile.shared",
    "level": 0
  }
]
```

## App Wildcard By Module Top 50

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

Faz 2C5: mobil shared dışındaki sıradaki düşük riskli wildcard import paketi seçilebilir.