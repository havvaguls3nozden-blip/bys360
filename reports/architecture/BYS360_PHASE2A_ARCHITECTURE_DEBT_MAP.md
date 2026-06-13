# BYS360 Faz 2A Mimari Borç Haritası

Tarih: 2026-06-13T10:30:49

## Sonuç

- OK: True
- Karar: PHASE2A_MAP_READY
- Python file count: 1678
- Blueprint count: 18
- Route count: 976
- Main-like route count: 885
- Wildcard import count: 72
- Ruff F405 available: False
- Ruff F405 count: None
- God-file count >=1000 lines: 20
- Broad except count: 2942
- CIC hotspot count: 53
- Compileall returncode: 0
- Pytest quality smoke returncode: 0
- Pytest default returncode: 0

## Route Count By Domain

```json
{
  "assistant": 494,
  "admin": 138,
  "hr": 5,
  "performance": 186,
  "feedback": 17,
  "communication": 113,
  "main_or_unclear": 14,
  "portal": 9
}
```

## Route Count By Blueprint Top 50

```json
{
  "main_bp": 863,
  "mobile_api_bp": 46,
  "ai_agent": 17,
  "strategic_performance": 8,
  "main": 5,
  "hierarchy_governance": 4,
  "bp": 4,
  "pwa": 4,
  "president_scorecard_v2": 4,
  "ai_decision_faz10": 3,
  "ai_decision_faz11": 3,
  "ai_decision_faz12": 3,
  "executive_summary": 3,
  "bys360_pwa": 3,
  "health": 2,
  "strategic_performance_dashboard": 2,
  "app": 1,
  "workflow_dashboard_upgrade": 1
}
```

## Wildcard Imports

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
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 10,
    "module": "app.api.mobile.domains.auth",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 11,
    "module": "app.api.mobile.domains.dashboard",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 12,
    "module": "app.api.mobile.domains.personnel_read",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 13,
    "module": "app.api.mobile.domains.notifications",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 14,
    "module": "app.api.mobile.domains.support_survey_write",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 18,
    "module": "app.api.mobile.domains.communication_v1_write",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 19,
    "module": "app.api.mobile.domains.communication_v2_write",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 20,
    "module": "app.api.mobile.domains.assistant_chat",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 24,
    "module": "app.api.mobile.domains.personnel_write_all",
    "level": 0
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 25,
    "module": "app.api.mobile.domains.kpi_target_management",
    "level": 0
  },
  {
    "file": "app/institutional/hr_form_helpers.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "level": 0
  },
  {
    "file": "app/institutional/hr_leave_attendance_routes.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "level": 0
  },
  {
    "file": "app/institutional/hr_leave_attendance_routes.py",
    "line_no": 6,
    "module": "app.institutional.hr_form_helpers",
    "level": 0
  },
  {
    "file": "app/institutional/hr_leave_attendance_routes.py",
    "line_no": 7,
    "module": "app.institutional.hr_scope_helpers",
    "level": 0
  },
  {
    "file": "app/institutional/hr_reports_routes.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "level": 0
  },
  {
    "file": "app/institutional/hr_reports_routes.py",
    "line_no": 6,
    "module": "app.institutional.hr_form_helpers",
    "level": 0
  },
  {
    "file": "app/institutional/hr_reports_routes.py",
    "line_no": 7,
    "module": "app.institutional.hr_scope_helpers",
    "level": 0
  },
  {
    "file": "app/institutional/hr_scope_helpers.py",
    "line_no": 5,
    "module": "app.institutional.hr_common",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 9,
    "module": "app.institutional.hr_common",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 10,
    "module": "app.institutional.hr_form_helpers",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 11,
    "module": "app.institutional.hr_scope_helpers",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 139,
    "module": "app.institutional.org_unit_routes",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 140,
    "module": "app.institutional.hr_personnel_operations_routes",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 141,
    "module": "app.institutional.hr_leave_attendance_routes",
    "level": 0
  },
  {
    "file": "app/institutional/routes.py",
    "line_no": 142,
    "module": "app.institutional.hr_reports_routes",
    "level": 0
  },
  {
    "file": "app/main_handlers/account_handlers.py",
    "line_no": 5,
    "module": "app.main_handlers.account_communication_helpers",
    "level": 0
  },
  {
    "file": "app/main_handlers/account_settings_helpers.py",
    "line_no": 5,
    "module": "app.main_handlers.account_communication_helpers",
    "level": 0
  },
  {
    "file": "app/main_handlers/account_settings_helpers.py",
    "line_no": 6,
    "module": "app.main_handlers.account_visibility_helpers",
    "level": 0
  },
  {
    "file": "app/main_handlers/account_visibility_helpers.py",
    "line_no": 5,
    "module": "app.main_handlers.account_communication_helpers",
    "level": 0
  },
  {
    "file": "app/performance/engagement_common.py",
    "line_no": 10,
    "module": "feedback_helpers",
    "level": 1
  },
  {
    "file": "app/performance/engagement_common.py",
    "line_no": 11,
    "module": "mail_helpers",
    "level": 1
  },
  {
    "file": "app/performance/engagement_common.py",
    "line_no": 12,
    "module": "publish_helpers",
    "level": 1
  },
  {
    "file": "app/refactor/hotfix_merge_registry.py",
    "line_no": 12,
    "module": "maintenance_merge_registry",
    "level": 1
  },
  {
    "file": "app/schema_guard_core_repairs.py",
    "line_no": 12,
    "module": "schema_guard_core_maintenances",
    "level": 1
  },
  {
    "file": "app/services/ai/__init__.py",
    "line_no": 8,
    "module": "dashboard_panels",
    "level": 1
  },
  {
    "file": "app/services/ai/dashboard_panel_communication.py",
    "line_no": 6,
    "module": "app.services.ai.dashboard_panel_common",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panel_hr.py",
    "line_no": 6,
    "module": "app.services.ai.dashboard_panel_common",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panel_operations.py",
    "line_no": 7,
    "module": "app.services.ai.dashboard_panel_common",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panel_performance.py",
    "line_no": 6,
    "module": "app.services.ai.dashboard_panel_common",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panel_personnel.py",
    "line_no": 6,
    "module": "app.services.ai.dashboard_panel_common",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panel_repository.py",
    "line_no": 6,
    "module": "app.services.ai.dashboard_panel_common",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 9,
    "module": "app.services.ai.dashboard_panel_performance",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 10,
    "module": "app.services.ai.dashboard_panel_personnel",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 11,
    "module": "app.services.ai.dashboard_panel_hr",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 12,
    "module": "app.services.ai.dashboard_panel_communication",
    "level": 0
  },
  {
    "file": "app/services/ai/dashboard_panels.py",
    "line_no": 13,
    "module": "app.services.ai.dashboard_panel_operations",
    "level": 0
  },
  {
    "file": "app/services/mail_feedback.py",
    "line_no": 5,
    "module": "app.services.mail_core",
    "level": 0
  },
  {
    "file": "app/services/mail_performance_builder.py",
    "line_no": 5,
    "module": "app.services.mail_core",
    "level": 0
  },
  {
    "file": "app/services/mail_performance_sender.py",
    "line_no": 5,
    "module": "app.services.mail_core",
    "level": 0
  },
  {
    "file": "app/services/mail_performance_sender.py",
    "line_no": 6,
    "module": "app.services.mail_performance_builder",
    "level": 0
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 9,
    "module": "app.services.mail_core",
    "level": 0
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 10,
    "module": "app.services.mail_performance_builder",
    "level": 0
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 11,
    "module": "app.services.mail_performance_sender",
    "level": 0
  },
  {
    "file": "app/services/mail_service.py",
    "line_no": 12,
    "module": "app.services.mail_feedback",
    "level": 0
  },
  {
    "file": "app/services/performance/common_admin_scope_hotfix.py",
    "line_no": 12,
    "module": "common_admin_scope_maintenance",
    "level": 1
  },
  {
    "file": "app/services/performance/performance_rule_engine.py",
    "line_no": 11,
    "module": "app.performance.services.performance_rule_engine",
    "level": 0
  },
  {
    "file": "app/services/performance/phase3_visibility_permissions.py",
    "line_no": 10,
    "module": "app.services.performance.phase3_role_matrix",
    "level": 0
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 1,
    "module": "constants",
    "level": 1
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 2,
    "module": "state",
    "level": 1
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 3,
    "module": "transitions",
    "level": 1
  },
  {
    "file": "app/services/workflow/__init__.py",
    "line_no": 4,
    "module": "visibility",
    "level": 1
  }
]
```

## Ruff F405 Summary

```json
{
  "available": false,
  "returncode": 127,
  "f405_count": null,
  "by_file_top_80": {}
}
```

## God Files Top 20

```json
[
  {
    "file": "app/services/corporate_information_center.py",
    "line_count": 2839,
    "domain_guess": "communication"
  },
  {
    "file": "app/services/settings/effective_menu.py",
    "line_count": 2219,
    "domain_guess": "admin"
  },
  {
    "file": "app/api/mobile/performance_routes.py",
    "line_count": 1790,
    "domain_guess": "performance"
  },
  {
    "file": "app/menu_registry.py",
    "line_count": 1552,
    "domain_guess": "main_or_unclear"
  },
  {
    "file": "app/services/performance/low_score_process_service.py",
    "line_count": 1534,
    "domain_guess": "performance"
  },
  {
    "file": "app/main_handlers/account_communication_helpers.py",
    "line_count": 1386,
    "domain_guess": "assistant"
  },
  {
    "file": "app/services/settings/catalog.py",
    "line_count": 1332,
    "domain_guess": "admin"
  },
  {
    "file": "app/services/ai_agent/service.py",
    "line_count": 1298,
    "domain_guess": "assistant"
  },
  {
    "file": "app/institutional/hr_personnel_operations_routes.py",
    "line_count": 1246,
    "domain_guess": "hr"
  },
  {
    "file": "app/admin/ops_routes.py",
    "line_count": 1223,
    "domain_guess": "admin"
  },
  {
    "file": "app/admin/ai_routes.py",
    "line_count": 1217,
    "domain_guess": "admin"
  },
  {
    "file": "app/support/routes.py",
    "line_count": 1214,
    "domain_guess": "feedback"
  },
  {
    "file": "app/admin/routes.py",
    "line_count": 1156,
    "domain_guess": "admin"
  },
  {
    "file": "app/performance/engagement_feedback_routes.py",
    "line_count": 1141,
    "domain_guess": "feedback"
  },
  {
    "file": "app/communication/surveys_routes.py",
    "line_count": 1075,
    "domain_guess": "communication"
  },
  {
    "file": "app/workflow/routes.py",
    "line_count": 1072,
    "domain_guess": "main_or_unclear"
  },
  {
    "file": "app/support/help_center_content.py",
    "line_count": 1062,
    "domain_guess": "feedback"
  },
  {
    "file": "app/services/performance/process_engine_phase6_president_approvals.py",
    "line_count": 1016,
    "domain_guess": "performance"
  },
  {
    "file": "app/services/ai/dashboard_panel_personnel.py",
    "line_count": 1005,
    "domain_guess": "assistant"
  },
  {
    "file": "app/models/hr_models.py",
    "line_count": 1004,
    "domain_guess": "main_or_unclear"
  }
]
```

## Broad Except Top Files

```json
{
  "broad_except_count": 2942,
  "by_type": {
    "Exception": 2940,
    "BaseException": 2
  },
  "by_file_top_80": {
    "app/services/corporate_information_center.py": 87,
    "app/services/settings/effective_menu.py": 62,
    "app/api/mobile/performance_routes.py": 61,
    "app/services/performance/low_score_process_service.py": 56,
    "app/menu_registry.py": 44,
    "app/institutional/hr_personnel_operations_routes.py": 22,
    "app/main_handlers/account_settings_helpers.py": 22,
    "app/services/performance/v2_1_9_period_center_process_notifications.py": 22,
    "app/services/performance_dashboard_live_service.py": 21,
    "app/services/ai_agent/service.py": 19,
    "app/main_handlers/account_communication_helpers.py": 17,
    "app/performance/admin_core_routes.py": 17,
    "app/services/executive_mail_center_v2.py": 17,
    "app/services/performance/feedback_followup_phase4.py": 17,
    "app/support/routes.py": 17,
    "app/institutional/hr_common.py": 16,
    "app/services/cic/mail_scheduler_service.py": 16,
    "app/communication/surveys_routes.py": 15,
    "app/performance/phase10_development_guidance_ui.py": 15,
    "app/ai/routes.py": 14,
    "app/services/assistant_module_access.py": 14,
    "app/services/assistant_shortcut_visibility.py": 14,
    "app/services/menu_visibility.py": 14,
    "app/services/performance/common.py": 14,
    "app/services/surveys/targets.py": 14,
    "app/error_handlers.py": 13,
    "app/services/ai_decision/development_guidance_integration.py": 13,
    "app/services/assistant_role_matrix_v10.py": 13,
    "app/services/performance/v2_1_8_period_center_assignment_launch.py": 13,
    "app/admin/ops_routes.py": 12,
    "app/api/mobile/shared.py": 12,
    "app/institutional/hr_scope_helpers.py": 12,
    "app/services/daily_weather_mail.py": 12,
    "app/services/ui_context/dashboard.py": 12,
    "app/communication/phase2_routes.py": 11,
    "app/performance/interim_notes_manager_routes.py": 11,
    "app/services/performance/archive_service.py": 11,
    "app/services/performance/completion_phase4_third_manager_center.py": 11,
    "app/services/performance/phase9_development_guidance_center.py": 11,
    "app/services/portal_experience_service.py": 11,
    "app/services/sp1d_target_management_service.py": 11,
    "scripts/maintenance/bys360_technical_debt_cleanup_safe_v7.py": 11,
    "scripts/maintenance/run_bys360_final_gate_v2_17_70.py": 11,
    "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py": 11,
    "app/ai_agent/routes.py": 10,
    "app/menu_registry_data_performance.py": 10,
    "app/performance/engagement_mail_routes.py": 10,
    "app/performance/v2_1_7_period_management_center_routes.py": 10,
    "app/route_support.py": 10,
    "app/services/dashboard_rebuild_service.py": 10,
    "app/services/executive_mail_center.py": 10,
    "app/services/performance/category_stats.py": 10,
    "app/services/performance/phase8_midterm_feedback_center.py": 10,
    "app/services/performance/third_supervisor_policy.py": 10,
    "app/services/surveys/repository.py": 10,
    "app/services/ai/visibility_gate.py": 9,
    "app/services/cic/repository.py": 9,
    "app/services/message_service.py": 9,
    "app/services/performance/feedback_aftercare_phase7_person_period.py": 9,
    "app/services/performance/meeting_p4_development_guidance.py": 9,
    "app/services/performance/meeting_rule_enforcement.py": 9,
    "app/services/performance/phase7_scorecard_archive_center.py": 9,
    "app/services/performance_v2/reporting_workspace.py": 9,
    "app/services/portal_press_news_service.py": 9,
    "app/services/publication_service.py": 9,
    "scripts/maintenance/bys360_technical_debt_cleanup_safe_v6.py": 9,
    "scripts/maintenance/bys360_technical_debt_cleanup_safe_v8.py": 9,
    "app/api/mobile/domains/communication_v2_write.py": 8,
    "app/communication/feedback_routes.py": 8,
    "app/institutional/hr_personnel_extension_routes.py": 8,
    "app/main_handlers/auth_handlers.py": 8,
    "app/performance/engagement_publish_routes.py": 8,
    "app/performance/v2_1_11_evaluator_reminder_center_routes.py": 8,
    "app/security/__init__.py": 8,
    "app/services/corporate_information_center_engine.py": 8,
    "app/services/performance/meeting_p2_archive_notes.py": 8,
    "app/services/performance/meeting_p3_reminders.py": 8,
    "app/services/performance/phase12_performance_final_gate_center.py": 8,
    "app/services/performance/phase2_category_center.py": 8,
    "app/services/performance/v2_1_10_evaluation_live_tracking.py": 8
  },
  "ratchet_recommendation": {
    "current": 2942,
    "phase2_first_target": 2842,
    "phase2_safe_target": 2692,
    "note": "Öneri: CI eşiği bir anda sıfıra değil, sprint bazlı düşürülmeli."
  }
}
```

## CIC Mail Hotspots

```json
[
  {
    "file": "app/services/corporate_information_center.py",
    "line_count": 2839,
    "mail_term_hit_count": 784,
    "term_hits": {
      "mail": 252,
      "email": 94,
      "subject": 62,
      "body": 57,
      "template": 42,
      "mesaj": 3,
      "gönder": 56,
      "gonder": 4,
      "smtp": 33,
      "recipient": 103,
      "alıcı": 39,
      "alici": 39
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase3_dispatch.py",
    "line_count": 558,
    "mail_term_hit_count": 202,
    "term_hits": {
      "mail": 54,
      "email": 19,
      "subject": 14,
      "body": 13,
      "template": 19,
      "mesaj": 0,
      "gönder": 38,
      "gonder": 0,
      "smtp": 1,
      "recipient": 10,
      "alıcı": 17,
      "alici": 17
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/services/cic/mail_scheduler_service.py",
    "line_count": 471,
    "mail_term_hit_count": 184,
    "term_hits": {
      "mail": 79,
      "email": 14,
      "subject": 5,
      "body": 5,
      "template": 3,
      "mesaj": 0,
      "gönder": 6,
      "gonder": 0,
      "smtp": 20,
      "recipient": 36,
      "alıcı": 8,
      "alici": 8
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.py",
    "line_count": 667,
    "mail_term_hit_count": 73,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 5,
      "template": 17,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 25,
      "alıcı": 13,
      "alici": 13
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/services/corporate_information_center_engine.py",
    "line_count": 282,
    "mail_term_hit_count": 67,
    "term_hits": {
      "mail": 20,
      "email": 16,
      "subject": 8,
      "body": 8,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 15,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/seed_corporate_information_center_recipients_v3_0_phase2_1.py",
    "line_count": 153,
    "mail_term_hit_count": 59,
    "term_hits": {
      "mail": 16,
      "email": 14,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 9,
      "alıcı": 10,
      "alici": 10
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/services/cic/template_service.py",
    "line_count": 140,
    "mail_term_hit_count": 58,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 15,
      "body": 17,
      "template": 26,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_7_release_clean_ui.py",
    "line_count": 55,
    "mail_term_hit_count": 46,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 2,
      "template": 10,
      "mesaj": 0,
      "gönder": 21,
      "gonder": 0,
      "smtp": 1,
      "recipient": 0,
      "alıcı": 6,
      "alici": 6
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_12_all_template_macro_fix.py",
    "line_count": 237,
    "mail_term_hit_count": 44,
    "term_hits": {
      "mail": 2,
      "email": 1,
      "subject": 0,
      "body": 0,
      "template": 24,
      "mesaj": 0,
      "gönder": 5,
      "gonder": 0,
      "smtp": 0,
      "recipient": 4,
      "alıcı": 4,
      "alici": 4
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase6_final_uat_live_ready.py",
    "line_count": 201,
    "mail_term_hit_count": 43,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 26,
      "mesaj": 0,
      "gönder": 5,
      "gonder": 0,
      "smtp": 1,
      "recipient": 5,
      "alıcı": 3,
      "alici": 3
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/communication/corporate_information_center_routes.py",
    "line_count": 271,
    "mail_term_hit_count": 39,
    "term_hits": {
      "mail": 3,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 16,
      "mesaj": 0,
      "gönder": 1,
      "gonder": 0,
      "smtp": 0,
      "recipient": 11,
      "alıcı": 4,
      "alici": 4
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/services/cic/task_contract.py",
    "line_count": 237,
    "mail_term_hit_count": 36,
    "term_hits": {
      "mail": 2,
      "email": 0,
      "subject": 8,
      "body": 8,
      "template": 0,
      "mesaj": 3,
      "gönder": 4,
      "gonder": 2,
      "smtp": 0,
      "recipient": 9,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_live_release_usage.py",
    "line_count": 214,
    "mail_term_hit_count": 36,
    "term_hits": {
      "mail": 1,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 13,
      "mesaj": 0,
      "gönder": 12,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 5,
      "alici": 5
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase5_control_panel.py",
    "line_count": 169,
    "mail_term_hit_count": 36,
    "term_hits": {
      "mail": 2,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 25,
      "mesaj": 0,
      "gönder": 4,
      "gonder": 0,
      "smtp": 0,
      "recipient": 3,
      "alıcı": 1,
      "alici": 1
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
    "line_count": 81,
    "mail_term_hit_count": 33,
    "term_hits": {
      "mail": 2,
      "email": 1,
      "subject": 0,
      "body": 0,
      "template": 14,
      "mesaj": 0,
      "gönder": 7,
      "gonder": 0,
      "smtp": 0,
      "recipient": 1,
      "alıcı": 4,
      "alici": 4
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.py",
    "line_count": 395,
    "mail_term_hit_count": 32,
    "term_hits": {
      "mail": 2,
      "email": 1,
      "subject": 0,
      "body": 0,
      "template": 15,
      "mesaj": 0,
      "gönder": 5,
      "gonder": 0,
      "smtp": 0,
      "recipient": 1,
      "alıcı": 4,
      "alici": 4
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_live_release_usage.py",
    "line_count": 194,
    "mail_term_hit_count": 32,
    "term_hits": {
      "mail": 1,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 9,
      "mesaj": 0,
      "gönder": 12,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 5,
      "alici": 5
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/services/cic/facade.py",
    "line_count": 121,
    "mail_term_hit_count": 32,
    "term_hits": {
      "mail": 11,
      "email": 6,
      "subject": 0,
      "body": 0,
      "template": 9,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 6,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "app/services/cic/repository.py",
    "line_count": 472,
    "mail_term_hit_count": 27,
    "term_hits": {
      "mail": 14,
      "email": 12,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase6_1_staff_noon_message.py",
    "line_count": 152,
    "mail_term_hit_count": 25,
    "term_hits": {
      "mail": 1,
      "email": 0,
      "subject": 10,
      "body": 9,
      "template": 5,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Mail içerikleri ayrı content/template katmanına alınmalı."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase5_control_panel.py",
    "line_count": 60,
    "mail_term_hit_count": 19,
    "term_hits": {
      "mail": 2,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 10,
      "mesaj": 0,
      "gönder": 4,
      "gonder": 0,
      "smtp": 0,
      "recipient": 1,
      "alıcı": 1,
      "alici": 1
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase6_final_uat_live_ready.py",
    "line_count": 75,
    "mail_term_hit_count": 18,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 12,
      "mesaj": 0,
      "gönder": 1,
      "gonder": 0,
      "smtp": 0,
      "recipient": 3,
      "alıcı": 1,
      "alici": 1
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_11_template_compat_fix.py",
    "line_count": 217,
    "mail_term_hit_count": 16,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 14,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 1,
      "alici": 1
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase4_1_real_advanced_ui.py",
    "line_count": 42,
    "mail_term_hit_count": 14,
    "term_hits": {
      "mail": 1,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 9,
      "mesaj": 0,
      "gönder": 1,
      "gonder": 0,
      "smtp": 0,
      "recipient": 1,
      "alıcı": 1,
      "alici": 1
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase2_1.py",
    "line_count": 31,
    "mail_term_hit_count": 13,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 5,
      "alıcı": 4,
      "alici": 4
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase1.py",
    "line_count": 36,
    "mail_term_hit_count": 11,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 10,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 1,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase2_2.py",
    "line_count": 35,
    "mail_term_hit_count": 10,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 2,
      "mesaj": 0,
      "gönder": 1,
      "gonder": 0,
      "smtp": 0,
      "recipient": 3,
      "alıcı": 2,
      "alici": 2
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_11_template_compat_fix.py",
    "line_count": 65,
    "mail_term_hit_count": 8,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 8,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    "line_count": 321,
    "mail_term_hit_count": 7,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 7,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_10_status_pill_fix.py",
    "line_count": 58,
    "mail_term_hit_count": 6,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 6,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "app/services/cic/__init__.py",
    "line_count": 21,
    "mail_term_hit_count": 6,
    "term_hits": {
      "mail": 3,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 3,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase4_advanced_ui.py",
    "line_count": 30,
    "mail_term_hit_count": 5,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 4,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 1,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/communication/repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
    "line_count": 197,
    "mail_term_hit_count": 4,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 4,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase3_dispatch.py",
    "line_count": 53,
    "mail_term_hit_count": 3,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 2,
      "mesaj": 0,
      "gönder": 1,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py",
    "line_count": 83,
    "mail_term_hit_count": 2,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 2,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py",
    "line_count": 72,
    "mail_term_hit_count": 2,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 2,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_12_all_template_macro_fix.py",
    "line_count": 55,
    "mail_term_hit_count": 2,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 2,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase5_1_gate_fix.py",
    "line_count": 52,
    "mail_term_hit_count": 2,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 1,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_7_release_clean_ui.py",
    "line_count": 42,
    "mail_term_hit_count": 2,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 2,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase2_3.py",
    "line_count": 28,
    "mail_term_hit_count": 2,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 2,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    "line_count": 60,
    "mail_term_hit_count": 1,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "app/services/cic/celebration_service.py",
    "line_count": 56,
    "mail_term_hit_count": 1,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v4_0_smart_celebrations.py",
    "line_count": 52,
    "mail_term_hit_count": 1,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "app/services/cic/query_service.py",
    "line_count": 46,
    "mail_term_hit_count": 1,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.py",
    "line_count": 42,
    "mail_term_hit_count": 1,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 1,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_1_base_css_link_fix.py",
    "line_count": 44,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/communication/run_corporate_information_center_task_v3_0_phase2.py",
    "line_count": 34,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase6_1_staff_noon_message.py",
    "line_count": 34,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
    "line_count": 32,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/communication/run_corporate_information_center_task.py",
    "line_count": 30,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase2.py",
    "line_count": 27,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase5_2_flat_gate_fix.py",
    "line_count": 22,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  },
  {
    "file": "scripts/quality/check_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
    "line_count": 22,
    "mail_term_hit_count": 0,
    "term_hits": {
      "mail": 0,
      "email": 0,
      "subject": 0,
      "body": 0,
      "template": 0,
      "mesaj": 0,
      "gönder": 0,
      "gonder": 0,
      "smtp": 0,
      "recipient": 0,
      "alıcı": 0,
      "alici": 0
    },
    "long_triple_string_block_count_estimate": 0,
    "recommendation": "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
  }
]
```

## Önerilen Refactor Sırası

```json
[
  {
    "order": 1,
    "phase": "Faz 2B",
    "title": "Blueprint route split contract tests",
    "goal": "Route taşıma başlamadan önce mevcut endpoint/url/permission davranışını kilitlemek.",
    "risk": "low",
    "entry_condition": "S0Z green",
    "exit_evidence": "Route snapshot ve role/permission smoke testleri yeşil."
  },
  {
    "order": 2,
    "phase": "Faz 2C",
    "title": "Wildcard import audit and first replacements",
    "goal": "72 wildcard import için explicit import planı üretmek.",
    "risk": "medium",
    "entry_condition": "F405 haritası hazır",
    "exit_evidence": "İlk düşük riskli dosya grubunda F405 azalır, testler yeşil kalır."
  },
  {
    "order": 3,
    "phase": "Faz 2D",
    "title": "feedback blueprint extraction candidate",
    "goal": "feedback alanındaki yaklaşık 17 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "low",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "feedback endpointleri aynı davranışla yeşil."
  },
  {
    "order": 4,
    "phase": "Faz 2D",
    "title": "assistant blueprint extraction candidate",
    "goal": "assistant alanındaki yaklaşık 494 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "low",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "assistant endpointleri aynı davranışla yeşil."
  },
  {
    "order": 5,
    "phase": "Faz 2D",
    "title": "portal blueprint extraction candidate",
    "goal": "portal alanındaki yaklaşık 9 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "medium",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "portal endpointleri aynı davranışla yeşil."
  },
  {
    "order": 6,
    "phase": "Faz 2D",
    "title": "communication blueprint extraction candidate",
    "goal": "communication alanındaki yaklaşık 113 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "medium",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "communication endpointleri aynı davranışla yeşil."
  },
  {
    "order": 7,
    "phase": "Faz 2D",
    "title": "hr blueprint extraction candidate",
    "goal": "hr alanındaki yaklaşık 5 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "medium",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "hr endpointleri aynı davranışla yeşil."
  },
  {
    "order": 8,
    "phase": "Faz 2D",
    "title": "performance blueprint extraction candidate",
    "goal": "performance alanındaki yaklaşık 186 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "high",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "performance endpointleri aynı davranışla yeşil."
  },
  {
    "order": 9,
    "phase": "Faz 2D",
    "title": "admin blueprint extraction candidate",
    "goal": "admin alanındaki yaklaşık 138 route için ayrı blueprint/url_prefix hazırlığı.",
    "risk": "high",
    "entry_condition": "Route snapshot testi mevcut.",
    "exit_evidence": "admin endpointleri aynı davranışla yeşil."
  },
  {
    "order": 10,
    "phase": "Faz 2E",
    "title": "Corporate Information Center mail content extraction",
    "goal": "E-posta konu/gövde içeriklerini servis dosyasından content/template katmanına taşımak.",
    "risk": "medium",
    "entry_condition": "Mail render smoke testi mevcut.",
    "exit_evidence": "Mail preview/test gönderim davranışı değişmeden yeşil."
  },
  {
    "order": 11,
    "phase": "Faz 2F",
    "title": "Broad except ratchet",
    "goal": "Broad except sayısını 2942 seviyesinden kontrollü düşürmek.",
    "risk": "medium",
    "entry_condition": "Mevcut sayı raporlandı.",
    "exit_evidence": "CI ratchet eşiği sprint bazlı düşer; testler yeşil kalır."
  }
]
```

## Pytest Default Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Sonraki Adım

Faz 2B route snapshot ve blueprint extraction contract testleri yazılabilir.