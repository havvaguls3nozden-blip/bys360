# BYS360 A10A Faz / Dev / Debug / Teknik Dil Audit

Tarih: 2026-06-12T19:48:14

## Özet

- Mode: `audit_only`
- File candidate count: 970
- Protected match count: 1
- Critical keep missing count: 0
- UI technical file count: 395
- UI technical hit total: 2233
- A10A OK: False

## Sınıflandırma

```json
{
  "app_user_or_runtime_review": 702,
  "test_or_contract_review": 34,
  "general_review": 113,
  "quality_gate_review": 108,
  "windows_script_review": 13
}
```

## Eksik Korunması Gereken Dosyalar

```text
Yok
```

## Korunan Eşleşmeler

```json
[
  {
    "path": "scripts/windows/claude_phase7_final_quality.ps1",
    "name": "claude_phase7_final_quality.ps1",
    "suffix": ".ps1",
    "hits": [
      "claude",
      "phase"
    ],
    "classification": "protected_keep"
  }
]
```

## Dosya Adı / Yol Adayları İlk 250

```json
[
  {
    "path": "app/schema_guard_core_repairs.py",
    "name": "schema_guard_core_repairs.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/template_safety.py",
    "name": "template_safety.py",
    "suffix": ".py",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase10_routes.py",
    "name": "ai_phase10_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase11_routes.py",
    "name": "ai_phase11_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase12_routes.py",
    "name": "ai_phase12_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase2_routes.py",
    "name": "ai_phase2_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase5_routes.py",
    "name": "ai_phase5_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase6_routes.py",
    "name": "ai_phase6_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase7_routes.py",
    "name": "ai_phase7_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase8_routes.py",
    "name": "ai_phase8_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/admin/ai_phase9_routes.py",
    "name": "ai_phase9_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz10_routes.py",
    "name": "decision_support_faz10_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz11_routes.py",
    "name": "decision_support_faz11_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz12_routes.py",
    "name": "decision_support_faz12_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz1_ui_safe.py",
    "name": "decision_support_faz1_ui_safe.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz3_routes.py",
    "name": "decision_support_faz3_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz4_routes.py",
    "name": "decision_support_faz4_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz5_routes.py",
    "name": "decision_support_faz5_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz6_routes.py",
    "name": "decision_support_faz6_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz7_routes.py",
    "name": "decision_support_faz7_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz8_routes.py",
    "name": "decision_support_faz8_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/ai/decision_support_faz9_routes.py",
    "name": "decision_support_faz9_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase1_routes.py",
    "name": "phase1_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase2_routes.py",
    "name": "phase2_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase3_routes.py",
    "name": "phase3_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase4_routes.py",
    "name": "phase4_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase5_routes.py",
    "name": "phase5_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase8_routes.py",
    "name": "phase8_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase9a_routes.py",
    "name": "phase9a_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase9b_routes.py",
    "name": "phase9b_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase9c_routes.py",
    "name": "phase9c_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase9d_routes.py",
    "name": "phase9d_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase9_routes.py",
    "name": "phase9_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/communication/phase_family_routes.py",
    "name": "phase_family_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/config/faz6_engine_patch.py",
    "name": "faz6_engine_patch.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/docs/GO_LIVE_PERFORMANCE_FAZ2_3_NORMALIZE_WEIGHT_INPUTS_FIX.md",
    "name": "GO_LIVE_PERFORMANCE_FAZ2_3_NORMALIZE_WEIGHT_INPUTS_FIX.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/institutional/hr_personnel_phase10_routes.py",
    "name": "hr_personnel_phase10_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/institutional/hr_personnel_phase11_routes.py",
    "name": "hr_personnel_phase11_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/institutional/hr_personnel_phase12_routes.py",
    "name": "hr_personnel_phase12_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/institutional/hr_personnel_phase13_routes.py",
    "name": "hr_personnel_phase13_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/models/communication_phase1_models.py",
    "name": "communication_phase1_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/models/communication_phase2_models.py",
    "name": "communication_phase2_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/models/communication_phase3_models.py",
    "name": "communication_phase3_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/models/communication_phase4_models.py",
    "name": "communication_phase4_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/models/communication_phase5_models.py",
    "name": "communication_phase5_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/feedback_corporate_cleanup_phase6_routes.py",
    "name": "feedback_corporate_cleanup_phase6_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/feedback_final_gate_phase5_routes.py",
    "name": "feedback_final_gate_phase5_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/feedback_followup_phase4_routes.py",
    "name": "feedback_followup_phase4_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/meeting_development_faz3_routes.py",
    "name": "meeting_development_faz3_routes.py",
    "suffix": ".py",
    "hits": [
      "dev",
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/meeting_development_faz4_routes.py",
    "name": "meeting_development_faz4_routes.py",
    "suffix": ".py",
    "hits": [
      "dev",
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/meeting_development_routes.py",
    "name": "meeting_development_routes.py",
    "suffix": ".py",
    "hits": [
      "dev"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/meeting_p4_development_guidance_routes.py",
    "name": "meeting_p4_development_guidance_routes.py",
    "suffix": ".py",
    "hits": [
      "dev"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/phase10_development_guidance_ui.py",
    "name": "phase10_development_guidance_ui.py",
    "suffix": ".py",
    "hits": [
      "dev",
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/phase10_scorecard_integration.py",
    "name": "phase10_scorecard_integration.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/process_engine_phase10_reports_routes.py",
    "name": "process_engine_phase10_reports_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/process_engine_phase6_president_approvals_routes.py",
    "name": "process_engine_phase6_president_approvals_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/performance/process_engine_phase8_tracking_routes.py",
    "name": "process_engine_phase8_tracking_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1e_deletion_allowlist.py",
    "name": "faz1e_deletion_allowlist.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1f_family_targets.py",
    "name": "faz1f_family_targets.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1g_selected_merge_specs.py",
    "name": "faz1g_selected_merge_specs.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1h_selected_targets.py",
    "name": "faz1h_selected_targets.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1i_required_merge_spec.py",
    "name": "faz1i_required_merge_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1j_selected_route_melt_spec.py",
    "name": "faz1j_selected_route_melt_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1k_phase_family_spec.py",
    "name": "faz1k_phase_family_spec.py",
    "suffix": ".py",
    "hits": [
      "faz",
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1l_family_melt_spec.py",
    "name": "faz1l_family_melt_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/faz1m_service_delegate_spec.py",
    "name": "faz1m_service_delegate_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/hotfix_merge_registry.py",
    "name": "hotfix_merge_registry.py",
    "suffix": ".py",
    "hits": [
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/phase_alias_manifest.py",
    "name": "phase_alias_manifest.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/refactor/schema_guard_faz1d_bundle.py",
    "name": "schema_guard_faz1d_bundle.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/assignment_sync_service.py",
    "name": "assignment_sync_service.py",
    "suffix": ".py",
    "hits": [
      "sync"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/async_job_queue.py",
    "name": "async_job_queue.py",
    "suffix": ".py",
    "hits": [
      "sync"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase1_service.py",
    "name": "communication_phase1_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase2_service.py",
    "name": "communication_phase2_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase3_service.py",
    "name": "communication_phase3_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase4_service.py",
    "name": "communication_phase4_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase5_service.py",
    "name": "communication_phase5_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase8_service.py",
    "name": "communication_phase8_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase9a_service.py",
    "name": "communication_phase9a_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase9b_service.py",
    "name": "communication_phase9b_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase9c_service.py",
    "name": "communication_phase9c_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase9d_service.py",
    "name": "communication_phase9d_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/communication_phase9_service.py",
    "name": "communication_phase9_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/evaluation_workflow_service.py",
    "name": "evaluation_workflow_service.py",
    "suffix": ".py",
    "hits": [
      "workflow"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/instagram_portal_sync.py",
    "name": "instagram_portal_sync.py",
    "suffix": ".py",
    "hits": [
      "sync"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/legacy_import_service.py",
    "name": "legacy_import_service.py",
    "suffix": ".py",
    "hits": [
      "legacy"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/personnel_sync_service.py",
    "name": "personnel_sync_service.py",
    "suffix": ".py",
    "hits": [
      "sync"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/role_matrix_phase4_gate_service.py",
    "name": "role_matrix_phase4_gate_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/services/role_matrix_phase5_final_gate_service.py",
    "name": "role_matrix_phase5_final_gate_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/about_bys360.html",
    "name": "about_bys360.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/account.html",
    "name": "account.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/account_change_password.html",
    "name": "account_change_password.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/account_security_setup.html",
    "name": "account_security_setup.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/action_suggestion_macros.html",
    "name": "action_suggestion_macros.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_acceptance_pack.html",
    "name": "admin_ai_acceptance_pack.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_assignment_recommendations.html",
    "name": "admin_ai_assignment_recommendations.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_base.html",
    "name": "admin_ai_base.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_center.html",
    "name": "admin_ai_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_decision_history.html",
    "name": "admin_ai_decision_history.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_executive_brief.html",
    "name": "admin_ai_executive_brief.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_executive_report.html",
    "name": "admin_ai_executive_report.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_feedback.html",
    "name": "admin_ai_feedback.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_final_live_hardening.html",
    "name": "admin_ai_final_live_hardening.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_governance_hub.html",
    "name": "admin_ai_governance_hub.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_governance_settings.html",
    "name": "admin_ai_governance_settings.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_go_live_readiness.html",
    "name": "admin_ai_go_live_readiness.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_management_pack.html",
    "name": "admin_ai_management_pack.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_module_health.html",
    "name": "admin_ai_module_health.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_notification_priority.html",
    "name": "admin_ai_notification_priority.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_operations_report.html",
    "name": "admin_ai_operations_report.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_preflight.html",
    "name": "admin_ai_preflight.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_prompt_compare.html",
    "name": "admin_ai_prompt_compare.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_quality_hub.html",
    "name": "admin_ai_quality_hub.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_recommendations.html",
    "name": "admin_ai_recommendations.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_redaction_rules.html",
    "name": "admin_ai_redaction_rules.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_requests.html",
    "name": "admin_ai_requests.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_review_queue.html",
    "name": "admin_ai_review_queue.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_schema_not_ready.html",
    "name": "admin_ai_schema_not_ready.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_settings.html",
    "name": "admin_ai_settings.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_smoke.html",
    "name": "admin_ai_smoke.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_visibility_gate.html",
    "name": "admin_ai_visibility_gate.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_ai_weekly_summary.html",
    "name": "admin_ai_weekly_summary.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_analysis_excel_preview.html",
    "name": "admin_analysis_excel_preview.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_analysis_recommendation_priority.html",
    "name": "admin_analysis_recommendation_priority.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_analysis_visual_reports.html",
    "name": "admin_analysis_visual_reports.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_dashboard.html",
    "name": "admin_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_go_live_readiness.html",
    "name": "admin_go_live_readiness.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_import_health_report.html",
    "name": "admin_import_health_report.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_system_scan.html",
    "name": "admin_system_scan.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_users.html",
    "name": "admin_users.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_user_create.html",
    "name": "admin_user_create.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/admin_user_edit.html",
    "name": "admin_user_edit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/announcements_list.html",
    "name": "announcements_list.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/announcement_new.html",
    "name": "announcement_new.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/assignment_audit_detail.html",
    "name": "assignment_audit_detail.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/assignment_generate.html",
    "name": "assignment_generate.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/assignment_recommendations.html",
    "name": "assignment_recommendations.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/assignment_rule_audit.html",
    "name": "assignment_rule_audit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/assistant_training_bank.html",
    "name": "assistant_training_bank.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/base.html",
    "name": "base.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/communication_dashboard.html",
    "name": "communication_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/communication_suite_macros.html",
    "name": "communication_suite_macros.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/criteria.html",
    "name": "criteria.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/criteria_create.html",
    "name": "criteria_create.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/criteria_edit.html",
    "name": "criteria_edit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/dashboard.html",
    "name": "dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/db_check.html",
    "name": "db_check.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/decision_support_macros.html",
    "name": "decision_support_macros.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/evaluation_form.html",
    "name": "evaluation_form.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/evaluation_tasks.html",
    "name": "evaluation_tasks.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/excel_import.html",
    "name": "excel_import.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_audit_dashboard.html",
    "name": "feedback_audit_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_executive_summary_dashboard.html",
    "name": "feedback_executive_summary_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_go_live_center.html",
    "name": "feedback_go_live_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_go_live_smoke.html",
    "name": "feedback_go_live_smoke.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_go_live_uat.html",
    "name": "feedback_go_live_uat.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "name": "feedback_meetings_list.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_meeting_detail.html",
    "name": "feedback_meeting_detail.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_operations_dashboard.html",
    "name": "feedback_operations_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/feedback_watch_dashboard.html",
    "name": "feedback_watch_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/forgot_password.html",
    "name": "forgot_password.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hierarchy_assignments.html",
    "name": "hierarchy_assignments.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hierarchy_assignment_edit.html",
    "name": "hierarchy_assignment_edit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hierarchy_settings.html",
    "name": "hierarchy_settings.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hierarchy_tree.html",
    "name": "hierarchy_tree.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/home.html",
    "name": "home.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_attendance.html",
    "name": "hr_attendance.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_career.html",
    "name": "hr_career.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_leave.html",
    "name": "hr_leave.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_management.html",
    "name": "hr_management.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_approval_station_center.html",
    "name": "hr_personnel_approval_station_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_assets_center.html",
    "name": "hr_personnel_assets_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_asset_transfer_center.html",
    "name": "hr_personnel_asset_transfer_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_checklist_center.html",
    "name": "hr_personnel_checklist_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_clearance_board.html",
    "name": "hr_personnel_clearance_board.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_dashboard.html",
    "name": "hr_personnel_dashboard.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_digital_handover_documents.html",
    "name": "hr_personnel_digital_handover_documents.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_exit_interviews.html",
    "name": "hr_personnel_exit_interviews.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_exit_risk_center.html",
    "name": "hr_personnel_exit_risk_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_handover_center.html",
    "name": "hr_personnel_handover_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_lifecycle_board.html",
    "name": "hr_personnel_lifecycle_board.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_lifecycle_center.html",
    "name": "hr_personnel_lifecycle_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_operations.html",
    "name": "hr_personnel_operations.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_reminder_center.html",
    "name": "hr_personnel_reminder_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_renewal_calendar.html",
    "name": "hr_personnel_renewal_calendar.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_request_analytics.html",
    "name": "hr_personnel_request_analytics.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_request_reports.html",
    "name": "hr_personnel_request_reports.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_request_review.html",
    "name": "hr_personnel_request_review.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_request_sla_policies.html",
    "name": "hr_personnel_request_sla_policies.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_request_tasks.html",
    "name": "hr_personnel_request_tasks.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_personnel_validity_center.html",
    "name": "hr_personnel_validity_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_reports.html",
    "name": "hr_reports.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_reports_print.html",
    "name": "hr_reports_print.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_reward_discipline.html",
    "name": "hr_reward_discipline.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_self_service.html",
    "name": "hr_self_service.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/hr_self_service_requests.html",
    "name": "hr_self_service_requests.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/kunye.html",
    "name": "kunye.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/list_workspace_macros.html",
    "name": "list_workspace_macros.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/login.html",
    "name": "login.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/management_workspace_macros.html",
    "name": "management_workspace_macros.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/manager_feedback_requests.html",
    "name": "manager_feedback_requests.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/manager_feedback_request_detail.html",
    "name": "manager_feedback_request_detail.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/manager_feedback_request_schedule.html",
    "name": "manager_feedback_request_schedule.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/messages_inbox.html",
    "name": "messages_inbox.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/messages_new.html",
    "name": "messages_new.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/messages_thread.html",
    "name": "messages_thread.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/my_performance_comparison.html",
    "name": "my_performance_comparison.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/notifications_list.html",
    "name": "notifications_list.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/org_units.html",
    "name": "org_units.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/org_units_list.html",
    "name": "org_units_list.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/org_unit_create.html",
    "name": "org_unit_create.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/org_unit_edit.html",
    "name": "org_unit_edit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/org_unit_form.html",
    "name": "org_unit_form.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_core_health.html",
    "name": "performance_core_health.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_evaluation_history.html",
    "name": "performance_evaluation_history.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_feedback_reports.html",
    "name": "performance_feedback_reports.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_feedback_request.html",
    "name": "performance_feedback_request.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_hierarchy_assignments.html",
    "name": "performance_hierarchy_assignments.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_history_import.html",
    "name": "performance_history_import.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_history_import_detail.html",
    "name": "performance_history_import_detail.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_low_score_processes.html",
    "name": "performance_low_score_processes.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_mail_reminders.html",
    "name": "performance_mail_reminders.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_mail_templates.html",
    "name": "performance_mail_templates.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_operations_center.html",
    "name": "performance_operations_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_pilot_simulation_center.html",
    "name": "performance_pilot_simulation_center.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_publish.html",
    "name": "performance_publish.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_publish_preflight.html",
    "name": "performance_publish_preflight.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_reports.html",
    "name": "performance_reports.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_reports_print.html",
    "name": "performance_reports_print.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_report_card.html",
    "name": "performance_report_card.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_scorecard_detail.html",
    "name": "performance_scorecard_detail.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_tasks.html",
    "name": "performance_tasks.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_task_health.html",
    "name": "performance_task_health.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_task_preflight.html",
    "name": "performance_task_preflight.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase1.html",
    "name": "performance_v2_phase1.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase2.html",
    "name": "performance_v2_phase2.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase3.html",
    "name": "performance_v2_phase3.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase3_assignment.html",
    "name": "performance_v2_phase3_assignment.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase5_dashboard.html",
    "name": "performance_v2_phase5_dashboard.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase5_publish.html",
    "name": "performance_v2_phase5_publish.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase5_scorecard.html",
    "name": "performance_v2_phase5_scorecard.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase6_dashboard.html",
    "name": "performance_v2_phase6_dashboard.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase6_print.html",
    "name": "performance_v2_phase6_print.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase7_hub.html",
    "name": "performance_v2_phase7_hub.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_v2_phase8_hub.html",
    "name": "performance_v2_phase8_hub.html",
    "suffix": ".html",
    "hits": [
      "phase",
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/performance_workspace_macros.html",
    "name": "performance_workspace_macros.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/periods.html",
    "name": "periods.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/period_create.html",
    "name": "period_create.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/period_edit.html",
    "name": "period_edit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/personnel_add.html",
    "name": "personnel_add.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  },
  {
    "path": "app/templates/personnel_edit.html",
    "name": "personnel_edit.html",
    "suffix": ".html",
    "hits": [
      "temp"
    ],
    "classification": "app_user_or_runtime_review"
  }
]
```

## Kullanıcıya Yansıyabilecek Teknik Dil Bulguları İlk 150

```json
[
  {
    "path": "app/templates/account.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 11,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 546,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz4_support_account_mobile.js') }}\"></script>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/account_change_password.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 9,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 464,
        "term": "faz",
        "sample": "<p>Birden fazla kelime, rakam ve özel karakter kullanmak şifrenizin dayanıklılığını artırır.</p>"
      },
      {
        "line": 503,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz4_support_account_mobile.js') }}\"></script>"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/templates/account_security_setup.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 9,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 459,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz4_support_account_mobile.js') }}\"></script>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/admin_ai_acceptance_pack.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 68,
        "term": "gate",
        "sample": "{% for gate in gates %}"
      },
      {
        "line": 72,
        "term": "gate",
        "sample": "<div class=\"fw-semibold\">{{ gate.label }}</div>"
      },
      {
        "line": 73,
        "term": "gate",
        "sample": "<span class=\"badge text-bg-{% if gate.status == 'pass' %}success{% elif gate.status == 'warn' %}warning{% else %}danger{% endif %}\">{{ gate.status }}</span>"
      },
      {
        "line": 75,
        "term": "gate",
        "sample": "<div class=\"small text-muted mt-2\">{{ gate.detail }}</div>"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/admin_ai_assignment_recommendations.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 27,
        "term": "gate",
        "sample": "<input type=\"text\" name=\"event_type\" value=\"{{ event_type or '' }}\" placeholder=\"delegated, uncovered\">"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/admin_ai_center.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 128,
        "term": "gate",
        "sample": "<a class=\"ai-link\" href=\"{{ safe_url_for('main.admin_ai_visibility_gate', fallback='#') }}\"><i class=\"fa-solid fa-lock\"></i> Görünürlük kapısı</a>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/admin_ai_executive_brief.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 15,
        "term": "json",
        "sample": "<a class=\"btn btn-outline-secondary\" href=\"{{ url_for('main.admin_ai_executive_brief_export_json', lookback_days=lookback_days) }}\">JSON</a>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/admin_ai_executive_report.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 62,
        "term": "json",
        "sample": "<p class=\"ai-sub\">CSV, JSON ve Markdown çıktıları yalnız özet, metrik, risk ve aksiyon notu verir. Ham AI metni, kişisel veri ve dosya içe aktarım satırı export edilmez.</p>"
      },
      {
        "line": 65,
        "term": "json",
        "sample": "<a class=\"ai-link\" href=\"{{ safe_url_for('main.admin_ai_executive_report_export_json', fallback='#', lookback_days=lookback_days, module_type=selected_module_type) }}\"><i class=\"fa-solid fa-code\"></i> JSON dışa aktar</a>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/admin_ai_feedback.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 11,
        "term": "faz",
        "sample": "<p class=\"ai-sub\">Bu ekran, AI yanıtlarının ne kadar faydalı bulunduğunu ve hangi modüllerde daha fazla düzeltme baskısı oluştuğunu görünür kılar.</p>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/admin_ai_final_live_hardening.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 126,
        "term": "phase",
        "sample": "{% for row in phase_gate_rows %}"
      },
      {
        "line": 128,
        "term": "phase",
        "sample": "<td><strong>Kontrol {{ row.phase }}</strong></td>"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": "<div class=\"ai-kicker\">Faz 12 · Final canlı sertleştirme</div>"
      },
      {
        "line": 13,
        "term": "faz",
        "sample": "<p class=\"ai-sub\">Bu ekran AI Karar Destek / Analiz Merkezi fazlarını canlıya hazırlayan son denetim yüzeyidir. DB yazımı, gerçek içe aktarım, ham AI metni gösterimi ve otomatik karar uygulaması yapmaz.</p>"
      },
      {
        "line": 77,
        "term": "faz",
        "sample": "<li class=\"ai-list-item\"><div><strong>Gerçek içe aktarım</strong><div class=\"ai-mini\">Excel/CSV verisi içeri alınmaz; Faz 7 önizleme çizgisi korunur.</div></div><span class=\"ai-badge success\">Yok</span></li>"
      },
      {
        "line": 120,
        "term": "faz",
        "sample": "<div class=\"ai-kicker\">Faz gate izleme listesi</div>"
      },
      {
        "line": 123,
        "term": "faz",
        "sample": "<tr><th>Faz</th><th>Başlık</th><th>Komut</th><th>Durum</th><th>Not</th></tr>"
      },
      {
        "line": 69,
        "term": "json",
        "sample": "<p class=\"ai-sub\">CSV, JSON ve Markdown çıktıları yalnız kalite kapısı, güvenlik özeti, risk metrikleri ve aksiyon notu içerir. Ham AI istem/yanıt metni, kişisel veri ve gerçek içe aktarım satırı export edilmez.</p>"
      },
      {
        "line": 72,
        "term": "json",
        "sample": "<a class=\"ai-link\" href=\"{{ safe_url_for('main.admin_ai_final_live_hardening_export_json', fallback='#', lookback_days=lookback_days) }}\"><i class=\"fa-solid fa-code\"></i> JSON dışa aktar</a>"
      },
      {
        "line": 54,
        "term": "gate",
        "sample": "{% for gate in readiness_gates %}"
      },
      {
        "line": 56,
        "term": "gate",
        "sample": "<td><strong>{{ gate.label }}</strong><div class=\"ai-mini\">{{ gate.key }}</div></td>"
      },
      {
        "line": 57,
        "term": "gate",
        "sample": "<td><span class=\"ai-badge {{ 'success' if gate.ok else 'warning' }}\">{{ gate.status }}</span></td>"
      },
      {
        "line": 58,
        "term": "gate",
        "sample": "<td>{{ gate.finding }}</td>"
      },
      {
        "line": 59,
        "term": "gate",
        "sample": "<td>{{ gate.action }}</td>"
      },
      {
        "line": 120,
        "term": "gate",
        "sample": "<div class=\"ai-kicker\">Faz gate izleme listesi</div>"
      },
      {
        "line": 126,
        "term": "gate",
        "sample": "{% for row in phase_gate_rows %}"
      }
    ],
    "hit_count": 16
  },
  {
    "path": "app/templates/admin_ai_go_live_readiness.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 15,
        "term": "json",
        "sample": "<a class=\"btn btn-outline-secondary\" href=\"{{ url_for('main.admin_ai_go_live_readiness_export_json', lookback_days=lookback_days) }}\">JSON</a>"
      },
      {
        "line": 32,
        "term": "gate",
        "sample": "{% for gate in gates %}"
      },
      {
        "line": 35,
        "term": "gate",
        "sample": "<div class=\"fw-semibold\">{{ gate.label }}</div>"
      },
      {
        "line": 37,
        "term": "gate",
        "sample": "<span class=\"badge text-bg-secondary\">{{ gate.owner }}</span>"
      },
      {
        "line": 38,
        "term": "gate",
        "sample": "<span class=\"badge text-bg-{% if gate.status == 'pass' %}success{% elif gate.status == 'warn' %}warning{% else %}danger{% endif %}\">{{ gate.status }}</span>"
      },
      {
        "line": 41,
        "term": "gate",
        "sample": "<div class=\"small text-muted mt-2\">{{ gate.detail }}</div>"
      }
    ],
    "hit_count": 6
  },
  {
    "path": "app/templates/admin_ai_management_pack.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 15,
        "term": "json",
        "sample": "<a class=\"btn btn-outline-secondary\" href=\"{{ url_for('main.admin_ai_management_pack_export_json', lookback_days=lookback_days) }}\">JSON</a>"
      },
      {
        "line": 113,
        "term": "gate",
        "sample": "{% for row in sections.go_live_gates %}"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/admin_ai_visibility_gate.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 31,
        "term": "gate",
        "sample": "<a class=\"ai-link\" href=\"{{ safe_url_for('main.admin_ai_visibility_gate_export', fallback='/admin/ai-visibility-gate/export', **filters) }}\"><i class=\"fa-solid fa-file-csv\"></i> Güvenli CSV</a>"
      },
      {
        "line": 52,
        "term": "gate",
        "sample": "<form class=\"ai-form-wrap\" method=\"get\" action=\"{{ safe_url_for('main.admin_ai_visibility_gate', fallback='/admin/ai-visibility-gate') }}\">"
      },
      {
        "line": 9,
        "term": "contract",
        "sample": ".vg-contract{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:14px}"
      },
      {
        "line": 10,
        "term": "contract",
        "sample": ".vg-contract .item{padding:12px;border-radius:16px;background:#fff;border:1px solid rgba(15,23,42,.08)}"
      },
      {
        "line": 11,
        "term": "contract",
        "sample": ".vg-contract .k{font-size:.72rem;color:#64748b;font-weight:900;text-transform:uppercase;letter-spacing:.03em}.vg-contract .v{margin-top:6px;font-weight:900;color:#111827}"
      },
      {
        "line": 17,
        "term": "contract",
        "sample": "@media (max-width:1200px){.vg-contract{grid-template-columns:repeat(2,minmax(0,1fr))}.vg-mini-matrix{grid-template-columns:repeat(2,minmax(0,1fr))}}"
      },
      {
        "line": 18,
        "term": "contract",
        "sample": "@media (max-width:768px){.vg-contract,.vg-mini-matrix{grid-template-columns:1fr}.vg-risk{width:40px;height:40px}}"
      },
      {
        "line": 40,
        "term": "contract",
        "sample": "<div class=\"vg-contract\">"
      },
      {
        "line": 93,
        "term": "contract",
        "sample": "<div class=\"vg-contract\">"
      },
      {
        "line": 94,
        "term": "contract",
        "sample": "<div class=\"item\"><div class=\"k\">DB yazımı</div><div class=\"v\">{{ 'Açık' if visibility_contract.DB_WRITE_ENABLED else 'Kapalı' }}</div></div>"
      },
      {
        "line": 95,
        "term": "contract",
        "sample": "<div class=\"item\"><div class=\"k\">AI nihai karar</div><div class=\"v\">{{ 'Açık' if visibility_contract.AI_FINAL_DECISION_ENABLED else 'Kapalı' }}</div></div>"
      },
      {
        "line": 96,
        "term": "contract",
        "sample": "<div class=\"item\"><div class=\"k\">Otomatik uygulama</div><div class=\"v\">{{ 'Açık' if visibility_contract.AI_AUTO_APPLY_ENABLED else 'Kapalı' }}</div></div>"
      }
    ],
    "hit_count": 12
  },
  {
    "path": "app/templates/admin_analysis_excel_preview.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 28,
        "term": "faz",
        "sample": "<p class=\"ai-sub\">En fazla {{ max_file_size_mb }} MB dosya analiz edilir. Dosya diske kaydedilmez; sonuç yalnızca bu sayfada gösterilir.</p>"
      },
      {
        "line": 122,
        "term": "faz",
        "sample": "Dosya yüklenene kadar hiçbir veri okunmaz. Yükleme sonrası yalnız güvenli analiz ve maskeli önizleme gösterilir; gerçek içe aktarım butonu bu fazda yoktur."
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/admin_analysis_recommendation_priority.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 18,
        "term": "contract",
        "sample": ".priority-contract{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:14px}"
      },
      {
        "line": 19,
        "term": "contract",
        "sample": ".priority-contract .item{padding:12px;border-radius:16px;background:#fff;border:1px solid rgba(15,23,42,.07)}"
      },
      {
        "line": 20,
        "term": "contract",
        "sample": ".priority-contract .k{font-size:.72rem;color:#6b7280;font-weight:900;text-transform:uppercase;letter-spacing:.03em}.priority-contract .v{margin-top:6px;font-weight:900;color:#111827}"
      },
      {
        "line": 21,
        "term": "contract",
        "sample": "@media (max-width:1200px){.priority-contract{grid-template-columns:repeat(2,minmax(0,1fr))}}"
      },
      {
        "line": 22,
        "term": "contract",
        "sample": "@media (max-width:768px){.priority-contract{grid-template-columns:1fr}.priority-rank{width:40px;height:40px}}"
      },
      {
        "line": 40,
        "term": "contract",
        "sample": "<div class=\"priority-contract\">"
      },
      {
        "line": 41,
        "term": "contract",
        "sample": "<div class=\"item\"><div class=\"k\">Nihai karar</div><div class=\"v\">{{ 'Açık' if safety_contract.AI_FINAL_DECISION_ENABLED else 'Kapalı' }}</div></div>"
      },
      {
        "line": 42,
        "term": "contract",
        "sample": "<div class=\"item\"><div class=\"k\">Otomatik uygulama</div><div class=\"v\">{{ 'Açık' if safety_contract.AI_AUTO_APPLY_ENABLED else 'Kapalı' }}</div></div>"
      },
      {
        "line": 43,
        "term": "contract",
        "sample": "<div class=\"item\"><div class=\"k\">DB yazımı</div><div class=\"v\">{{ 'Açık' if safety_contract.DB_WRITE_ENABLED else 'Kapalı' }}</div></div>"
      }
    ],
    "hit_count": 9
  },
  {
    "path": "app/templates/admin_analysis_visual_reports.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 153,
        "term": "contract",
        "sample": "<li class=\"ai-list-item\"><div><strong>DB yazımı</strong><div class=\"ai-mini\">Kontrol 8 servisinde yazma komutu bulunmaz.</div></div><span class=\"ai-badge success\">{{ 'Kapalı' if not read_only_contract.DB_WRITE_ENABLED else 'Açık' }}</span><"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/admin_dashboard.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 396,
        "term": "gate",
        "sample": "<span class=\"risk-mini\">Vekâlet {{ unit.delegated }}</span>"
      },
      {
        "line": 410,
        "term": "gate",
        "sample": "<div class=\"info-item\"><strong>Açıkta zincir:</strong> {{ coverage_summary.uncovered if coverage_summary else 0 }} · <strong>Muafiyet:</strong> {{ coverage_summary.exempted if coverage_summary else 0 }} · <strong>Vekâlet:</strong> {{ covera"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/admin_go_live_readiness.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 50,
        "term": "faz",
        "sample": "<p class=\"section-sub\">Yönetim ve BT için son turda en fazla değer taşıyan kısa okuma alanı.</p>"
      },
      {
        "line": 29,
        "term": "json",
        "sample": "<a class=\"btn-soft secondary\" href=\"{{ url_for('main.admin_go_live_readiness_export_json') }}\"><i class=\"fa-solid fa-code\"></i> JSON indir</a>"
      },
      {
        "line": 109,
        "term": "gate",
        "sample": "{% for gate in gates %}"
      },
      {
        "line": 111,
        "term": "gate",
        "sample": "<td>{{ gate.label }}</td>"
      },
      {
        "line": 112,
        "term": "gate",
        "sample": "<td><span class=\"badge {{ gate.status }}\">{{ 'Geçti' if gate.status == 'pass' else 'Uyarı' if gate.status == 'warn' else 'Blokaj' }}</span></td>"
      },
      {
        "line": 113,
        "term": "gate",
        "sample": "<td>{{ gate.owner }}</td>"
      },
      {
        "line": 114,
        "term": "gate",
        "sample": "<td>{{ gate.detail }}</td>"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/templates/admin_user_create.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 344,
        "term": "phase",
        "sample": "<div class=\"form-field\" data-bys360-marker=\"BYS360_PHASE2_ADMIN_USER_CREATE_CATEGORY_FIELD\">"
      },
      {
        "line": 291,
        "term": "faz",
        "sample": "Personelin kendisini amir olarak seçmesi engellenir ve aynı kişi birden fazla amir seviyesinde atanamaz. :contentReference[oaicite:2]{index=2}"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/admin_user_edit.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 465,
        "term": "phase",
        "sample": "<div class=\"form-field\" data-bys360-marker=\"BYS360_PHASE2_ADMIN_USER_EDIT_CATEGORY_FIELD\">"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/announcements_list.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 130,
        "term": "sync",
        "sample": "function sync(){"
      },
      {
        "line": 139,
        "term": "sync",
        "sample": "sync();"
      },
      {
        "line": 141,
        "term": "sync",
        "sample": "function syncToolbarState(){"
      },
      {
        "line": 147,
        "term": "sync",
        "sample": "syncToolbarState();"
      },
      {
        "line": 148,
        "term": "sync",
        "sample": "if (toolbarToggle && shell) toolbarToggle.addEventListener('click', function(){ shell.classList.toggle('filters-collapsed'); localStorage.setItem(toolbarKey, shell.classList.contains('filters-collapsed') ? '1' : '0'); syncToolbarState(); })"
      },
      {
        "line": 152,
        "term": "sync",
        "sample": "sync();"
      }
    ],
    "hit_count": 6
  },
  {
    "path": "app/templates/announcement_new.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 359,
        "term": "sync",
        "sample": "function syncTone(recipientCount) {"
      },
      {
        "line": 373,
        "term": "sync",
        "sample": "function syncCharCount() {"
      },
      {
        "line": 431,
        "term": "sync",
        "sample": "syncRecipientPreview();"
      },
      {
        "line": 432,
        "term": "sync",
        "sample": "syncSelectionSummary();"
      },
      {
        "line": 435,
        "term": "sync",
        "sample": "function syncRecipientPreview() {"
      },
      {
        "line": 440,
        "term": "sync",
        "sample": "syncTone(totalUserCount);"
      },
      {
        "line": 447,
        "term": "sync",
        "sample": "syncTone(count);"
      },
      {
        "line": 451,
        "term": "sync",
        "sample": "function syncSelectionSummary(){"
      },
      {
        "line": 476,
        "term": "sync",
        "sample": "targetValues.addEventListener(\"change\", function(){ syncRecipientPreview(); syncSelectionSummary(); });"
      },
      {
        "line": 483,
        "term": "sync",
        "sample": "syncRecipientPreview();"
      },
      {
        "line": 344,
        "term": "json",
        "sample": "const previewCounts = {{ preview_counts|tojson }};"
      },
      {
        "line": 386,
        "term": "json",
        "sample": "localStorage.setItem(draftKey, JSON.stringify(payload));"
      },
      {
        "line": 395,
        "term": "json",
        "sample": "const payload = JSON.parse(raw);"
      }
    ],
    "hit_count": 13
  },
  {
    "path": "app/templates/assignment_audit_detail.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 15,
        "term": "gate",
        "sample": "<div class=\"field\"><label>Olay tipi</label><input type=\"text\" name=\"event_type\" value=\"{{ event_type or '' }}\" placeholder=\"delegated / uncovered / chain_issue\"></div>"
      },
      {
        "line": 58,
        "term": "gate",
        "sample": "<div class=\"summary-card\"><div class=\"summary-label\">Vekâlet</div><div class=\"summary-value\">{{ summary.delegated or 0 }}</div></div>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/assistant_training_bank.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 286,
        "term": "sync",
        "sample": "btn.addEventListener('click', async () => {"
      },
      {
        "line": 68,
        "term": "gate",
        "sample": ".bys360-teach-gates{display:grid;gap:10px}"
      },
      {
        "line": 237,
        "term": "gate",
        "sample": "<div class=\"bys360-teach-gates\">"
      },
      {
        "line": 238,
        "term": "gate",
        "sample": "<div class=\"bys360-teach-gate\"><span class=\"ok\"><i class=\"fa-solid fa-check\"></i></span><div><b>Kanonik Asistan</b><span>Tek JS/CSS include, tek root ve temiz base yerleşimi.</span></div></div>"
      },
      {
        "line": 239,
        "term": "gate",
        "sample": "<div class=\"bys360-teach-gate\"><span class=\"ok\"><i class=\"fa-solid fa-check\"></i></span><div><b>Güvenli Menü Haritası</b><span>Kırık link ve eski URL yönlendirmelerini engeller.</span></div></div>"
      },
      {
        "line": 240,
        "term": "gate",
        "sample": "<div class=\"bys360-teach-gate\"><span class=\"ok\"><i class=\"fa-solid fa-check\"></i></span><div><b>Ekran Zekâsı</b><span>URL, menü, başlık, breadcrumb, buton ve tablo ipuçlarını puanlar.</span></div></div>"
      },
      {
        "line": 241,
        "term": "gate",
        "sample": "<div class=\"bys360-teach-gate\"><span class=\"ok\"><i class=\"fa-solid fa-check\"></i></span><div><b>Repo Hijyeni</b><span>Teknik veya alaycı kullanıcı dili canlı ekrana taşınmaz.</span></div></div>"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/templates/base.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 23,
        "term": "phase",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/mobile_phase_m1.css') }}\">"
      },
      {
        "line": 28,
        "term": "phase",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/phase5_5_scorecard_mobile.css') }}\">"
      },
      {
        "line": 431,
        "term": "phase",
        "sample": "{% set is_tasks_active = current_ep in ['main.performance_tasks','main.performance_evaluate','main.performance_v2_phase3_dashboard','main.performance_v2_phase3_board','main.performance_v2_phase3_assignment','main.performance_v2_phase4_dashb"
      },
      {
        "line": 432,
        "term": "phase",
        "sample": "{% set is_scorecard_active = current_ep in ['main.performance_scorecard','main.performance_v2_phase5_scorecard','main.performance_v2_phase5_dashboard'] or current_ep.startswith('main.performance_scorecard_') or current_ep.startswith('main.s"
      },
      {
        "line": 434,
        "term": "phase",
        "sample": "{% set is_publish_active = current_ep == 'main.performance_v2_phase5_publish' or current_ep == 'main.performance_v2_phase5_publish_preflight' or current_ep.startswith('main.performance_publish') or current_ep.startswith('main.performance_un"
      },
      {
        "line": 437,
        "term": "phase",
        "sample": "{% set is_perf_open = current_ep.startswith('main.performance_criteria') or current_ep.startswith('main.performance_period') or current_ep.startswith('main.performance_task_management') or current_ep.startswith('main.performance_hierarchy')"
      },
      {
        "line": 1030,
        "term": "phase",
        "sample": "<script src=\"{{ url_for('static', filename='js/mobile_phase_m1.js') }}\"></script>"
      },
      {
        "line": 24,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz1_mobile_foundation.css') }}\">"
      },
      {
        "line": 252,
        "term": "faz",
        "sample": "<!-- BYS360_MOBILE_PWA_FAZ2_V1_HEAD_INCLUDE -->"
      },
      {
        "line": 260,
        "term": "faz",
        "sample": "<!-- /BYS360_MOBILE_PWA_FAZ2_V1_HEAD_INCLUDE -->"
      },
      {
        "line": 262,
        "term": "faz",
        "sample": "<!-- BYS360_MOBILE_APP_FAZ3_V1_HEAD_INCLUDE -->"
      },
      {
        "line": 263,
        "term": "faz",
        "sample": "<!-- /BYS360_MOBILE_APP_FAZ3_V1_HEAD_INCLUDE -->"
      },
      {
        "line": 431,
        "term": "faz",
        "sample": "{% set is_tasks_active = current_ep in ['main.performance_tasks','main.performance_evaluate','main.performance_v2_phase3_dashboard','main.performance_v2_phase3_board','main.performance_v2_phase3_assignment','main.performance_v2_phase4_dashb"
      },
      {
        "line": 432,
        "term": "faz",
        "sample": "{% set is_scorecard_active = current_ep in ['main.performance_scorecard','main.performance_v2_phase5_scorecard','main.performance_v2_phase5_dashboard'] or current_ep.startswith('main.performance_scorecard_') or current_ep.startswith('main.s"
      },
      {
        "line": 434,
        "term": "faz",
        "sample": "{% set is_publish_active = current_ep == 'main.performance_v2_phase5_publish' or current_ep == 'main.performance_v2_phase5_publish_preflight' or current_ep.startswith('main.performance_publish') or current_ep.startswith('main.performance_un"
      },
      {
        "line": 550,
        "term": "faz",
        "sample": "{% if menu_map.get('performance_meeting_p3_reminders', False) %}{{ nav_item(safe_url_for('main.performance_meeting_p3_reminders', fallback='/performance/meeting-development/faz9'), 'fa-bell', 'Hatırlatma ve Aksatan Amirler', current_path.st"
      },
      {
        "line": 556,
        "term": "faz",
        "sample": "{% if menu_map.get('performance_development_guidance', False) %}{{ nav_item(safe_url_for('main.performance_meeting_p4_development_guidance', fallback='/performance/meeting-development/faz10'), 'fa-seedling', 'Gelişim Rehberi', current_path."
      },
      {
        "line": 803,
        "term": "sync",
        "sample": "function sync(){"
      },
      {
        "line": 814,
        "term": "sync",
        "sample": "if(typeof mq.addEventListener==='function') mq.addEventListener('change',sync); else if(typeof mq.addListener==='function') mq.addListener(sync);"
      },
      {
        "line": 815,
        "term": "sync",
        "sample": "sync();"
      }
    ],
    "hit_count": 27
  },
  {
    "path": "app/templates/dashboard.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 220,
        "term": "json",
        "sample": "<script id=\"dashboard-rebuild-payload\" type=\"application/json\">{{ d|tojson }}</script>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/evaluation_form.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 3,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 15,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 16,
        "term": "phase",
        "sample": "{% set phase5_guide_title = \"Bu ekranda değerlendirme kararı güvenli biçimde tamamlanır\" %}"
      },
      {
        "line": 17,
        "term": "phase",
        "sample": "{% set phase5_guide_text = \"Puan girişleri, zorunlu açıklamalar ve süreç adımları aynı yüzeyde toplandığı için yönetici yanlış gönderim yapmadan önce formu kontrol edebilir.\" %}"
      },
      {
        "line": 18,
        "term": "phase",
        "sample": "{% set phase5_guide_points = ["
      },
      {
        "line": 23,
        "term": "phase",
        "sample": "{% set phase5_guide_note = \"Bu ekran, kurumsal işleyişe uygun olarak kör değerlendirme mantığıyla değil; görünür, kontrollü ve denetlenebilir akış mantığıyla kullanılmalıdır.\" %}"
      },
      {
        "line": 24,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_microguide.html\" %}"
      },
      {
        "line": 26,
        "term": "phase",
        "sample": "{% set phase5_3_comment_rule_from_settings = phase5_3_comment_rule_from_settings if phase5_3_comment_rule_from_settings is defined else true %}"
      },
      {
        "line": 27,
        "term": "phase",
        "sample": "{% set phase5_3_interim_ctx = interim_notes_context if interim_notes_context is defined and interim_notes_context else {} %}"
      },
      {
        "line": 68,
        "term": "workflow",
        "sample": "<span class=\"workspace-badge\"><i class=\"fa-solid fa-diagram-project\"></i> {{ workflow.label }}</span>"
      },
      {
        "line": 70,
        "term": "workflow",
        "sample": "{% if assignment.manager_level == 1 and workflow.can_level_1_edit %}"
      },
      {
        "line": 74,
        "term": "workflow",
        "sample": "{% elif assignment.manager_level == 2 and workflow.can_level_2_return %}"
      },
      {
        "line": 149,
        "term": "workflow",
        "sample": "<div class=\"info-value\">{{ workflow.label }}</div>"
      },
      {
        "line": 154,
        "term": "workflow",
        "sample": "{% if assignment.manager_level == 1 and workflow.can_level_1_edit %}"
      },
      {
        "line": 158,
        "term": "workflow",
        "sample": "{% elif assignment.manager_level == 2 and workflow.can_level_2_return %}"
      },
      {
        "line": 189,
        "term": "workflow",
        "sample": "<div class=\"info-value\">{{ workflow_return_note or '-' }}</div>"
      },
      {
        "line": 258,
        "term": "workflow",
        "sample": "placeholder=\"Genel değerlendirmenizi yazınız...\" {% if assignment.manager_level == 1 and not workflow.can_level_1_edit %}readonly{% endif %}>{{ current_general_comment or '' }}</textarea>"
      },
      {
        "line": 272,
        "term": "workflow",
        "sample": "{% if assignment.manager_level != 1 or workflow.can_level_1_edit %}"
      },
      {
        "line": 335,
        "term": "workflow",
        "sample": "{% if current_item and (current_item.score|int == value) %}checked{% endif %} {% if assignment.manager_level == 1 and not workflow.can_level_1_edit %}disabled{% endif %}>"
      }
    ],
    "hit_count": 20
  },
  {
    "path": "app/templates/evaluation_tasks.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 719,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase4_assignment', assignment_id=assignment.id) }}\""
      },
      {
        "line": 715,
        "term": "workflow",
        "sample": "<span class=\"pill workflow-{{ assignment.workflow_badge_class|default('neutral') }}\">{{ assignment.workflow_label|default('1. amirde taslak') }}</span>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/excel_import.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 289,
        "term": "phase",
        "sample": "<div class=\"hint-box\" data-bys360-marker=\"BYS360_PHASE2_3_IMPORT_CATEGORY_HINT\">"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/feedback_go_live_center.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 10,
        "term": "phase",
        "sample": "{% set phase5_guide_title = \"Bu ekran canlı öncesi son karar yüzeyidir\" %}"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": "{% set phase5_guide_text = \"Görevler, yayın durumu, açık talepler ve geciken görüşmeler aynı merkezde birleştiği için performans modülünün canlıya ne kadar hazır olduğunu tek ekranda okuyabilirsiniz.\" %}"
      },
      {
        "line": 12,
        "term": "phase",
        "sample": "{% set phase5_guide_points = ["
      },
      {
        "line": 17,
        "term": "phase",
        "sample": "{% set phase5_guide_note = \"Bu merkez, teknik ayrıntı göstermeden yöneticiye karar verebileceği kadar net ama kurumsal bir özet sunmak için düzenlendi.\" %}"
      },
      {
        "line": 18,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_microguide.html\" %}"
      },
      {
        "line": 105,
        "term": "phase",
        "sample": "<a class=\"mini-btn\" href=\"{{ url_for('main.performance_v2_phase5_publish_preflight', period_id=active_period.id if active_period else '') }}\"><i class=\"fa-solid fa-list-check\"></i> Ön Kontrol</a>"
      },
      {
        "line": 223,
        "term": "endpoint",
        "sample": "{% for item in endpoint_checks %}"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/templates/feedback_meetings_list.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 275,
        "term": "sync",
        "sample": "function syncToolbarState(){"
      },
      {
        "line": 284,
        "term": "sync",
        "sample": "syncToolbarState();"
      },
      {
        "line": 290,
        "term": "sync",
        "sample": "syncToolbarState();"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/templates/hierarchy_assignments.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 292,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_4_HIERARCHY_ASSIGNMENT_FORM #}"
      },
      {
        "line": 293,
        "term": "phase",
        "sample": "{% set phase4_4_show_third_form = phase4_4_should_show_third_supervisor_column([], selected_value=selected_manager_3_id, allow_setting=True) %}"
      },
      {
        "line": 327,
        "term": "phase",
        "sample": "{% if phase4_4_show_third_form %}"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/templates/home.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 20,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/ai_decision_faz12.css') }}?v=home-karar-destek-karti-v1\">"
      },
      {
        "line": 35,
        "term": "faz",
        "sample": "<div class=\"home-faz1-shell\">"
      },
      {
        "line": 36,
        "term": "faz",
        "sample": "<section class=\"home-faz1-hero\">"
      },
      {
        "line": 37,
        "term": "faz",
        "sample": "<div class=\"home-faz1-hero-main\">"
      },
      {
        "line": 38,
        "term": "faz",
        "sample": "<div class=\"home-faz1-kicker\"><i class=\"fa-solid fa-location-dot\"></i> {{ weather.location_name|default('Gelibolu Tarihi Alan', true) }}</div>"
      },
      {
        "line": 43,
        "term": "faz",
        "sample": "<div class=\"home-faz1-actions\">"
      },
      {
        "line": 44,
        "term": "faz",
        "sample": "<a href=\"{{ safe_url_for('main.performance_tasks', fallback='#') }}\" class=\"home-faz1-btn primary\"><i class=\"fa-solid fa-list-check\"></i> Görevlerime Git</a>"
      },
      {
        "line": 45,
        "term": "faz",
        "sample": "<a href=\"{{ safe_url_for('main.dashboard', fallback='#') }}\" class=\"home-faz1-btn\"><i class=\"fa-solid fa-chart-line\"></i> Dashboard</a>"
      },
      {
        "line": 46,
        "term": "faz",
        "sample": "<a href=\"{{ safe_url_for('main.support_index', fallback='#') }}\" class=\"home-faz1-btn\"><i class=\"fa-solid fa-circle-info\"></i> Yardım Merkezi</a>"
      },
      {
        "line": 51,
        "term": "faz",
        "sample": "<aside class=\"home-faz1-weather-card home-weather-executive is-{{ weather.status|default('fallback', true) }}\">"
      },
      {
        "line": 130,
        "term": "endpoint",
        "sample": "<a href=\"{{ safe_url_for(item.endpoint, fallback='#') }}\" class=\"home-faz1-quick-card tone-{{ item.tone }}\">"
      },
      {
        "line": 175,
        "term": "endpoint",
        "sample": "<a href=\"{{ safe_url_for(card.endpoint, fallback='#') }}\" class=\"home-faz1-op-card\">"
      },
      {
        "line": 204,
        "term": "gate",
        "sample": "{% include 'ai_decision/_final_gate_panel.html' ignore missing %}"
      }
    ],
    "hit_count": 13
  },
  {
    "path": "app/templates/hr_attendance.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 622,
        "term": "sync",
        "sample": "function syncAttendanceDefaults(){"
      },
      {
        "line": 629,
        "term": "sync",
        "sample": "function syncPerformanceMode(){"
      },
      {
        "line": 634,
        "term": "sync",
        "sample": "if(typeSelect){ typeSelect.addEventListener('change', syncAttendanceDefaults); }"
      },
      {
        "line": 635,
        "term": "sync",
        "sample": "if(perfMode){ perfMode.addEventListener('change', syncPerformanceMode); }"
      },
      {
        "line": 636,
        "term": "sync",
        "sample": "if(managerCheckbox){ managerCheckbox.addEventListener('change', syncAttendanceDefaults); }"
      },
      {
        "line": 637,
        "term": "sync",
        "sample": "syncAttendanceDefaults();"
      },
      {
        "line": 638,
        "term": "sync",
        "sample": "syncPerformanceMode();"
      },
      {
        "line": 308,
        "term": "exception",
        "sample": "<select name=\"exception_type\" required data-role=\"attendance-type\">"
      },
      {
        "line": 424,
        "term": "exception",
        "sample": "<option value=\"{{ row.id }}\">{{ row.user.full_name if row.user else '-' }} · {{ row.record_date }} · {{ row.exception_type }}</option>"
      },
      {
        "line": 492,
        "term": "exception",
        "sample": "<td>{{ attendance_type_label(row.exception_type) }}</td>"
      },
      {
        "line": 106,
        "term": "gate",
        "sample": "{% if selected_user_guard.has_covering_delegation and selected_user_guard.covering_delegation and selected_user_guard.covering_delegation.delegate_user %}"
      },
      {
        "line": 107,
        "term": "gate",
        "sample": "<div style=\"margin-top:10px;\">Mevcut kapsayan vekâlet: <strong>{{ selected_user_guard.covering_delegation.delegate_user.full_name }}</strong></div>"
      },
      {
        "line": 351,
        "term": "gate",
        "sample": "<select name=\"delegate_user_id\">"
      },
      {
        "line": 353,
        "term": "gate",
        "sample": "{% for user in delegate_candidates %}"
      },
      {
        "line": 403,
        "term": "gate",
        "sample": "<select name=\"delegate_user_id\" required>"
      },
      {
        "line": 556,
        "term": "gate",
        "sample": "<td>{{ row.delegate.full_name if row.delegate else '-' }}</td>"
      }
    ],
    "hit_count": 16
  },
  {
    "path": "app/templates/hr_leave.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 11,
        "term": "faz",
        "sample": "<style>@import url(\"{{ url_for('static', filename='css/faz3_communication_hr_mobile.css') }}\");</style>"
      },
      {
        "line": 741,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz3_communication_hr_mobile.js') }}\"></script>"
      },
      {
        "line": 718,
        "term": "sync",
        "sample": "function syncLeaveForm(){"
      },
      {
        "line": 728,
        "term": "sync",
        "sample": "function syncPerformanceMode(){"
      },
      {
        "line": 732,
        "term": "sync",
        "sample": "if(leaveType){ leaveType.addEventListener('change', syncLeaveForm); }"
      },
      {
        "line": 733,
        "term": "sync",
        "sample": "if(startDate){ startDate.addEventListener('change', syncLeaveForm); }"
      },
      {
        "line": 734,
        "term": "sync",
        "sample": "if(perfMode){ perfMode.addEventListener('change', syncPerformanceMode); }"
      },
      {
        "line": 735,
        "term": "sync",
        "sample": "if(managerCheckbox){ managerCheckbox.addEventListener('change', syncLeaveForm); }"
      },
      {
        "line": 736,
        "term": "sync",
        "sample": "syncLeaveForm();"
      },
      {
        "line": 737,
        "term": "sync",
        "sample": "syncPerformanceMode();"
      },
      {
        "line": 21,
        "term": "gate",
        "sample": "{% set _delegated_open_assignments = _delegation_health.delegated_open_assignments if _delegation_health and _delegation_health.delegated_open_assignments is defined else 0 %}"
      },
      {
        "line": 210,
        "term": "gate",
        "sample": "{% if selected_user_guard.has_covering_delegation and selected_user_guard.covering_delegation and selected_user_guard.covering_delegation.delegate_user %}"
      },
      {
        "line": 211,
        "term": "gate",
        "sample": "<div style=\"margin-top:10px;\">Mevcut kapsayan vekâlet: <strong>{{ selected_user_guard.covering_delegation.delegate_user.full_name }}</strong></div>"
      },
      {
        "line": 303,
        "term": "gate",
        "sample": "<div class=\"value\">{{ _delegated_open_assignments }}</div>"
      },
      {
        "line": 331,
        "term": "gate",
        "sample": "<td>{{ row.delegate.full_name if row.delegate is defined and row.delegate else (row.delegate_name if row.delegate_name is defined else '-') }}</td>"
      },
      {
        "line": 504,
        "term": "gate",
        "sample": "<select name=\"delegate_user_id\">"
      },
      {
        "line": 506,
        "term": "gate",
        "sample": "{% for user in delegate_candidates %}"
      }
    ],
    "hit_count": 17
  },
  {
    "path": "app/templates/hr_management.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 167,
        "term": "gate",
        "sample": "<td>{{ row.delegate.full_name if row.delegate else '-' }}</td>"
      },
      {
        "line": 188,
        "term": "gate",
        "sample": "<td>{{ row.delegate.full_name if row.delegate else '-' }}</td>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/hr_personnel_operations.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 202,
        "term": "faz",
        "sample": "<div class=\"help-note\">Aynı personele ait birden fazla belgeyi tek hamlede yükleyin. Dosya adı başlığa otomatik işlenir; isterseniz ortak ön ek verebilirsiniz.</div>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/hr_reports.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 46,
        "term": "json",
        "sample": "<div class=\"bys-pro-chart compact\"><canvas data-bys-chart=\"bar\" data-labels='{{ [\"İzin\", \"Devamsızlık\", \"Vekâlet\", \"Birim\"]|tojson }}' data-datasets='{{ [{\"label\":\"Personel hareketleri\",\"data\":[leave_count|default(0,true), attendance_count|"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/login.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 15,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz1_mobile_foundation.css') }}\">"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/manager_feedback_request_schedule.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 229,
        "term": "sync",
        "sample": "function syncSummary(){"
      },
      {
        "line": 292,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 293,
        "term": "sync",
        "sample": "syncRemotePreview();"
      },
      {
        "line": 306,
        "term": "sync",
        "sample": "function syncRemotePreview(){"
      },
      {
        "line": 331,
        "term": "sync",
        "sample": "el.addEventListener('input', syncSummary);"
      },
      {
        "line": 333,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 335,
        "term": "sync",
        "sample": "syncRemotePreview();"
      },
      {
        "line": 339,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 340,
        "term": "sync",
        "sample": "syncRemotePreview();"
      },
      {
        "line": 321,
        "term": "json",
        "sample": ".then(function(response){ return response.json(); })"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/templates/messages_thread.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 91,
        "term": "json",
        "sample": "<button type=\"button\" class=\"msg-mini-btn\" onclick=\"openEditModal('{{ message.id }}', {{ message.body|tojson }})\">"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/my_performance_comparison.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 49,
        "term": "json",
        "sample": "<div class=\"bys-pro-chart compact\"><canvas data-bys-chart=\"line\" data-labels='{{ timeline|default([])|map(attribute=\"title\")|list|tojson }}' data-datasets='{{ [{\"label\":\"Puan\",\"data\":timeline|default([])|map(attribute=\"score\")|list}]|tojson"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/notifications_list.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 7,
        "term": "faz",
        "sample": "<style>@import url(\"{{ url_for('static', filename='css/faz3_communication_hr_mobile.css') }}\");</style>"
      },
      {
        "line": 404,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz3_communication_hr_mobile.js') }}\"></script>"
      },
      {
        "line": 336,
        "term": "sync",
        "sample": "function syncFieldContainer(container){"
      },
      {
        "line": 347,
        "term": "sync",
        "sample": "function syncSelection(){"
      },
      {
        "line": 351,
        "term": "sync",
        "sample": "syncFieldContainer(bulkDeleteFields);"
      },
      {
        "line": 352,
        "term": "sync",
        "sample": "syncFieldContainer(bulkReadFields);"
      },
      {
        "line": 353,
        "term": "sync",
        "sample": "syncFieldContainer(bulkUnreadFields);"
      },
      {
        "line": 359,
        "term": "sync",
        "sample": "function syncCounter(){"
      },
      {
        "line": 370,
        "term": "sync",
        "sample": "syncCounter();"
      },
      {
        "line": 371,
        "term": "sync",
        "sample": "syncSelection();"
      },
      {
        "line": 382,
        "term": "sync",
        "sample": "bulkCheckboxes.forEach(cb => cb.addEventListener('change', syncSelection));"
      },
      {
        "line": 388,
        "term": "sync",
        "sample": "syncSelection();"
      }
    ],
    "hit_count": 12
  },
  {
    "path": "app/templates/performance_core_health.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 11,
        "term": "phase",
        "sample": "<section class=\"ch-card ch-hero\"><div><span class=\"ch-kicker\"><i class=\"fa-solid fa-shield-heart\"></i> {{ readiness.label }}</span><h2 class=\"ch-title\">BYS360 çekirdeği için son güçlendirme kapısı</h2><p class=\"ch-text\">Bu panel teknik temi"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/performance_evaluation_history.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_scorecard_ui_styles.html\" ignore missing %}"
      },
      {
        "line": 19,
        "term": "phase",
        "sample": "{# BYS360_PHASE2_5_SCORECARD_CATEGORY_AVERAGE_CONTEXT #}"
      },
      {
        "line": 22,
        "term": "phase",
        "sample": "<div class=\"card shadow-sm border-0 h-100\" data-bys360-marker=\"BYS360_PHASE2_5_SCORECARD_CATEGORY_AVERAGE_CARD\"><div class=\"card-body\"><div class=\"text-muted small mb-1\">Kategori Ortalaması</div><div class=\"fs-4 fw-semibold\">{{ '%.2f'|forma"
      },
      {
        "line": 87,
        "term": "phase",
        "sample": "<div>{{ row.from_status_label|phase5_4_status_label }} → {{ row.to_status_label|phase5_4_status_label }}</div>"
      },
      {
        "line": 119,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_BOUND #}"
      },
      {
        "line": 120,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_BOUND #}"
      },
      {
        "line": 115,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ11_PANEL_INCLUDED #}"
      },
      {
        "line": 65,
        "term": "workflow",
        "sample": "<div class=\"col-md-3\"><strong>İş Akışı:</strong> {{ evaluation.workflow_status or '-' }}</div>"
      }
    ],
    "hit_count": 9
  },
  {
    "path": "app/templates/performance_hierarchy_assignments.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 316,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_4_PERFORMANCE_HIERARCHY_COLUMN #}"
      },
      {
        "line": 317,
        "term": "phase",
        "sample": "{% set phase4_4_show_third_col = phase4_4_should_show_third_supervisor_column(rows) %}"
      },
      {
        "line": 325,
        "term": "phase",
        "sample": "{% if phase4_4_show_third_col %}<th>3. Amir</th>{% endif %}"
      },
      {
        "line": 357,
        "term": "phase",
        "sample": "{% if phase4_4_show_third_col %}"
      },
      {
        "line": 408,
        "term": "phase",
        "sample": "{% if phase4_4_show_third_col %}"
      }
    ],
    "hit_count": 5
  },
  {
    "path": "app/templates/performance_history_import_detail.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 120,
        "term": "json",
        "sample": "{% set meta = row.raw_payload_json.get('_history_meta', {}) if row.raw_payload_json else {} %}"
      },
      {
        "line": 166,
        "term": "json",
        "sample": "<pre class=\"mono\" style=\"white-space:pre-wrap;max-width:440px;\">{{ row.raw_payload_json | tojson(indent=2) }}</pre>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/performance_low_score_processes.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "{# BYS360_LIVE_HARDENING_PHASE1_12_PHASE6_RUNTIME_ALIGNMENT #}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V5 #}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V4 #}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V3 #}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V2 #}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "{# BYS360_PHASE6_6_SECOND_LOW_SCORE_PROCESS_V2 #}"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 14,
        "term": "phase",
        "sample": "<!-- BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_FORCE_TEMPLATE -->"
      },
      {
        "line": 15,
        "term": "phase",
        "sample": "<section class=\"phase6-4-approval-panel\">"
      },
      {
        "line": 23,
        "term": "phase",
        "sample": "<section class=\"phase6-4-history\">"
      },
      {
        "line": 4,
        "term": "faz",
        "sample": "{# BYS360_CANLI_SAGLAMLASTIRMA_FAZ1_6_LOW_SCORE_TEMPLATE #}"
      },
      {
        "line": 112,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ6_LOW_PERFORMANCE_PANEL_INCLUDE #}"
      },
      {
        "line": 113,
        "term": "faz",
        "sample": "{% include \"ai_decision/_faz6_low_performance_approval_panel.html\" ignore missing %}"
      },
      {
        "line": 166,
        "term": "sync",
        "sample": "<form method=\"post\" action=\"{{ url_for('main.performance_low_score_process_sync', period_id=period.id) }}\" class=\"performance-toolbar\">"
      },
      {
        "line": 5,
        "term": "gate",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V5 #}"
      },
      {
        "line": 6,
        "term": "gate",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V4 #}"
      },
      {
        "line": 7,
        "term": "gate",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V3 #}"
      },
      {
        "line": 8,
        "term": "gate",
        "sample": "{# BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_V2 #}"
      },
      {
        "line": 14,
        "term": "gate",
        "sample": "<!-- BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_FORCE_TEMPLATE -->"
      },
      {
        "line": 40,
        "term": "gate",
        "sample": "<!-- BYS360_PHASE6_7_FINAL_GATE_ALIGNMENT_FORCE_TEMPLATE -->"
      }
    ],
    "hit_count": 24
  },
  {
    "path": "app/templates/performance_operations_center.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 8,
        "term": "phase",
        "sample": "{% set phase5_guide_title = \"Bu ekran performans operasyonunu tek bakışta toplar\" %}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "{% set phase5_guide_text = \"Görev ön kontrolü, yayın güvenliği, sağlık raporu ve son işlem logları birlikte okunarak canlı öncesi son operasyon kararı hızla verilebilir.\" %}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": "{% set phase5_guide_points = ["
      },
      {
        "line": 15,
        "term": "phase",
        "sample": "{% set phase5_guide_note = \"Bu yüzey, teknik ekip ile yönetim arasında ortak bir okuma alanı oluşturmak için daha yalın ve daha güven veren bir dilde düzenlendi.\" %}"
      },
      {
        "line": 16,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_microguide.html\" %}"
      },
      {
        "line": 54,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase5_publish_preflight', period_id=period.id if period else None) }}\" class=\"btn-soft secondary\"><i class=\"fa-solid fa-share-nodes\"></i> Yayın ön kontrol</a>"
      },
      {
        "line": 106,
        "term": "faz",
        "sample": "<p class=\"section-sub\">Canlıya çıkışı doğrudan yavaşlatan başlıklar burada birleşik görünür. Aynı sorun birden fazla ekranda tekrar ediyorsa bunu tek merkezden fark etmek kolaylaşır.</p>"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/templates/performance_pilot_simulation_center.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 146,
        "term": "phase",
        "sample": "{% if 'main.performance_v2_phase5_publish_preflight' in current_app.view_functions %}"
      },
      {
        "line": 147,
        "term": "phase",
        "sample": "<a class=\"mini-link\" href=\"{{ url_for('main.performance_v2_phase5_publish_preflight') }}\"><div>Yayın Ön Kontrol</div><span>Personel görünürlük kapısı</span></a>"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/performance_publish.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/performance_publish_preflight.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 32,
        "term": "phase",
        "sample": "<a class=\"btn-soft\" href=\"{{ url_for('main.performance_v2_phase5_publish', period_id=period.id if period else None) }}\"><i class=\"fa-solid fa-arrow-left\"></i> Yayın ekranı</a>"
      },
      {
        "line": 34,
        "term": "phase",
        "sample": "<form method=\"post\" action=\"{{ url_for('main.performance_v2_phase5_publish', period_id=period.id) }}\" style=\"display:inline-flex;gap:10px;flex-wrap:wrap;\">"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/templates/performance_reports.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_4_TEMPLATE_GUARD_NOTE"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "3. amir ekran blokları phase4_4_show_third_col koşuluyla yönetilir."
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_4_THIRD_SUPERVISOR_COLUMN_CONDITIONAL_FLAG #}"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": "{% set phase4_4_show_third_col = phase4_4_show_third_col|default(show_third_supervisor_column|default(third_supervisor_show_column|default(has_third_supervisor|default(false)))) %}"
      },
      {
        "line": 25,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 440,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_4_PERFORMANCE_REPORTS_COLUMN #}"
      },
      {
        "line": 441,
        "term": "phase",
        "sample": "{% if phase4_4_show_third_col %} {# BYS360_PHASE4_4_THIRD_SUPERVISOR_COLUMN_CONDITIONAL_START #}"
      },
      {
        "line": 442,
        "term": "phase",
        "sample": "{% set phase4_4_show_third_col = phase4_4_should_show_third_supervisor_column(evaluations) %}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/templates/performance_reports_print.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 3,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 13,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 67,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_4_PRINT_REPORTS_COLUMN #}"
      },
      {
        "line": 68,
        "term": "phase",
        "sample": "{% set phase4_4_show_third_col = phase4_4_should_show_third_supervisor_column(evaluations if evaluations is defined else []) %}"
      },
      {
        "line": 78,
        "term": "phase",
        "sample": "{% if phase4_show_third_supervisor_column|default(period_level_3_enabled|default(false)) %}{% if phase4_4_show_third_col %}<th>3. Amir</th>{% endif %}{% endif %} {# BYS360_PHASE4_THIRD_SUPERVISOR_COLUMN_GUARD #}"
      },
      {
        "line": 92,
        "term": "phase",
        "sample": "{% if phase4_show_third_supervisor_column|default(period_level_3_enabled|default(false)) %}<td>{{ '%.2f'|format(item.level_3_total_100 or 0) }}</td>{% endif %}"
      },
      {
        "line": 94,
        "term": "phase",
        "sample": "<td>{{ item.status or '-'|phase5_4_status_label }}</td>"
      },
      {
        "line": 107,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_ACTIONS_GUARD: buton/form aksiyonları mobilde tek sütuna düşer #}"
      }
    ],
    "hit_count": 9
  },
  {
    "path": "app/templates/performance_report_card.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 12,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_ACTIONS_GUARD: buton/form aksiyonları mobilde tek sütuna düşer #}"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/performance_scorecard_detail.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".phase10-detail-summary{"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".phase10-detail-summary:hover{"
      },
      {
        "line": 12,
        "term": "phase",
        "sample": ".phase10-note-detail-card{"
      },
      {
        "line": 21,
        "term": "phase",
        "sample": ".phase10-status-badge{"
      },
      {
        "line": 33,
        "term": "phase",
        "sample": "/* BYS360_PHASE5_2_EMPLOYEE_SCORECARD_SIMPLE_STYLE */"
      },
      {
        "line": 34,
        "term": "phase",
        "sample": ".phase5-employee-scorecard{display:grid;gap:18px}"
      },
      {
        "line": 35,
        "term": "phase",
        "sample": ".phase5-employee-hero{display:grid;grid-template-columns:minmax(0,1.15fr) 260px;gap:18px;align-items:stretch;border:1px solid rgba(139,0,0,.14);border-radius:28px;background:linear-gradient(135deg,rgba(139,0,0,.075),rgba(255,255,255,.96));b"
      },
      {
        "line": 36,
        "term": "phase",
        "sample": ".phase5-employee-kicker{font-size:.78rem;font-weight:950;letter-spacing:.08em;text-transform:uppercase;color:#8B0000}"
      },
      {
        "line": 37,
        "term": "phase",
        "sample": ".phase5-employee-title{margin:7px 0 8px;color:#111827;font-size:1.55rem;font-weight:950;line-height:1.25}"
      },
      {
        "line": 111,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz2_performance_mobile.css') }}\">"
      },
      {
        "line": 112,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ11_PANEL_INCLUDED #}"
      },
      {
        "line": 117,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ7_HISTORICAL_ARCHIVE_PANEL_INCLUDE #}"
      },
      {
        "line": 118,
        "term": "faz",
        "sample": "{% include \"ai_decision/_faz7_historical_archive_panel.html\" ignore missing %}"
      },
      {
        "line": 120,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ5_SCORECARD_PANEL_INCLUDE #}"
      },
      {
        "line": 121,
        "term": "faz",
        "sample": "{% include \"ai_decision/_faz5_scorecard_decision_panel.html\" ignore missing %}"
      },
      {
        "line": 417,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ10_PANEL_INCLUDED #}"
      },
      {
        "line": 156,
        "term": "gate",
        "sample": "{# BYS360_PHASE5_2_HISTORY_ROUTE_BIND | Geçmiş Karnelerime Git | performance_scorecard | route bağı erken gate markerı #}"
      }
    ],
    "hit_count": 18
  },
  {
    "path": "app/templates/performance_tasks.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 803,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase4_assignment', assignment_id=assignment.id) }}\""
      },
      {
        "line": 11,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz2_performance_mobile.css') }}\">"
      },
      {
        "line": 836,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz2_performance_mobile.js') }}\"></script>"
      },
      {
        "line": 787,
        "term": "workflow",
        "sample": "<span class=\"pill workflow-{{ assignment.workflow_badge_class|default('neutral') }}\">{{ assignment.workflow_label|default('1. amirde taslak') }}</span>"
      },
      {
        "line": 411,
        "term": "gate",
        "sample": ".coverage-panel.delegated{background:rgba(239,246,255,.94);border-color:rgba(29,78,216,.14)}"
      },
      {
        "line": 417,
        "term": "gate",
        "sample": ".coverage-chip.delegated{background:rgba(29,78,216,.10);color:#1d4ed8}"
      },
      {
        "line": 423,
        "term": "gate",
        "sample": ".assignment-callout.delegated{background:rgba(239,246,255,.96);border-color:rgba(29,78,216,.12);color:#1d4ed8}"
      },
      {
        "line": 540,
        "term": "gate",
        "sample": "<div class=\"count-chip\">Vekâlet: {{ delegated_assignment_count or 0 }} · Açıkta: {{ uncovered_assignment_count or 0 }}</div>"
      },
      {
        "line": 545,
        "term": "gate",
        "sample": "<div class=\"unit-box-value\">{{ (total_count or 0) - (delegated_assignment_count or 0) - (uncovered_assignment_count or 0) }}</div>"
      },
      {
        "line": 549,
        "term": "gate",
        "sample": "<div class=\"unit-box-value\">{{ delegated_assignment_count or 0 }}</div>"
      },
      {
        "line": 765,
        "term": "gate",
        "sample": "{% if assignment.assignment_source == 'delegated' and assignment.original_evaluator %}"
      },
      {
        "line": 766,
        "term": "gate",
        "sample": "<div class=\"assignment-callout delegated\">"
      }
    ],
    "hit_count": 12
  },
  {
    "path": "app/templates/performance_task_health.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 117,
        "term": "faz",
        "sample": "<div class=\"section-sub\">Aynı personelin aynı amir seviyesinde birden fazla görev satırı oluştuysa burada görünür.</div>"
      },
      {
        "line": 190,
        "term": "workflow",
        "sample": "<div class=\"list-item\"><strong>{{ row.employee_name }}</strong><small>{{ row.employee_unit }} · {{ row.workflow_status }}{% if row.exempted %} · Muaf{% endif %}</small></div>"
      },
      {
        "line": 88,
        "term": "gate",
        "sample": "<div class=\"mini-card\"><strong>{{ summary.delegated_count or 0 }}</strong><span>Vekâletli görev</span></div>"
      },
      {
        "line": 107,
        "term": "gate",
        "sample": "<div class=\"mini-card\"><strong>{{ coverage_summary.delegated or 0 }}</strong><span>Log içindeki vekâletli kayıt</span></div>"
      },
      {
        "line": 214,
        "term": "gate",
        "sample": "<div class=\"list-item\"><strong>{{ row.manager_name }}</strong><small>{{ row.manager_unit }} · Açık: {{ row.open_count }} · Geciken: {{ row.overdue_count }} · Vekâlet: {{ row.delegated_count }}</small></div>"
      }
    ],
    "hit_count": 5
  },
  {
    "path": "app/templates/performance_task_preflight.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 173,
        "term": "faz",
        "sample": "<div class=\"section-sub\">Faz 1 ile görev üretimi artık bu sabit kurallar üzerinden korunur.</div>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/performance_v2_phase1.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 36,
        "term": "json",
        "sample": "<div style=\"margin-top:18px;\"><h3 class=\"section-title\">Sistem Ön İzleme</h3><pre class=\"code-block\">{{ preview[\"de\" ~ \"bug\"] | tojson(indent=2) }}</pre></div>"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/performance_v2_phase2.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 37,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE8_PERIOD_SCOPE_BOUND #}"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/performance_v2_phase3.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 3,
        "term": "phase",
        "sample": "{% block extra_head %}<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/performance_phase3.css') }}\">{% endblock %}"
      },
      {
        "line": 63,
        "term": "phase",
        "sample": "<a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase2_dashboard', period_id=period.id if period else None) }}\"><i class=\"fa-solid fa-rotate\"></i> Görev senkronu</a>"
      },
      {
        "line": 64,
        "term": "phase",
        "sample": "<a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase5_dashboard', period_id=period.id if period else None) }}\"><i class=\"fa-solid fa-chart-column\"></i> Rapor özeti</a>"
      },
      {
        "line": 126,
        "term": "phase",
        "sample": "<td><a class=\"performance-btn primary\" href=\"{{ url_for('main.performance_v2_phase3_assignment', assignment_id=item.id) }}\"><i class=\"fa-solid fa-arrow-up-right-from-square\"></i> Formu aç</a></td>"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/performance_v2_phase3_assignment.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": "/* BYS360_PHASE5_3_MANAGER_SCORING_STYLE */"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".phase5-3-manager-context{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:16px 0 18px}.phase5-3-manager-card{border:1px solid rgba(139,0,0,.12);border-radius:20px;background:rgba(255,255,255,.94);box-shadow:0 14px"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "{# BYS360_PHASE4_3_ASSIGNMENT_STATUS_LANGUAGE | Yorum/Görüş Bekliyor | Puanlama Bekliyor | assignment.manager_level == 3 #}"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 13,
        "term": "phase",
        "sample": "{% block extra_head %}<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/performance_phase3.css') }}\">{% endblock %}"
      },
      {
        "line": 20,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 99,
        "term": "phase",
        "sample": "{% set phase5_3_comment_rule_from_settings = phase5_3_comment_rule_from_settings if phase5_3_comment_rule_from_settings is defined else true %}"
      },
      {
        "line": 100,
        "term": "phase",
        "sample": "{% set phase5_3_interim_ctx = interim_notes_context if interim_notes_context is defined and interim_notes_context else {} %}"
      },
      {
        "line": 101,
        "term": "phase",
        "sample": "{% set phase5_3_interim_notes = phase5_3_interim_ctx.notes if phase5_3_interim_ctx.notes is defined else [] %}"
      },
      {
        "line": 471,
        "term": "sync",
        "sample": "function syncLiveMiniCards() {"
      },
      {
        "line": 503,
        "term": "sync",
        "sample": "function syncLiveProgress(filledCount) {"
      },
      {
        "line": 610,
        "term": "sync",
        "sample": "const filledCount = syncLiveMiniCards();"
      },
      {
        "line": 611,
        "term": "sync",
        "sample": "syncLiveProgress(filledCount);"
      },
      {
        "line": 680,
        "term": "sync",
        "sample": "input.addEventListener('input', syncLiveMiniCards);"
      }
    ],
    "hit_count": 15
  },
  {
    "path": "app/templates/performance_v2_phase5_dashboard.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 7,
        "term": "phase",
        "sample": "{% block extra_head %}<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/performance_phase3.css') }}\">{% endblock %}"
      },
      {
        "line": 22,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_scorecard_ui_styles.html\" ignore missing %}"
      },
      {
        "line": 53,
        "term": "phase",
        "sample": "<a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase5_scorecard', period_id=period.id if period else None) }}\"><i class=\"fa-solid fa-id-card\"></i> Not karnesi</a>"
      },
      {
        "line": 54,
        "term": "phase",
        "sample": "<a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase5_publish', period_id=period.id if period else None) }}\"><i class=\"fa-solid fa-share-nodes\"></i> Sonuç yayınlama</a>"
      },
      {
        "line": 112,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_BOUND #}"
      },
      {
        "line": 113,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE11_REPORTING_RISK_BOUND #}"
      },
      {
        "line": 114,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_READINESS_BOUND #}"
      },
      {
        "line": 1,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ9_REMINDER_CSS_LINK #}"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/ai_decision_faz9_reminder.css') }}\">"
      },
      {
        "line": 3,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_CSS_LINK #}"
      },
      {
        "line": 4,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/ai_decision_faz8_period_scope.css') }}\">"
      },
      {
        "line": 13,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ9_REMINDER_PANEL_INCLUDE #}"
      },
      {
        "line": 14,
        "term": "faz",
        "sample": "{% include \"ai_decision/_faz9_reminder_panel.html\" ignore missing %}"
      },
      {
        "line": 16,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_PANEL_INCLUDE #}"
      },
      {
        "line": 17,
        "term": "faz",
        "sample": "{% include \"ai_decision/_faz8_period_scope_panel.html\" ignore missing %}"
      },
      {
        "line": 19,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ5_SCORECARD_PANEL_INCLUDE #}"
      },
      {
        "line": 20,
        "term": "faz",
        "sample": "{% include \"ai_decision/_faz5_scorecard_decision_panel.html\" ignore missing %}"
      }
    ],
    "hit_count": 17
  },
  {
    "path": "app/templates/performance_v2_phase5_publish.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 7,
        "term": "phase",
        "sample": "{% block extra_head %}<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/performance_phase3.css') }}\">{% endblock %}"
      },
      {
        "line": 31,
        "term": "phase",
        "sample": "{% set phase5_guide_title = \"Bu ekran personel görünürlüğünü kontrollü biçimde yönetir\" %}"
      },
      {
        "line": 33,
        "term": "phase",
        "sample": "{% set phase5_guide_text = \"Yayınlama, yalnızca tamamlanmış ve kurala uygun kayıtların personele açılması için kullanılmalıdır. Geri alma ise görünürlüğü kapatır; değerlendirme geçmişini silmez.\" %}"
      },
      {
        "line": 35,
        "term": "phase",
        "sample": "{% set phase5_guide_points = ["
      },
      {
        "line": 45,
        "term": "phase",
        "sample": "{% set phase5_guide_note = \"Sonuçlar, Personel veya yetkili idari onay tamamlanmadan personele açılmamalıdır. Bu yüzey yayın güvenliği için son kapıdır.\" %}"
      },
      {
        "line": 47,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_microguide.html\" %}"
      },
      {
        "line": 160,
        "term": "phase",
        "sample": "<a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase5_publish_preflight', period_id=period.id) }}\"><i class=\"fa-solid fa-shield-check\"></i> Ön kontrol</a>"
      },
      {
        "line": 162,
        "term": "phase",
        "sample": "<a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase6_export_csv', period_id=period.id, type='publish_summary') }}\"><i class=\"fa-solid fa-file-csv\"></i> Yayın özeti CSV</a>"
      },
      {
        "line": 210,
        "term": "phase",
        "sample": "{% if period %}<div class=\"preflight-actions\"><a class=\"performance-btn secondary\" href=\"{{ url_for('main.performance_v2_phase5_publish_preflight', period_id=period.id) }}\"><i class=\"fa-solid fa-clipboard-check\"></i> Ayrıntılı ekran</a></di"
      },
      {
        "line": 484,
        "term": "workflow",
        "sample": "<td>{{ row.status }}<div class=\"performance-subtext\">{{ row.workflow_status }}</div></td>"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/templates/performance_v2_phase5_scorecard.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_4_TECHNICAL_LANGUAGE_CLEANUP #}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_FINAL_GATE_TEMPLATE_CONTRACT_FIX #}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_2_PERSONEL_KARNE_EKRANI #}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": "{# phase5_2_is_employee_scorecard #}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_ACTIONS_GUARD: buton/form aksiyonları mobilde tek sütuna düşer #}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": "{% set phase5_2_is_employee_scorecard = phase5_2_is_employee_scorecard if phase5_2_is_employee_scorecard is defined else false %}"
      },
      {
        "line": 25,
        "term": "phase",
        "sample": "<div class=\"sr-only phase5-final-contract-labels\" aria-hidden=\"true\">Ana Puan Kartı Dönem Bilgisi Kriter Sonuçları Yayınlanan Açıklama Geçmiş Karne Bağlantısı</div>"
      },
      {
        "line": 26,
        "term": "phase",
        "sample": "<div class=\"bys-elite-shell\" data-bys360-marker=\"BYS360_PHASE7_PREMIUM_SCORECARD_SURFACE_V2\">"
      },
      {
        "line": 3,
        "term": "gate",
        "sample": "{# BYS360_PHASE5_FINAL_GATE_TEMPLATE_CONTRACT_FIX #}"
      },
      {
        "line": 3,
        "term": "contract",
        "sample": "{# BYS360_PHASE5_FINAL_GATE_TEMPLATE_CONTRACT_FIX #}"
      },
      {
        "line": 25,
        "term": "contract",
        "sample": "<div class=\"sr-only phase5-final-contract-labels\" aria-hidden=\"true\">Ana Puan Kartı Dönem Bilgisi Kriter Sonuçları Yayınlanan Açıklama Geçmiş Karne Bağlantısı</div>"
      }
    ],
    "hit_count": 13
  },
  {
    "path": "app/templates/performance_v2_phase6_dashboard.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 23,
        "term": "phase",
        "sample": "<a class=\"bys-pro-btn light\" href=\"{{ url_for('main.performance_v2_phase6_export_xlsx', period_id=period.id) if period else '#' }}\"><i class=\"fa-solid fa-file-excel\"></i> Excel</a>"
      },
      {
        "line": 24,
        "term": "phase",
        "sample": "<a class=\"bys-pro-btn\" href=\"{{ url_for('main.performance_v2_phase6_print', period_id=period.id) if period else '#' }}\"><i class=\"fa-solid fa-print\"></i> Yazdır</a>"
      },
      {
        "line": 26,
        "term": "workflow",
        "sample": "<a class=\"bys-pro-btn light\" href=\"{{ url_for('main.workflow_executive_dashboard') }}\"><i class=\"fa-solid fa-route\"></i> İş Akış Paneli</a>"
      },
      {
        "line": 55,
        "term": "json",
        "sample": "<div class=\"bys-pro-chart compact\"><canvas data-bys-chart=\"bar\" data-labels='{{ [\"Ortalama\", \"70 altı\", \"90 üstü\", \"Yayımlanan\"]|tojson }}' data-datasets='{{ [{\"label\":\"Skor kartı\",\"data\":[sc.avg_score|default(0,true), sc.low_count|default("
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/performance_v2_phase7_hub.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 28,
        "term": "phase",
        "sample": "<div class=\"v2-card\"><h3>Faz 2 · Görev Senkronu</h3><p>Aktif dönem için evaluator zincirini ve görev satırlarını V2 omurgasıyla yeniden üretir.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_pha"
      },
      {
        "line": 30,
        "term": "phase",
        "sample": "<div class=\"v2-card\"><h3>Değerlendirme Görevlerim</h3><p>Kullanıcının değerlendirme çalışma alanını değerlendirme formu ve süreç akışıyla açar.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_pha"
      },
      {
        "line": 31,
        "term": "phase",
        "sample": "<div class=\"v2-card\"><h3>Not Karnesi</h3><p>Dönem sonuçlarını, yayımlama durumunu ve personel bazlı karne görünümünü açar.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_phase5_scorecard', perio"
      },
      {
        "line": 33,
        "term": "phase",
        "sample": "<div class=\"v2-card\"><h3>Faz 5 · Yayın Yönetimi</h3><p>Dönem sonuçlarını toplu yayımlama ve geri alma işlemlerini yönetir.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_phase5_publish', period_"
      },
      {
        "line": 34,
        "term": "phase",
        "sample": "<div class=\"v2-card\"><h3>Faz 6 · Yönetici Dashboard</h3><p>Excel ve CSV exportlarıyla birlikte yönetici özet göstergelerini açar.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_phase6_dashboard'"
      },
      {
        "line": 28,
        "term": "faz",
        "sample": "<div class=\"v2-card\"><h3>Faz 2 · Görev Senkronu</h3><p>Aktif dönem için evaluator zincirini ve görev satırlarını V2 omurgasıyla yeniden üretir.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_pha"
      },
      {
        "line": 33,
        "term": "faz",
        "sample": "<div class=\"v2-card\"><h3>Faz 5 · Yayın Yönetimi</h3><p>Dönem sonuçlarını toplu yayımlama ve geri alma işlemlerini yönetir.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_phase5_publish', period_"
      },
      {
        "line": 34,
        "term": "faz",
        "sample": "<div class=\"v2-card\"><h3>Faz 6 · Yönetici Dashboard</h3><p>Excel ve CSV exportlarıyla birlikte yönetici özet göstergelerini açar.</p><div class=\"v2-actions\"><a class=\"btn-soft primary\" href=\"{{ url_for('main.performance_v2_phase6_dashboard'"
      }
    ],
    "hit_count": 8
  },
  {
    "path": "app/templates/performance_v2_phase8_hub.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 79,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase3_dashboard', period_id=period.id if period else None) }}\" class=\"v2-btn secondary\">Çalışma Alanı</a>"
      },
      {
        "line": 87,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase5_scorecard', period_id=period.id if period else None) }}\" class=\"v2-btn primary\">Not Karnesi</a>"
      },
      {
        "line": 88,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase5_publish', period_id=period.id if period else None) }}\" class=\"v2-btn secondary\">Yayın Yönetimi</a>"
      },
      {
        "line": 96,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase6_dashboard', period_id=period.id if period else None) }}\" class=\"v2-btn primary\">Raporlar</a>"
      },
      {
        "line": 97,
        "term": "phase",
        "sample": "<a href=\"{{ url_for('main.performance_v2_phase6_export_xlsx', period_id=period.id if period else None) }}\" class=\"v2-btn secondary\">Excel Export</a>"
      },
      {
        "line": 94,
        "term": "faz",
        "sample": "<p>Yönetici dashboard’u, Excel ve CSV exportları Faz 6 üzerinden açılır.</p>"
      }
    ],
    "hit_count": 6
  },
  {
    "path": "app/templates/periods.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 359,
        "term": "phase",
        "sample": "/* BYS360_PHASE8_3_SPECIAL_SCENARIO_LIST_STYLE_START */"
      },
      {
        "line": 362,
        "term": "phase",
        "sample": "/* BYS360_PHASE8_3_SPECIAL_SCENARIO_LIST_STYLE_END */"
      },
      {
        "line": 364,
        "term": "phase",
        "sample": "/* BYS360_PHASE8_5_PERIOD_LIST_SCOPE_LABELS_STYLE_START */"
      },
      {
        "line": 365,
        "term": "phase",
        "sample": ".bys360-phase8-5-scope-card{background:linear-gradient(180deg,rgba(139,0,0,.055),#fff);border-color:rgba(139,0,0,.12);}"
      },
      {
        "line": 366,
        "term": "phase",
        "sample": ".bys360-phase8-5-scope-line{display:flex;align-items:center;gap:7px;flex-wrap:wrap;line-height:1.65;}"
      },
      {
        "line": 367,
        "term": "phase",
        "sample": ".bys360-phase8-5-scope-chip{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:4px 9px;background:rgba(139,0,0,.085);color:#8B0000;font-weight:900;font-size:.78rem;}"
      },
      {
        "line": 368,
        "term": "phase",
        "sample": ".bys360-phase8-5-scope-chip.neutral{background:rgba(15,23,42,.065);color:#374151;}"
      },
      {
        "line": 369,
        "term": "phase",
        "sample": ".bys360-phase8-5-scope-chip.info{background:rgba(29,78,216,.085);color:#1d4ed8;}"
      },
      {
        "line": 370,
        "term": "phase",
        "sample": ".bys360-phase8-5-scope-target{color:#374151;font-size:.82rem;font-weight:800;}"
      },
      {
        "line": 371,
        "term": "phase",
        "sample": "/* BYS360_PHASE8_5_PERIOD_LIST_SCOPE_LABELS_STYLE_END */"
      },
      {
        "line": 635,
        "term": "gate",
        "sample": "Muaf {{ row.coverage_summary.exempted or 0 }} · Açıkta {{ row.coverage_summary.uncovered or 0 }} · Zincir {{ row.coverage_summary.chain_issue or 0 }} · Vekâlet {{ row.coverage_summary.delegated or 0 }}"
      }
    ],
    "hit_count": 11
  },
  {
    "path": "app/templates/period_create.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 479,
        "term": "sync",
        "sample": "function syncScoringDateMin(){"
      },
      {
        "line": 496,
        "term": "sync",
        "sample": "periodEndDateInput.addEventListener('change', syncScoringDateMin);"
      },
      {
        "line": 497,
        "term": "sync",
        "sample": "syncScoringDateMin();"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/templates/period_edit.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 460,
        "term": "phase",
        "sample": "{# BYS360_PHASE8_3_SPECIAL_SCENARIO_FIELDS_START #}"
      },
      {
        "line": 461,
        "term": "phase",
        "sample": "<div class=\"form-group full bys360-phase8-special-scenario-field\">"
      },
      {
        "line": 474,
        "term": "phase",
        "sample": "{# BYS360_PHASE8_3_SPECIAL_SCENARIO_FIELDS_END #}"
      },
      {
        "line": 476,
        "term": "phase",
        "sample": "{# BYS360_PHASE8_2_PERIOD_SCOPE_FIELDS_START #}"
      },
      {
        "line": 513,
        "term": "phase",
        "sample": "{# BYS360_PHASE8_2_PERIOD_SCOPE_FIELDS_END #}"
      },
      {
        "line": 472,
        "term": "faz",
        "sample": "<small class=\"form-help\">Senaryo seçildiğinde dönem türü “Özel Dönem” mantığında değerlendirilir; görev üretiminde kapsam filtresi Faz 8.4 ile kesin bağlanacaktır.</small>"
      },
      {
        "line": 511,
        "term": "faz",
        "sample": "<small class=\"form-help\">Seçili Personel kapsamında yalnızca bu listede yer alan personele görev üretimi Faz 8.4 ile bağlanacaktır.</small>"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/templates/personnel_excel_upload.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 578,
        "term": "phase",
        "sample": "<div class=\"tip-item\" data-bys360-marker=\"BYS360_PHASE2_3_EXCEL_TEMPLATE_AUTO_NOTE\">"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/reports.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 17,
        "term": "phase",
        "sample": "<div class=\"bys-elite-shell\" data-bys360-marker=\"BYS360_PHASE7_PREMIUM_REPORTS_SURFACE_V2\">"
      },
      {
        "line": 56,
        "term": "phase",
        "sample": "<div class=\"bys-elite-field\" data-bys360-marker=\"BYS360_PHASE2_REPORT_CATEGORY_FILTER\">"
      },
      {
        "line": 106,
        "term": "phase",
        "sample": "<section class=\"bys-elite-card bys-elite-pad\" data-bys360-marker=\"BYS360_PHASE2_4_CATEGORY_AVERAGE_CARD\">"
      },
      {
        "line": 285,
        "term": "json",
        "sample": "}|tojson }};"
      },
      {
        "line": 203,
        "term": "gate",
        "sample": "<div class=\"bys-elite-mini-box success\"><span>Vekâletli</span><strong>{{ coverage_stats.delegated|default(0, true) }}</strong></div>"
      },
      {
        "line": 230,
        "term": "gate",
        "sample": "<td>{{ row.delegated|default(0, true) }}</td>"
      }
    ],
    "hit_count": 6
  },
  {
    "path": "app/templates/reports_pdf.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 66,
        "term": "phase",
        "sample": "{% if phase4_show_third_supervisor_column|default(period_level_3_enabled|default(false)) %}<th>3. Amir</th>{% endif %} {# BYS360_PHASE4_THIRD_SUPERVISOR_COLUMN_GUARD #}"
      },
      {
        "line": 80,
        "term": "phase",
        "sample": "{% if phase4_show_third_supervisor_column|default(period_level_3_enabled|default(false)) %}<td>{{ '%.2f'|format(item.level_3_total_100 or 0) }}</td>{% endif %}"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/templates/scorecard.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 4,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 14,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 831,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_ACTIONS_GUARD: buton/form aksiyonları mobilde tek sütuna düşer #}"
      },
      {
        "line": 17,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz2_performance_mobile.css') }}\">"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/scorecard_pdf.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_TABLE_GUARD: tablolar CSS ile yatay kaydırılabilir #}"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT #}"
      },
      {
        "line": 391,
        "term": "phase",
        "sample": "/* BYS360_PHASE10_SCORECARD_DEVELOPMENT_PDF_STYLE */"
      },
      {
        "line": 508,
        "term": "phase",
        "sample": "<!-- BYS360_PHASE10_SCORECARD_DEVELOPMENT_PDF_BLOCK -->"
      },
      {
        "line": 670,
        "term": "phase",
        "sample": "{# BYS360_PHASE5_5_MOBILE_ACTIONS_GUARD: buton/form aksiyonları mobilde tek sütuna düşer #}"
      }
    ],
    "hit_count": 5
  },
  {
    "path": "app/templates/settings.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 134,
        "term": "phase",
        "sample": "<span class=\"matrix-pill\"><i class=\"fa-solid fa-layer-group\"></i> Tamamlanan faz: {{ ui_panel.completed_phase_count }}</span>"
      },
      {
        "line": 135,
        "term": "phase",
        "sample": "<span class=\"matrix-pill\"><i class=\"fa-solid fa-flag-checkered\"></i> Aktif: {{ ui_panel.active_phase.phase|default('Faz 11') }}</span>"
      },
      {
        "line": 136,
        "term": "phase",
        "sample": "<span class=\"matrix-pill\"><i class=\"fa-solid fa-forward-step\"></i> Sıradaki: {{ ui_panel.next_phase_label }}</span>"
      },
      {
        "line": 140,
        "term": "phase",
        "sample": "<div class=\"settings-phase-strip\" aria-label=\"Ayarlar servisi faz durumu\">"
      },
      {
        "line": 141,
        "term": "phase",
        "sample": "{% for phase in ui_panel.phase_sequence %}"
      },
      {
        "line": 142,
        "term": "phase",
        "sample": "<span class=\"settings-phase-pill {{ phase.status_class }}\" title=\"{{ phase.title }}\">"
      },
      {
        "line": 143,
        "term": "phase",
        "sample": "<i class=\"fa-solid {{ 'fa-check' if phase.status_class == 'ok' else ('fa-circle-dot' if phase.status_class == 'warn' else 'fa-clock') }}\"></i>"
      },
      {
        "line": 144,
        "term": "phase",
        "sample": "{{ phase.phase }} · {{ phase.status }}"
      },
      {
        "line": 460,
        "term": "phase",
        "sample": "{% if phase1_seed_summary.ok %}"
      },
      {
        "line": 462,
        "term": "phase",
        "sample": "<span class=\"matrix-pill\"><i class=\"fa-solid fa-database\"></i> Rol satırı tohumlama: {{ phase1_seed_summary.seeded_role_defaults }}</span>"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 100,
        "term": "faz",
        "sample": "<div class=\"section-text\" style=\"margin:8px 0 0 0;\">Faz 2 ile kalıcı hale gelen birim bazlı menü profilleri.</div>"
      },
      {
        "line": 105,
        "term": "faz",
        "sample": "<div class=\"section-text\" style=\"margin:8px 0 0 0;\">Faz 3 ile eklenen son değişiklik ve geri alma kayıtları.</div>"
      },
      {
        "line": 115,
        "term": "faz",
        "sample": "<div class=\"section-text\" style=\"margin-bottom:0;\">Faz 4–11 servis köprüleri, canlı menü filtresi, veritabanı omurgası ve son değişiklik kayıtları tek bakışta izlenir.</div>"
      },
      {
        "line": 134,
        "term": "faz",
        "sample": "<span class=\"matrix-pill\"><i class=\"fa-solid fa-layer-group\"></i> Tamamlanan faz: {{ ui_panel.completed_phase_count }}</span>"
      },
      {
        "line": 135,
        "term": "faz",
        "sample": "<span class=\"matrix-pill\"><i class=\"fa-solid fa-flag-checkered\"></i> Aktif: {{ ui_panel.active_phase.phase|default('Faz 11') }}</span>"
      },
      {
        "line": 140,
        "term": "faz",
        "sample": "<div class=\"settings-phase-strip\" aria-label=\"Ayarlar servisi faz durumu\">"
      },
      {
        "line": 433,
        "term": "faz",
        "sample": "<div class=\"section-text\" style=\"margin-bottom:0;\">Statik menü tanımları faz 1 ile veritabanına senkronize edilir ve kişi bazlı yetki mantığıyla birlikte çalışır.</div>"
      },
      {
        "line": 472,
        "term": "faz",
        "sample": "<div class=\"section-title\">Faz 2 · Birim Profili Anlık Durum</div>"
      },
      {
        "line": 496,
        "term": "faz",
        "sample": "<div class=\"empty-box\">Henüz kaydedilmiş birim profili bulunmuyor. Faz 2 ile seçili matrisi birim profiline yazabilirsiniz.</div>"
      }
    ],
    "hit_count": 31
  },
  {
    "path": "app/templates/surveys_list.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 121,
        "term": "sync",
        "sample": "function sync(){"
      },
      {
        "line": 134,
        "term": "sync",
        "sample": "sync();"
      },
      {
        "line": 136,
        "term": "sync",
        "sample": "function syncToolbarState(){"
      },
      {
        "line": 141,
        "term": "sync",
        "sample": "syncToolbarState();"
      },
      {
        "line": 142,
        "term": "sync",
        "sample": "if (toolbarToggle && shell) toolbarToggle.addEventListener('click', function(){ shell.classList.toggle('filters-collapsed'); localStorage.setItem(storageKey, shell.classList.contains('filters-collapsed') ? '1' : '0'); syncToolbarState(); })"
      }
    ],
    "hit_count": 5
  },
  {
    "path": "app/templates/survey_create.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 12,
        "term": "phase",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/survey_jotform_phase1.css') }}\">"
      },
      {
        "line": 90,
        "term": "phase",
        "sample": "<div class=\"builder-shell jotform-phase1-shell\" data-survey-studio=\"1\">"
      },
      {
        "line": 861,
        "term": "phase",
        "sample": "<script src=\"{{ url_for('static', filename='js/survey_builder_phase1.js') }}\"></script>"
      },
      {
        "line": 475,
        "term": "sync",
        "sample": "function syncTargetPanels() {"
      },
      {
        "line": 484,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 511,
        "term": "sync",
        "sample": "syncTargetPanels();"
      },
      {
        "line": 533,
        "term": "sync",
        "sample": "async function runUserSearch() {"
      },
      {
        "line": 634,
        "term": "sync",
        "sample": "function syncOptionsField() {"
      },
      {
        "line": 642,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 645,
        "term": "sync",
        "sample": "function syncLogicFields() {"
      },
      {
        "line": 656,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 659,
        "term": "sync",
        "sample": "typeSelect.addEventListener('change', syncOptionsField);"
      },
      {
        "line": 660,
        "term": "sync",
        "sample": "if (logicModeSelect) logicModeSelect.addEventListener('change', syncLogicFields);"
      },
      {
        "line": 386,
        "term": "json",
        "sample": "const userSearchPath = {{ url_for('main.survey_target_users')|tojson }};"
      },
      {
        "line": 387,
        "term": "json",
        "sample": "const initialQuestions = {{ initial_questions|tojson|safe }};"
      },
      {
        "line": 546,
        "term": "json",
        "sample": "const payload = await response.json();"
      }
    ],
    "hit_count": 16
  },
  {
    "path": "app/templates/survey_edit.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 12,
        "term": "phase",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/survey_jotform_phase1.css') }}\">"
      },
      {
        "line": 87,
        "term": "phase",
        "sample": "<div class=\"builder-shell jotform-phase1-shell\" data-survey-studio=\"1\" data-has-responses=\"{{ 1 if has_responses else 0 }}\">"
      },
      {
        "line": 667,
        "term": "phase",
        "sample": "<script src=\"{{ url_for('static', filename='js/survey_builder_phase1.js') }}\"></script>"
      },
      {
        "line": 401,
        "term": "sync",
        "sample": "function syncTargetPanels() {"
      },
      {
        "line": 410,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 441,
        "term": "sync",
        "sample": "async function runUserSearch() {"
      },
      {
        "line": 477,
        "term": "sync",
        "sample": "syncTargetPanels();"
      },
      {
        "line": 489,
        "term": "sync",
        "sample": "function syncOptionsField() {"
      },
      {
        "line": 498,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 501,
        "term": "sync",
        "sample": "function syncLogicFields() {"
      },
      {
        "line": 512,
        "term": "sync",
        "sample": "syncSummary();"
      },
      {
        "line": 515,
        "term": "sync",
        "sample": "if (typeSelect) typeSelect.addEventListener('change', syncOptionsField);"
      },
      {
        "line": 516,
        "term": "sync",
        "sample": "if (logicModeSelect) logicModeSelect.addEventListener('change', syncLogicFields);"
      },
      {
        "line": 372,
        "term": "json",
        "sample": "const userSearchPath = {{ url_for('main.survey_target_users')|tojson }};"
      },
      {
        "line": 373,
        "term": "json",
        "sample": "const initialQuestions = {{ initial_questions|tojson|safe }};"
      },
      {
        "line": 454,
        "term": "json",
        "sample": "const payload = await response.json();"
      }
    ],
    "hit_count": 16
  },
  {
    "path": "app/templates/survey_manage.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 13,
        "term": "phase",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/survey_jotform_phase1.css') }}\">"
      },
      {
        "line": 78,
        "term": "phase",
        "sample": "<div class=\"survey-manage-shell jotform-phase1-shell\" data-survey-manage=\"1\">"
      },
      {
        "line": 439,
        "term": "phase",
        "sample": "<script src=\"{{ url_for('static', filename='js/survey_manage_phase1.js') }}\"></script>"
      },
      {
        "line": 10,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 438,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz4_support_account_mobile.js') }}\"></script>"
      },
      {
        "line": 376,
        "term": "sync",
        "sample": "function syncSelection(){"
      },
      {
        "line": 404,
        "term": "sync",
        "sample": "function syncSearch(){"
      },
      {
        "line": 416,
        "term": "sync",
        "sample": "boxes.forEach(box => box.addEventListener('change', syncSelection));"
      },
      {
        "line": 420,
        "term": "sync",
        "sample": "syncSelection();"
      },
      {
        "line": 426,
        "term": "sync",
        "sample": "syncSelection();"
      },
      {
        "line": 431,
        "term": "sync",
        "sample": "syncSearch();"
      },
      {
        "line": 434,
        "term": "sync",
        "sample": "syncSearch();"
      },
      {
        "line": 435,
        "term": "sync",
        "sample": "syncSelection();"
      }
    ],
    "hit_count": 13
  },
  {
    "path": "app/templates/survey_results.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 12,
        "term": "phase",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/survey_jotform_phase1.css') }}\">"
      },
      {
        "line": 85,
        "term": "phase",
        "sample": "<div class=\"results-shell jotform-phase1-shell\">"
      },
      {
        "line": 9,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 362,
        "term": "faz",
        "sample": "{% block extra_scripts %}<script src=\"{{ url_for('static', filename='js/survey_formbricks_overlay.js') }}\"></script><script src=\"{{ url_for('static', filename='js/faz4_support_account_mobile.js') }}\"></script><script src=\"{{ url_for('static"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/survey_take.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 12,
        "term": "faz",
        "sample": "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/faz4_support_account_mobile.css') }}\">"
      },
      {
        "line": 220,
        "term": "faz",
        "sample": "<script src=\"{{ url_for('static', filename='js/faz4_support_account_mobile.js') }}\"></script>"
      },
      {
        "line": 216,
        "term": "json",
        "sample": "serverDraftProgress: {{ server_draft_progress|default(0)|tojson }},"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/templates/task_management.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 17,
        "term": "phase",
        "sample": "{% set phase5_guide_title = \"Bu ekran görev üretimini ve kapsama kalitesini birlikte yönetir\" %}"
      },
      {
        "line": 18,
        "term": "phase",
        "sample": "{% set phase5_guide_text = \"Görevleri yalnızca üretmek değil; doğru amire, doğru seviyede ve eksiksiz kapsama ile düştüğünü doğrulamak için bu ekran kullanılır.\" %}"
      },
      {
        "line": 19,
        "term": "phase",
        "sample": "{% set phase5_guide_points = ["
      },
      {
        "line": 24,
        "term": "phase",
        "sample": "{% set phase5_guide_note = \"Canlı kullanımda en güvenli yöntem, doğrudan toplu üretim yerine önce ön kontrolü çalıştırıp sonra görevleri üretmektir.\" %}"
      },
      {
        "line": 25,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_microguide.html\" %}"
      },
      {
        "line": 353,
        "term": "gate",
        "sample": ".coverage-card.delegated{border-color:rgba(29,78,216,.16);background:rgba(239,246,255,.9)}"
      },
      {
        "line": 362,
        "term": "gate",
        "sample": ".coverage-inline.delegated{background:rgba(239,246,255,.95);border-color:rgba(29,78,216,.12);color:#1d4ed8}"
      },
      {
        "line": 386,
        "term": "gate",
        "sample": ".event-pill.delegated{background:rgba(239,246,255,.95);color:#1d4ed8;border-color:rgba(29,78,216,.12)}"
      },
      {
        "line": 661,
        "term": "gate",
        "sample": "<div class=\"count-chip\">Vekâlet: {{ coverage_summary.delegated or 0 }} · Açıkta: {{ coverage_summary.uncovered or 0 }}</div>"
      },
      {
        "line": 665,
        "term": "gate",
        "sample": "<div class=\"coverage-card delegated\">"
      },
      {
        "line": 667,
        "term": "gate",
        "sample": "{% if delegated_assignments %}"
      },
      {
        "line": 668,
        "term": "gate",
        "sample": "{% for row in delegated_assignments %}"
      },
      {
        "line": 739,
        "term": "gate",
        "sample": "<div class=\"log-chip\"><i class=\"fa-solid fa-user-check\"></i> Vekâletle çözülen: <strong>{{ latest_assignment_log_summary.delegated or 0 }}</strong></div>"
      },
      {
        "line": 769,
        "term": "gate",
        "sample": "{% elif row.event_type == 'delegated' %}Vekâlet"
      },
      {
        "line": 788,
        "term": "gate",
        "sample": "<div class=\"coverage-inline delegated\" style=\"margin-top:14px;\">"
      }
    ],
    "hit_count": 15
  },
  {
    "path": "app/templates/team_compare.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 56,
        "term": "json",
        "sample": "<div class=\"bys-pro-chart compact\"><canvas data-bys-chart=\"doughnut\" data-labels='{{ [\"70 altı\", \"70-90\", \"90 üstü\"]|tojson }}' data-datasets='{{ [{\"label\":\"Dağılım\",\"data\":[st.low_count|default(0,true), st.mid_count|default(0,true), st.hig"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/templates/weight_create.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 154,
        "term": "sync",
        "sample": "function syncFromFirst() {"
      },
      {
        "line": 162,
        "term": "sync",
        "sample": "function syncFromSecond() {"
      },
      {
        "line": 170,
        "term": "sync",
        "sample": "w1.addEventListener(\"input\", syncFromFirst);"
      },
      {
        "line": 171,
        "term": "sync",
        "sample": "w2.addEventListener(\"input\", syncFromSecond);"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/templates/weight_edit.html",
    "suffix": ".html",
    "hits": [
      {
        "line": 157,
        "term": "sync",
        "sample": "function syncFromFirst() {"
      },
      {
        "line": 165,
        "term": "sync",
        "sample": "function syncFromSecond() {"
      },
      {
        "line": 173,
        "term": "sync",
        "sample": "w1.addEventListener(\"input\", syncFromFirst);"
      },
      {
        "line": 174,
        "term": "sync",
        "sample": "w2.addEventListener(\"input\", syncFromSecond);"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/static/css/ai_decision_faz10.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ10_CSS_OK */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": ".ai-decision-faz10-page,"
      },
      {
        "line": 3,
        "term": "faz",
        "sample": ".ai-decision-faz10-panel {"
      },
      {
        "line": 7,
        "term": "faz",
        "sample": ".ai-decision-faz10-hero,"
      },
      {
        "line": 8,
        "term": "faz",
        "sample": ".ai-decision-faz10-panel {"
      },
      {
        "line": 16,
        "term": "faz",
        "sample": ".ai-decision-faz10-hero {"
      },
      {
        "line": 21,
        "term": "faz",
        "sample": ".ai-decision-faz10-hero p,"
      },
      {
        "line": 22,
        "term": "faz",
        "sample": ".ai-decision-faz10-eyebrow {"
      },
      {
        "line": 31,
        "term": "faz",
        "sample": ".ai-decision-faz10-hero h1,"
      },
      {
        "line": 32,
        "term": "faz",
        "sample": ".ai-decision-faz10-head h3 {"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ11_CSS_OK */"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/ai_decision_faz12.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ12_CSS_OK */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": ".ai-faz12-page{padding:1.25rem;max-width:1180px;margin:0 auto;color:#1f2937}.ai-faz12-final-panel,.ai-faz12-card,.ai-faz12-section{background:rgba(255,255,255,.88);border:1px solid rgba(139,0,0,.12);box-shadow:0 18px 45px rgba(31,41,55,.08)"
      },
      {
        "line": 5,
        "term": "faz",
        "sample": ".home-faz1-ai-decision-wrap{"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/ai_decision_faz5_scorecard.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ5_SCORECARD_CSS */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": ".ai-faz5-panel{margin:18px 0;border:1px solid rgba(139,0,0,.14);border-radius:26px;background:linear-gradient(135deg,rgba(139,0,0,.055),rgba(255,255,255,.96));box-shadow:0 18px 38px rgba(15,23,42,.07);padding:20px;color:#1f2937}"
      },
      {
        "line": 3,
        "term": "faz",
        "sample": ".ai-faz5-head{display:grid;grid-template-columns:minmax(0,1fr) 190px;gap:18px;align-items:stretch}"
      },
      {
        "line": 4,
        "term": "faz",
        "sample": ".ai-faz5-kicker{display:inline-flex;align-items:center;border-radius:999px;background:rgba(139,0,0,.08);color:#8B0000;font-weight:900;font-size:.78rem;padding:7px 11px;letter-spacing:.02em}"
      },
      {
        "line": 5,
        "term": "faz",
        "sample": ".ai-faz5-head h3{margin:10px 0 6px;font-size:1.25rem;line-height:1.25;color:#111827;font-weight:950}.ai-faz5-head p{margin:0;color:#64748b;line-height:1.55}"
      },
      {
        "line": 6,
        "term": "faz",
        "sample": ".ai-faz5-score{border:1px solid rgba(15,23,42,.08);border-radius:22px;background:#fff;display:flex;flex-direction:column;justify-content:center;text-align:center;padding:14px;min-height:128px}.ai-faz5-score span{color:#64748b;font-size:.78r"
      },
      {
        "line": 7,
        "term": "faz",
        "sample": ".ai-faz5-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-top:16px}.ai-faz5-card{border:1px solid rgba(15,23,42,.08);border-radius:18px;background:rgba(255,255,255,.94);padding:14px}.ai-faz5-card sp"
      },
      {
        "line": 8,
        "term": "faz",
        "sample": ".ai-faz5-recommendations{margin-top:16px;border-top:1px solid rgba(15,23,42,.08);padding-top:16px}.ai-faz5-recommendations h4{margin:0 0 10px;font-size:1rem;color:#111827;font-weight:950}.ai-faz5-rec{border-radius:16px;border:1px solid rgba"
      },
      {
        "line": 9,
        "term": "faz",
        "sample": ".ai-faz5-safe-note{margin:14px 0 0;color:#64748b;font-size:.86rem;line-height:1.5}"
      },
      {
        "line": 10,
        "term": "faz",
        "sample": "@media(max-width:760px){.ai-faz5-head{grid-template-columns:1fr}.ai-faz5-score{min-height:110px}.ai-faz5-panel{padding:16px;border-radius:22px}}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/ai_decision_faz6_low_performance.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": ".bys360-faz6-approval-panel{"
      },
      {
        "line": 10,
        "term": "faz",
        "sample": ".faz6-panel-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:14px;}"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": ".faz6-kicker{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:#8B0000;font-weight:700;}"
      },
      {
        "line": 12,
        "term": "faz",
        "sample": ".bys360-faz6-approval-panel h3{margin:4px 0 6px;font-size:1.14rem;color:#1f2937;}"
      },
      {
        "line": 13,
        "term": "faz",
        "sample": ".bys360-faz6-approval-panel p{margin:0;color:#4b5563;line-height:1.55;}"
      },
      {
        "line": 14,
        "term": "faz",
        "sample": ".faz6-badge{display:inline-flex;align-items:center;border-radius:999px;padding:8px 12px;background:rgba(139,0,0,.08);color:#8B0000;font-weight:700;white-space:nowrap;}"
      },
      {
        "line": 15,
        "term": "faz",
        "sample": ".faz6-panel-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;}"
      },
      {
        "line": 16,
        "term": "faz",
        "sample": ".faz6-panel-grid article{border:1px solid rgba(17,24,39,.08);border-radius:18px;padding:14px;background:rgba(255,255,255,.72);}"
      },
      {
        "line": 17,
        "term": "faz",
        "sample": ".faz6-panel-grid strong{display:block;color:#111827;font-size:1rem;margin-bottom:6px;}"
      },
      {
        "line": 18,
        "term": "faz",
        "sample": ".faz6-panel-grid span{display:block;color:#4b5563;font-size:.92rem;line-height:1.45;}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/ai_decision_faz7_historical_archive.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ7_HISTORICAL_ARCHIVE_CSS */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel {"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__header {"
      },
      {
        "line": 18,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__eyebrow {"
      },
      {
        "line": 26,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel h3 {"
      },
      {
        "line": 31,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__badge {"
      },
      {
        "line": 42,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__grid {"
      },
      {
        "line": 48,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__card {"
      },
      {
        "line": 54,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__card span {"
      },
      {
        "line": 60,
        "term": "faz",
        "sample": ".ai-decision-faz7-panel__card strong {"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/ai_decision_faz8_period_scope.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_CSS */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": ".ai-decision-faz8-panel {"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": ".ai-decision-faz8-head {"
      },
      {
        "line": 17,
        "term": "faz",
        "sample": ".ai-decision-faz8-kicker {"
      },
      {
        "line": 23,
        "term": "faz",
        "sample": ".ai-decision-faz8-head h3 {"
      },
      {
        "line": 28,
        "term": "faz",
        "sample": ".ai-decision-faz8-head p,"
      },
      {
        "line": 29,
        "term": "faz",
        "sample": ".ai-decision-faz8-grid span,"
      },
      {
        "line": 30,
        "term": "faz",
        "sample": ".ai-decision-faz8-note {"
      },
      {
        "line": 34,
        "term": "faz",
        "sample": ".ai-decision-faz8-link {"
      },
      {
        "line": 43,
        "term": "faz",
        "sample": ".ai-decision-faz8-grid {"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/ai_decision_faz9_reminder.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_AI_DECISION_FAZ9_REMINDER_CSS */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": ".ai-faz9-reminder-panel {"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": ".ai-faz9-reminder-header {"
      },
      {
        "line": 18,
        "term": "faz",
        "sample": ".ai-faz9-reminder-header h3 {"
      },
      {
        "line": 23,
        "term": "faz",
        "sample": ".ai-faz9-reminder-header p {"
      },
      {
        "line": 28,
        "term": "faz",
        "sample": ".ai-faz9-eyebrow {"
      },
      {
        "line": 35,
        "term": "faz",
        "sample": ".ai-faz9-badge {"
      },
      {
        "line": 44,
        "term": "faz",
        "sample": ".ai-faz9-grid {"
      },
      {
        "line": 49,
        "term": "faz",
        "sample": ".ai-faz9-grid article {"
      },
      {
        "line": 55,
        "term": "faz",
        "sample": ".ai-faz9-grid strong,"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/bys360_ai_agent_widget.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 10,
        "term": "gate",
        "sample": "AG-5 gate uyumluluk dosyasıdır."
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_android_responsive_core_p5b.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 88,
        "term": "json",
        "sample": ".json-output {"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_android_responsive_targeted_p5c.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 35,
        "term": "json",
        "sample": ".json-output {"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_assistant_module.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 173,
        "term": "gate",
        "sample": "/* BYS360_ASISTANI_MODULU_V12_FINAL_GATE_START */"
      },
      {
        "line": 184,
        "term": "gate",
        "sample": "/* BYS360_ASISTANI_MODULU_V12_FINAL_GATE_END */"
      },
      {
        "line": 170,
        "term": "contract",
        "sample": "/* BYS360_ASSISTANT_MODULE_TEACHING_CONTRACT_V7_CSS */"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/bys360_home_weather.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": ".home-faz1-shell{"
      },
      {
        "line": 5,
        "term": "faz",
        "sample": ".home-faz1-hero{"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": ".home-faz1-hero-main,"
      },
      {
        "line": 12,
        "term": "faz",
        "sample": ".home-faz1-weather-card,"
      },
      {
        "line": 13,
        "term": "faz",
        "sample": ".home-faz1-panel,"
      },
      {
        "line": 14,
        "term": "faz",
        "sample": ".home-faz1-status-band,"
      },
      {
        "line": 15,
        "term": "faz",
        "sample": ".home-faz1-quick-card{"
      },
      {
        "line": 21,
        "term": "faz",
        "sample": ".home-faz1-hero-main{"
      },
      {
        "line": 26,
        "term": "faz",
        "sample": ".home-faz1-hero-main:after{"
      },
      {
        "line": 37,
        "term": "faz",
        "sample": ".home-faz1-kicker,"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/bys360_ios_assistant_responsive_fix_v3.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 106,
        "term": "faz",
        "sample": "/* iPhone'da fazla giriş/tanıtım metinleri paneli boğmasın */"
      },
      {
        "line": 275,
        "term": "gate",
        "sample": "/* BYS360 iOS safe area gate marker */"
      },
      {
        "line": 276,
        "term": "gate",
        "sample": ".bys360-ios-safe-area-gate-marker {"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v4.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "gate",
        "sample": "/* BYS360_MOBILE_APP_EXPERIENCE_V4_FINAL_GATE"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_mobile_app_experience_v5.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_MOBILE_UYUM_FAZ1_V1_CSS"
      },
      {
        "line": 20,
        "term": "faz",
        "sample": "html.bys360-mobile-faz1-v1,"
      },
      {
        "line": 21,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1{"
      },
      {
        "line": 28,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 *,"
      },
      {
        "line": 29,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 *::before,"
      },
      {
        "line": 30,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 *::after{box-sizing:border-box;}"
      },
      {
        "line": 31,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 img,"
      },
      {
        "line": 32,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 svg,"
      },
      {
        "line": 33,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 video,"
      },
      {
        "line": 34,
        "term": "faz",
        "sample": "body.bys360-mobile-faz1-v1 canvas{max-width:100%;height:auto;}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/bys360_mobile_clean_native_v4.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 3,
        "term": "faz",
        "sample": "Önceki Faz1/V2/V3 dosyaları base.html'den devre dışı bırakılır; bu dosya mobilde tek otoritedir. */"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_mobile_native_shell_v2.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "faz",
        "sample": "Faz 3 sonrası gerçek cihaz/PWA/WebView mobil deneyim düzeltmesi."
      },
      {
        "line": 32,
        "term": "faz",
        "sample": "/* Native/PWA içinde kurulum kartları ve web fazından gelen fazlalıklar gizli kalsın. */"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/static/css/bys360_native_app_bridge_v1.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "faz",
        "sample": "Faz 3 gerçek mobil app kabuğu için güvenli UI uyum katmanı."
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_performance_archive_excel_v1.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PHASE7_3_PERFORMANCE_ARCHIVE_EXCEL_CSS */"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_phase11_process_engine.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PHASE11_PROCESS_UI_POLISH"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_phase7_scorecard_ui_v1.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PHASE7_SCORECARD_UI_REDESIGN_V1 */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": "/* BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT */"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/static/css/bys360_portal.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 536,
        "term": "sync",
        "sample": ".portal-instagram-sync-card p,"
      },
      {
        "line": 537,
        "term": "sync",
        "sample": ".portal-instagram-sync-card small {"
      },
      {
        "line": 610,
        "term": "sync",
        "sample": ".portal-instagram-sync-card p{color:#6b7280;line-height:1.45;}"
      },
      {
        "line": 628,
        "term": "sync",
        "sample": ".portal-instagram-sync-card,"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/static/css/bys360_portal_experience_v2d1_profile_visual_fix.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 70,
        "term": "faz",
        "sample": "/* Küçük sol kartta 'Kurumsal Profil' etiketi fazla kalabalık yapıyordu. */"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/bys360_pwa_install_v1.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* BYS360_MOBILE_PWA_FAZ2_V1_CSS"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_1_REAL_ADVANCED_UI */"
      },
      {
        "line": 105,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX */"
      },
      {
        "line": 129,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX */"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase5.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL */"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".cic-phase5{--phase5-green:#087443;--phase5-amber:#b54708;--phase5-red:#b42318;--phase5-blue:#175cd3}.cic-phase5-hero{position:relative;overflow:hidden}.cic-phase5-hero:after{content:\"\";position:absolute;inset:auto -80px -120px auto;width:3"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase6.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".cic-phase6-command{border:1px solid rgba(139,0,0,.18);background:linear-gradient(135deg,#fff,#fff7f5)}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".cic-phase6-score-row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:14px}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".cic-phase6-score{border-radius:20px;padding:16px;background:linear-gradient(180deg,#8B0000,#5c0000);color:#fff;box-shadow:0 14px 32px rgba(139,0,0,.16)}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".cic-phase6-score.small{width:118px;text-align:center;padding:12px 14px}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".cic-phase6-score strong{display:block;font-size:30px;line-height:1;letter-spacing:-.04em}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".cic-phase6-score span{display:block;font-size:12px;color:rgba(255,255,255,.82);margin-top:6px}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".cic-phase6-blockers{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:14px}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".cic-phase6-note,.cic-phase6-live-gate{background:linear-gradient(180deg,#ffffff,#fffaf8);border-color:rgba(139,0,0,.12)}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".cic-phase6-inline-checks{display:flex;flex-wrap:wrap;gap:9px;margin-top:10px}"
      },
      {
        "line": 9,
        "term": "gate",
        "sample": ".cic-phase6-note,.cic-phase6-live-gate{background:linear-gradient(180deg,#ffffff,#fffaf8);border-color:rgba(139,0,0,.12)}"
      }
    ],
    "hit_count": 11
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".cic-phase7-release{border:1px solid rgba(139,0,0,.16);background:linear-gradient(135deg,#ffffff 0%,#fff7f4 55%,#fff 100%);position:relative;overflow:hidden}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".cic-phase7-release:before{content:\"\";position:absolute;right:-80px;top:-80px;width:220px;height:220px;border-radius:50%;background:rgba(139,0,0,.08)}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".cic-phase7-release-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:14px;position:relative;z-index:1}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".cic-phase7-release-card{border:1px solid rgba(15,23,42,.08);border-radius:20px;background:rgba(255,255,255,.88);padding:16px;box-shadow:0 14px 28px rgba(15,23,42,.06)}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".cic-phase7-release-card i{width:38px;height:38px;border-radius:15px;display:grid;place-items:center;background:#fff1f3;color:#8B0000;margin-bottom:10px}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".cic-phase7-release-card strong{display:block;color:#101828;font-size:15px}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".cic-phase7-release-card span{display:block;color:#667085;font-size:12.5px;line-height:1.45;margin-top:5px}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".cic-phase7-timeline{display:grid;gap:10px;margin-top:12px}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".cic-phase7-step{display:grid;grid-template-columns:38px 1fr auto;gap:12px;align-items:start;border:1px solid rgba(15,23,42,.08);border-radius:18px;background:#fff;padding:14px}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI */"
      },
      {
        "line": 382,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX */"
      },
      {
        "line": 406,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX */"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_7_release_clean.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_7_RELEASE_CLEAN_UI: styles are embedded in system.html intentionally for local reliability. */"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX */"
      },
      {
        "line": 27,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX */"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_8_base_header_pro.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_8_BASE_HEADER_PRO */\\n:root{\\n  --cic-red:#8B0000;\\n  --cic-red-2:#650000;\\n  --cic-ink:#111827;\\n  --cic-muted:#667085;\\n  --cic-line:rgba(17,24,39,.10);\\n  --cic-soft:#fff6f6;\\n  --cic-bg"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX */"
      },
      {
        "line": 27,
        "term": "phase",
        "sample": "/* BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX */"
      },
      {
        "line": 51,
        "term": "phase",
        "sample": "/* BYS360_PHASE7_12_COMPAT */"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_9_base_clean.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "/* BYS360 Corporate Information Center V3.0 Phase 7.9 - clean base header */"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/corporate_information_center_v4_0_celebrations.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 3,
        "term": "json",
        "sample": ".cic-v40-hero h2{margin:.35rem 0 .45rem;font-size:1.65rem;color:#2b1111}.cic-v40-hero p{margin:0;max-width:820px;color:#5e4a4a;line-height:1.65}.cic-v40-hero-stats{display:grid;grid-template-columns:repeat(3,minmax(110px,1fr));gap:12px}.cic"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/corporate_information_center_v4_4_performance_style.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 3,
        "term": "faz",
        "sample": "Kurumsal Bilgilendirme Merkezi, /performans/v2/faz3 çizgisine yakın sade yüzeyler. */"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/corporate_information_center_v4_6b_celebrations_final.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 27,
        "term": "json",
        "sample": "body .cic-celeb-json{font-family:Consolas,Monaco,monospace;min-height:220px;line-height:1.55;} body .cic-celeb-upload-zone{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(280px,.8fr);gap:14px;} body .cic-celeb-drop{border:1px dash"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/corporate_information_center_v4_6_celebrations_studio.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 78,
        "term": "json",
        "sample": "body.bys360-cic-v46-celebrations .cic-celeb-json{font-family:Consolas,Monaco,monospace!important;min-height:220px!important;line-height:1.55!important;}"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/css/faz1_mobile_foundation.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 336,
        "term": "phase",
        "sample": "/* Login phase 1 */"
      },
      {
        "line": 405,
        "term": "phase",
        "sample": "/* Dashboard phase 1 */"
      },
      {
        "line": 2,
        "term": "faz",
        "sample": "--faz1-safe-bottom: calc(84px + env(safe-area-inset-bottom));"
      },
      {
        "line": 53,
        "term": "faz",
        "sample": "padding-bottom: calc(var(--faz1-safe-bottom) + 18px);"
      },
      {
        "line": 180,
        "term": "faz",
        "sample": "padding: 14px 14px calc(var(--faz1-safe-bottom) + 18px) 14px;"
      },
      {
        "line": 254,
        "term": "faz",
        "sample": "padding: 12px 12px calc(var(--faz1-safe-bottom) + 14px) 12px;"
      },
      {
        "line": 313,
        "term": "faz",
        "sample": "padding: 10px 10px calc(var(--faz1-safe-bottom) + 12px) 10px;"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/static/css/faz27_profile_kapak_hotfix.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* FAZ 27 – Portal sol profil kartı kapak alanı düzeltmesi"
      },
      {
        "line": 4,
        "term": "faz",
        "sample": "ve avatarın kapağın içine fazla gömülmesini engellemek. */"
      },
      {
        "line": 54,
        "term": "faz",
        "sample": "/* Eğer doğrudan ilk bloksa fazla yüksek header alanını kıs */"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/faz3_communication_hr_mobile.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "/* Faz 3 responsive güçlendirmesi: izin/vekâlet + bildirim + mesajlar */"
      },
      {
        "line": 4,
        "term": "faz",
        "sample": ".faz3-mobile-scroll-x{overflow-x:auto;-webkit-overflow-scrolling:touch}"
      },
      {
        "line": 5,
        "term": "faz",
        "sample": ".faz3-mobile-hidden{display:none}"
      },
      {
        "line": 6,
        "term": "faz",
        "sample": ".faz3-mobile-stack{display:grid;gap:12px}"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/static/css/faz4_support_account_mobile.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "faz",
        "sample": "/* Faz 4 responsive overlay: survey + support + settings + account */"
      },
      {
        "line": 4,
        "term": "faz",
        "sample": ".faz4-mobile-table-cards{display:none;gap:12px;margin-top:16px}"
      },
      {
        "line": 5,
        "term": "faz",
        "sample": ".faz4-mobile-record-card{background:rgba(255,255,255,.96);border:1px solid rgba(15,23,42,.08);border-radius:18px;padding:14px;box-shadow:0 10px 24px rgba(15,23,42,.06)}"
      },
      {
        "line": 6,
        "term": "faz",
        "sample": ".faz4-mobile-record-card__head{display:grid;gap:6px;padding-bottom:10px;border-bottom:1px solid rgba(15,23,42,.08);margin-bottom:10px}"
      },
      {
        "line": 7,
        "term": "faz",
        "sample": ".faz4-mobile-record-card__title{font-size:.98rem;font-weight:900;color:#111827;line-height:1.55}"
      },
      {
        "line": 8,
        "term": "faz",
        "sample": ".faz4-mobile-record-card__meta{font-size:.8rem;color:#6b7280;line-height:1.6}"
      },
      {
        "line": 9,
        "term": "faz",
        "sample": ".faz4-mobile-record-card__body{display:grid;gap:10px}"
      },
      {
        "line": 10,
        "term": "faz",
        "sample": ".faz4-mobile-field{display:grid;gap:6px}"
      },
      {
        "line": 11,
        "term": "faz",
        "sample": ".faz4-mobile-field__label{font-size:.75rem;font-weight:900;color:#8B0000;text-transform:uppercase;letter-spacing:.04em}"
      },
      {
        "line": 12,
        "term": "faz",
        "sample": ".faz4-mobile-field__value{font-size:.88rem;color:#374151;line-height:1.7;word-break:break-word}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/performance_completion_phase10_reminder.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase10-reminder-panel{margin:18px 0;padding:18px;border:1px solid rgba(139,0,0,.16);border-radius:18px;background:rgba(255,255,255,.82);box-shadow:0 14px 34px rgba(20,20,20,.08);backdrop-filter:blur(8px)}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".bys360-phase10-reminder-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;border-bottom:1px solid rgba(139,0,0,.10);padding-bottom:12px;margin-bottom:14px}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".bys360-phase10-reminder-head h3{margin:0;color:#8B0000;font-size:1.08rem;font-weight:800;letter-spacing:.01em}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".bys360-phase10-reminder-head p{margin:6px 0 0;color:#555;line-height:1.45}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".bys360-phase10-badge{display:inline-flex;align-items:center;white-space:nowrap;border-radius:999px;background:#8B0000;color:#fff;padding:7px 12px;font-weight:700;font-size:.82rem}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".bys360-phase10-reminder-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".bys360-phase10-card{border:1px solid rgba(139,0,0,.12);border-radius:14px;padding:13px;background:rgba(255,255,255,.74)}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".bys360-phase10-card strong{display:block;color:#2a2a2a;margin-bottom:6px}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".bys360-phase10-card span{display:block;color:#626262;font-size:.92rem;line-height:1.4}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/performance_completion_phase11_period_scope_assignment.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase11-panel{"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": ".bys360-phase11-panel__title{"
      },
      {
        "line": 17,
        "term": "phase",
        "sample": ".bys360-phase11-panel__body{color:#333;line-height:1.55;font-size:.95rem;}"
      },
      {
        "line": 18,
        "term": "phase",
        "sample": ".bys360-phase11-panel__body ul{margin:8px 0 0 18px;padding:0;}"
      },
      {
        "line": 19,
        "term": "phase",
        "sample": ".bys360-phase11-badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:6px 10px;background:rgba(139,0,0,.08);color:#8B0000;font-weight:600;font-size:.86rem;}"
      },
      {
        "line": 20,
        "term": "phase",
        "sample": "@media (max-width: 768px){.bys360-phase11-panel{padding:14px;margin:12px 0}.bys360-phase11-panel__body{font-size:.9rem}}"
      }
    ],
    "hit_count": 7
  },
  {
    "path": "app/static/css/performance_completion_phase12_final_gate.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase12-final-gate-panel{"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".phase12-final-gate-header{"
      },
      {
        "line": 19,
        "term": "phase",
        "sample": ".phase12-final-gate-header h3{"
      },
      {
        "line": 25,
        "term": "phase",
        "sample": ".phase12-final-gate-header p{"
      },
      {
        "line": 30,
        "term": "phase",
        "sample": ".phase12-final-gate-badge{"
      },
      {
        "line": 39,
        "term": "phase",
        "sample": ".phase12-final-gate-grid{"
      },
      {
        "line": 44,
        "term": "phase",
        "sample": ".phase12-final-gate-card{"
      },
      {
        "line": 50,
        "term": "phase",
        "sample": ".phase12-final-gate-card strong{"
      },
      {
        "line": 55,
        "term": "phase",
        "sample": ".phase12-final-gate-card span{"
      },
      {
        "line": 1,
        "term": "gate",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE_CSS */"
      },
      {
        "line": 2,
        "term": "gate",
        "sample": ".bys360-phase12-final-gate-panel{"
      },
      {
        "line": 10,
        "term": "gate",
        "sample": ".phase12-final-gate-header{"
      },
      {
        "line": 19,
        "term": "gate",
        "sample": ".phase12-final-gate-header h3{"
      },
      {
        "line": 25,
        "term": "gate",
        "sample": ".phase12-final-gate-header p{"
      },
      {
        "line": 30,
        "term": "gate",
        "sample": ".phase12-final-gate-badge{"
      },
      {
        "line": 39,
        "term": "gate",
        "sample": ".phase12-final-gate-grid{"
      },
      {
        "line": 44,
        "term": "gate",
        "sample": ".phase12-final-gate-card{"
      },
      {
        "line": 50,
        "term": "gate",
        "sample": ".phase12-final-gate-card strong{"
      },
      {
        "line": 55,
        "term": "gate",
        "sample": ".phase12-final-gate-card span{"
      }
    ],
    "hit_count": 20
  },
  {
    "path": "app/static/css/performance_completion_phase5_scorecard_ui.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ":root{--bys-phase5-primary:#8B0000;--bys-phase5-ink:#111827;--bys-phase5-muted:#64748b;--bys-phase5-border:rgba(15,23,42,.10);--bys-phase5-soft:rgba(139,0,0,.07);--bys-phase5-danger:#991b1b;--bys-phase5-success:#166534}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".bys360-phase5-scorecard,.phase5-scorecard-shell{display:grid;gap:16px;max-width:1560px;margin:0 auto 40px}.bys360-phase5-hero,.bys360-phase5-score-hero{display:grid;grid-template-columns:minmax(220px,320px) minmax(0,1fr);gap:16px;align-ite"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/css/performance_completion_phase6_low_score_process.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-panel{border:1px solid rgba(139,0,0,.16);border-left:5px solid #8B0000;border-radius:18px;background:rgba(255,255,255,.86);box-shadow:0 10px 30px rgba(0,0,0,.06);padding:18px;margin:16px 0;}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-title{font-weight:800;color:#8B0000;font-size:1.05rem;margin-bottom:12px;}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-grid div{background:rgba(139,0,0,.035);border-radius:14px;padding:12px;}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-grid strong{display:block;color:#3b3b3b;font-size:.82rem;margin-bottom:4px;}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-grid span{display:block;color:#111;font-weight:700;}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".bys360-phase6-low-score-note{margin:12px 0 0;color:#555;line-height:1.55;}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "@media (max-width:700px){.bys360-phase6-low-score-panel{padding:14px;border-radius:14px}.bys360-phase6-low-score-grid{grid-template-columns:1fr}}"
      }
    ],
    "hit_count": 9
  },
  {
    "path": "app/static/css/performance_completion_phase7_scorecard_archive.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase7-archive-panel{margin:18px 0;padding:18px;border:1px solid rgba(139,0,0,.16);border-radius:18px;background:rgba(255,255,255,.86);box-shadow:0 12px 32px rgba(31,41,55,.08);backdrop-filter:blur(8px)}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".bys360-phase7-archive-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:14px}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".bys360-phase7-archive-head h3{margin:2px 0 6px;font-size:1.18rem;color:#2f1720;font-weight:800}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".bys360-phase7-archive-head p{margin:0;color:#5f6673;line-height:1.55}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".bys360-phase7-kicker{font-size:.78rem;color:#8B0000;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin:0!important}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".bys360-phase7-badge{display:inline-flex;align-items:center;padding:7px 11px;border-radius:999px;background:rgba(139,0,0,.1);color:#8B0000;font-weight:800;white-space:nowrap}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".bys360-phase7-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".bys360-phase7-card{padding:14px;border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(248,250,252,.9));border:1px solid rgba(15,23,42,.08)}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".bys360-phase7-card strong{display:block;color:#1f2937;margin-bottom:6px;font-size:.94rem}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/performance_completion_phase8_midterm_feedback.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase8-midterm-panel{margin:18px 0;padding:18px;border:1px solid rgba(139,0,0,.16);border-radius:18px;background:rgba(255,255,255,.88);box-shadow:0 12px 32px rgba(31,41,55,.08);backdrop-filter:blur(8px)}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".bys360-phase8-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:14px}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".bys360-phase8-head h3{margin:2px 0 6px;font-size:1.18rem;color:#2f1720;font-weight:800}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".bys360-phase8-head p{margin:0;color:#5f6673;line-height:1.55}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".bys360-phase8-kicker{font-size:.78rem;color:#8B0000;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin:0!important}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".bys360-phase8-badge{display:inline-flex;align-items:center;padding:7px 11px;border-radius:999px;background:rgba(139,0,0,.1);color:#8B0000;font-weight:800;white-space:nowrap}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".bys360-phase8-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".bys360-phase8-card{padding:14px;border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(248,250,252,.9));border:1px solid rgba(15,23,42,.08)}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".bys360-phase8-card strong{display:block;color:#1f2937;margin-bottom:6px;font-size:.94rem}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/performance_completion_phase9_development_guidance.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CSS */"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": ".bys360-phase9-guidance-panel{margin:18px 0;padding:18px;border:1px solid rgba(139,0,0,.16);border-radius:18px;background:rgba(255,255,255,.9);box-shadow:0 12px 34px rgba(31,41,55,.08);backdrop-filter:blur(8px)}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": ".bys360-phase9-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:14px}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": ".bys360-phase9-head h3{margin:2px 0 6px;font-size:1.18rem;color:#2f1720;font-weight:800}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": ".bys360-phase9-head p{margin:0;color:#5f6673;line-height:1.55}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".bys360-phase9-kicker{font-size:.78rem;color:#8B0000;font-weight:800;letter-spacing:.04em;text-transform:uppercase;margin:0!important}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": ".bys360-phase9-badge{display:inline-flex;align-items:center;padding:7px 11px;border-radius:999px;background:rgba(139,0,0,.1);color:#8B0000;font-weight:800;white-space:nowrap}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": ".bys360-phase9-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": ".bys360-phase9-card{padding:14px;border-radius:14px;background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(248,250,252,.9));border:1px solid rgba(15,23,42,.08)}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".bys360-phase9-card strong{display:block;color:#1f2937;margin-bottom:6px;font-size:.94rem}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/performance_phase3.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 5,
        "term": "phase",
        "sample": "@import url(\"./performance_phase3_parts/performance_phase3_part_01.css\");"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": "@import url(\"./performance_phase3_parts/performance_phase3_part_02.css\");"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": "@import url(\"./performance_phase3_parts/performance_phase3_part_03.css\");"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "@import url(\"./performance_phase3_parts/performance_phase3_part_04.css\");"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "@import url(\"./performance_phase3_parts/performance_phase3_part_05.css\");"
      }
    ],
    "hit_count": 5
  },
  {
    "path": "app/static/css/phase5_5_scorecard_mobile.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "/* BYS360_PHASE5_5_SCORECARD_MOBILE_LAYOUT"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": ".phase5-5-mobile-layout-note {"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": ".phase5-5-table-scroll,"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": ".phase5_5_mobile_table,"
      },
      {
        "line": 16,
        "term": "phase",
        "sample": ".phase5-5-scorecard-shell,"
      },
      {
        "line": 17,
        "term": "phase",
        "sample": ".phase5-5-scoring-shell {"
      },
      {
        "line": 22,
        "term": "phase",
        "sample": ".phase5-5-scorecard-shell,"
      },
      {
        "line": 23,
        "term": "phase",
        "sample": ".phase5-5-scoring-shell,"
      },
      {
        "line": 31,
        "term": "phase",
        "sample": ".phase5-5-table-scroll,"
      },
      {
        "line": 32,
        "term": "phase",
        "sample": ".phase5_5_mobile_table,"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/survey_jotform_phase1.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": ".jotform-phase1-shell{display:grid;gap:20px}"
      },
      {
        "line": 22,
        "term": "phase",
        "sample": ".phase1-preview-card{display:grid;gap:14px}"
      },
      {
        "line": 23,
        "term": "phase",
        "sample": ".phase1-preview-hero{padding:18px;border-radius:20px;border:1px solid rgba(139,0,0,.10);background:linear-gradient(135deg,rgba(139,0,0,.06),rgba(255,255,255,.96))}"
      },
      {
        "line": 24,
        "term": "phase",
        "sample": ".phase1-preview-kicker{display:inline-flex;align-items:center;gap:8px;min-height:26px;padding:0 10px;border-radius:999px;background:#fff;color:#8B0000;font-size:.72rem;font-weight:900;width:max-content;margin-bottom:10px}"
      },
      {
        "line": 25,
        "term": "phase",
        "sample": ".phase1-preview-title{font-size:1.05rem;font-weight:900;color:#111827;line-height:1.35;margin:0}"
      },
      {
        "line": 26,
        "term": "phase",
        "sample": ".phase1-preview-text{margin:8px 0 0;color:#6b7280;font-size:.83rem;line-height:1.7}"
      },
      {
        "line": 27,
        "term": "phase",
        "sample": ".phase1-preview-meta{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}"
      },
      {
        "line": 28,
        "term": "phase",
        "sample": ".phase1-preview-meta .item{padding:12px 14px;border-radius:16px;border:1px solid rgba(15,23,42,.06);background:#fff}"
      },
      {
        "line": 29,
        "term": "phase",
        "sample": ".phase1-preview-meta .label{display:block;font-size:.72rem;font-weight:900;color:#667085;text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}"
      },
      {
        "line": 30,
        "term": "phase",
        "sample": ".phase1-preview-meta .value{display:block;font-size:.92rem;font-weight:900;color:#111827;line-height:1.35}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/survey_jotform_phase2.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .builder-phase2-tip,"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .builder-phase2-inline-tip{border-radius:18px}"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .question-card.is-collapsed .phase2-card-summary{display:flex}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-card-summary{display:none;gap:8px;flex-wrap:wrap;padding:12px 14px;border-radius:16px;background:rgba(15,23,42,.03);border:1px dashed rgba(15,23,42,.08);margin-bottom:10px}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:#f8fafc;border:1px solid rgba(15,23,42,.08);font-size:.76rem;font-weight:800;color:#475569}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-tools{display:flex;gap:6px;flex-wrap:wrap;margin-right:4px}"
      },
      {
        "line": 11,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-icon-btn{width:38px;height:38px;border:none;border-radius:12px;background:#f8fafc;border:1px solid rgba(15,23,42,.08);display:inline-flex;align-items:center;justify-content:center;color:#334155;cursor:pointe"
      },
      {
        "line": 12,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-icon-btn:hover{transform:translateY(-1px);border-color:rgba(139,0,0,.24);color:#8B0000;background:#fff}"
      },
      {
        "line": 13,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-icon-btn.is-active{background:rgba(139,0,0,.08);color:#8B0000;border-color:rgba(139,0,0,.18)}"
      },
      {
        "line": 14,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase2-drag-handle{cursor:grab}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/survey_jotform_phase3.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 1,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-toolbar-card{padding:18px;border-radius:20px;background:rgba(255,255,255,.92);border:1px solid rgba(15,23,42,.08);box-shadow:0 14px 28px rgba(15,23,42,.06);margin-bottom:16px}"
      },
      {
        "line": 2,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-toolbar-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;flex-wrap:wrap;margin-bottom:12px}"
      },
      {
        "line": 3,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-toolbar-head h4{margin:0;font-size:1rem;font-weight:900;color:#111827}"
      },
      {
        "line": 4,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-toolbar-head p{margin:6px 0 0;font-size:.82rem;color:#64748b;line-height:1.6}"
      },
      {
        "line": 5,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-toolbar-actions{display:flex;flex-wrap:wrap;gap:8px}"
      },
      {
        "line": 6,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-btn{display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:0 14px;border-radius:12px;border:1px solid rgba(15,23,42,.08);background:#fff;color:#334155;font-weight:800;font-size:.8rem;cursor:p"
      },
      {
        "line": 7,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-btn:hover{transform:translateY(-1px);border-color:rgba(139,0,0,.24);color:#8B0000;background:rgba(139,0,0,.03)}"
      },
      {
        "line": 8,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-btn.primary{background:linear-gradient(180deg,#8B0000,#6f0000);color:#fff;border-color:transparent;box-shadow:0 12px 24px rgba(139,0,0,.16)}"
      },
      {
        "line": 9,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-toolbar-stats{display:flex;flex-wrap:wrap;gap:8px}"
      },
      {
        "line": 10,
        "term": "phase",
        "sample": "[data-survey-studio=\"1\"] .phase3-chip{display:inline-flex;align-items:center;gap:7px;padding:8px 12px;border-radius:999px;background:rgba(15,23,42,.05);border:1px solid rgba(15,23,42,.07);font-size:.76rem;font-weight:900;color:#475569}"
      }
    ],
    "hit_count": 10
  },
  {
    "path": "app/static/css/survey_jotform_phase4.css",
    "suffix": ".css",
    "hits": [
      {
        "line": 2,
        "term": "phase",
        "sample": ".phase4-results-note{background:linear-gradient(135deg, rgba(139,0,0,.10), rgba(139,0,0,.03));border:1px solid rgba(139,0,0,.10)}"
      }
    ],
    "hit_count": 1
  },
  {
    "path": "app/static/js/ai_runtime_summary.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 141,
        "term": "sync",
        "sample": "async function postFeedback(card, type) {"
      },
      {
        "line": 170,
        "term": "sync",
        "sample": "async function runRequest(card, mode) {"
      },
      {
        "line": 153,
        "term": "json",
        "sample": "'Content-Type': 'application/json',"
      },
      {
        "line": 158,
        "term": "json",
        "sample": "body: JSON.stringify({ feedback_type: type })"
      },
      {
        "line": 160,
        "term": "json",
        "sample": "const payload = await response.json();"
      },
      {
        "line": 196,
        "term": "json",
        "sample": "const payload = await response.json();"
      }
    ],
    "hit_count": 6
  },
  {
    "path": "app/static/js/analysis_center_ultra.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 5,
        "term": "json",
        "sample": "try { return JSON.parse(node.textContent || '{}'); } catch (err) { return {}; }"
      },
      {
        "line": 81,
        "term": "json",
        "sample": "fetch(url, { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })"
      },
      {
        "line": 82,
        "term": "json",
        "sample": ".then(resp => resp.json())"
      }
    ],
    "hit_count": 3
  },
  {
    "path": "app/static/js/announcement_popup.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 39,
        "term": "json",
        "sample": "}).then(function(resp){ return resp.json().then(function(data){ return {status: resp.status, data: data}; }); });"
      },
      {
        "line": 193,
        "term": "json",
        "sample": ".then(function(resp){ return resp.json(); })"
      }
    ],
    "hit_count": 2
  },
  {
    "path": "app/static/js/bys360_ai_agent_widget.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 5,
        "term": "gate",
        "sample": "* Eski gate etiketi: Güvenli Sanal Asistan"
      },
      {
        "line": 14,
        "term": "gate",
        "sample": "AG-5 gate uyumluluk dosyasıdır."
      },
      {
        "line": 16,
        "term": "gate",
        "sample": "Amaç: eski AG-5 gate'in beklediği bys360_ai_agent_widget.js dosya adını güvenli alias olarak sağlamak."
      },
      {
        "line": 29,
        "term": "gate",
        "sample": "var CANONICAL_GUARD = '__BYS360_ASSISTANT_MODULE_12STEP_STATUS_GATE_V8_LOADED__';"
      }
    ],
    "hit_count": 4
  },
  {
    "path": "app/static/js/bys360_ai_everywhere_v1.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 110,
        "term": "faz",
        "sample": "links:[['Dönem İçi Notlar','/performance/interim-notes'],['Gelişim Rehberi','/performance/meeting-development/faz10']]"
      },
      {
        "line": 121,
        "term": "faz",
        "sample": "links:[['Performans Yönetimi','/performance/dashboard'],['AI Karar Destek','/ai/decision-support/faz1/health']]"
      },
      {
        "line": 165,
        "term": "faz",
        "sample": "links:[['AI Karar Destek Merkezi','/ai/decision-support/faz1/health'],['Asistan Bilgi Bankası','/ai-agent/knowledge']]"
      },
      {
        "line": 198,
        "term": "faz",
        "sample": "links:[['AI Karar Destek','/ai/decision-support/faz1/health']]"
      },
      {
        "line": 209,
        "term": "faz",
        "sample": "links:[['BYS360 Asistanı','/ai-agent/panel'],['AI Karar Destek','/ai/decision-support/faz1/health']]"
      }
    ],
    "hit_count": 5
  },
  {
    "path": "app/static/js/bys360_assistant_module.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 114,
        "term": "faz",
        "sample": "{ title: 'Gelişim Rehberi', href: '/performance/meeting-development/faz10', keywords: ['gelisim rehberi', 'gelisim onerisi', 'egitim onerisi'], text: 'Değerlendirme sonrası gelişim önerileri ve rehber notlar için kullanılır.' },"
      },
      {
        "line": 120,
        "term": "faz",
        "sample": "{ title: 'AI Karar Destek Merkezi', href: '/ai/decision-support/faz1/health', keywords: ['ai karar', 'karar destek', 'analiz', 'risk', 'ozet'], text: 'Analiz ve karar destek katmanıdır; BYS360 Asistanı ise kullanıcı rehberlik katmanıdır.' }"
      },
      {
        "line": 866,
        "term": "faz",
        "sample": "return makeAnswer('BYS360 içindeki bilgi bankası, güvenli menü haritası, işlem adımları ve yetki kurallarıyla çalışırım. Yapay zekâ/akıllı yönlendirme katmanından yararlanabilirim; ancak BYS360 sınırlarının dışına çıkmam. Karar destek alanı"
      },
      {
        "line": 897,
        "term": "faz",
        "sample": "return makeAnswer('Performans notu için doğru yol: Sol şerit > Performans Yönetimi > Dönem İçi Notlar. Bu ekran puan verme ekranı değildir; dönem içindeki olumlu/olumsuz gözlem, başarı, gelişim ihtiyacı veya genel not kaydı için kullanılır."
      },
      {
        "line": 950,
        "term": "faz",
        "sample": "return makeAnswer('AI Karar Destek Merkezi; performans, personel, anket, destek ve rapor verilerinden özet, risk farkındalığı ve yönetici içgörüsü üretir. BYS360 Asistanı ise kullanım rehberi, güvenli menü yönlendirme ve işlem öğretme katma"
      },
      {
        "line": 2266,
        "term": "faz",
        "sample": "urls: [\"/performance/scorecards\", \"/performans/karne\", \"/performans/v2/faz5/scorecard\"],"
      },
      {
        "line": 2306,
        "term": "faz",
        "sample": "urls: [\"/performance/meeting-development/faz9\", \"/performance/meeting-development\"],"
      },
      {
        "line": 2346,
        "term": "faz",
        "sample": "urls: [\"/ai/decision-support/faz1/health\"],"
      },
      {
        "line": 2347,
        "term": "faz",
        "sample": "titles: [\"AI Karar Destek\", \"Faz 1 Health\"],"
      },
      {
        "line": 3353,
        "term": "faz",
        "sample": "\"/performance/meeting-development/faz10\": {"
      },
      {
        "line": 1128,
        "term": "json",
        "sample": "fetch('/ai-agent/api/assistant-widget-summary', { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })"
      },
      {
        "line": 1129,
        "term": "json",
        "sample": ".then(function (response) { if (!response.ok) throw new Error('summary'); return response.json(); })"
      },
      {
        "line": 1153,
        "term": "json",
        "sample": "method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },"
      },
      {
        "line": 1154,
        "term": "json",
        "sample": "body: JSON.stringify({ question: question, context: (typeof currentPageContext === 'function' ? currentPageContext() : {}) })"
      },
      {
        "line": 1157,
        "term": "json",
        "sample": "return response.json();"
      },
      {
        "line": 1223,
        "term": "json",
        "sample": "try { localStorage.setItem(STORAGE_POS, JSON.stringify({ left: root.style.left, top: root.style.top })); } catch (e) {}"
      },
      {
        "line": 1323,
        "term": "json",
        "sample": "var pos = JSON.parse(raw);"
      },
      {
        "line": 1372,
        "term": "json",
        "sample": "moveTo: function (left, top) { var pos = { x: Number(left) || 24, y: Number(top) || 24 }; root.style.left = pos.x + 'px'; root.style.top = pos.y + 'px'; root.style.right = 'auto'; root.style.bottom = 'auto'; try { localStorage.setItem(STORA"
      },
      {
        "line": 5785,
        "term": "json",
        "sample": "var parsed = JSON.parse(raw);"
      },
      {
        "line": 5807,
        "term": "json",
        "sample": "var data = JSON.stringify(history.slice(-MAX_HISTORY));"
      }
    ],
    "hit_count": 35
  },
  {
    "path": "app/static/js/bys360_assistant_performance_kb_v10.js",
    "suffix": ".js",
    "hits": [
      {
        "line": 25,
        "term": "faz",
        "sample": "delays: safeRoute('Performans Yönetimi > Hatırlatma ve Aksatan Amirler', '/performance/meeting-development/faz9')"
      }
    ],
    "hit_count": 1
  }
]
```

## Not

Bu rapor dosya silmez veya taşımaz. Adaylar manuel/kurallı sınıflandırmadan sonra A10B aşamasında karantina ya da düzeltme planına alınacaktır.