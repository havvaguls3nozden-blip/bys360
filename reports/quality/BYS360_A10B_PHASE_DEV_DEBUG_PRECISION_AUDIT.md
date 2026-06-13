# BYS360 A10B Hassas Faz / Dev / Debug Sınıflandırma Audit

Tarih: 2026-06-12T19:48:14

## Özet

- A10A file candidate count: 970
- A10A UI technical file count: 395
- Runtime rename candidate count: 199
- Cleanup candidate count: 59
- Hard UI technical file count: 20
- A10B OK: False

## Dosya Sınıflandırması

```json
{
  "runtime_cleanup_review": 7,
  "likely_false_positive_name": 490,
  "runtime_rename_candidate": 199,
  "runtime_review": 22,
  "contract_or_quality_keep_review": 142,
  "review": 56,
  "cleanup_candidate": 43,
  "windows_script_review": 2,
  "windows_legacy_script_cleanup_candidate": 9
}
```

## UI Teknik Dil Sınıflandırması

```json
{
  "ui_review_technical_language": 374,
  "ui_likely_false_positive": 1,
  "ui_hard_technical_language": 20
}
```

## Runtime Rename Adayları İlk 200

```json
[
  {
    "path": "app/admin/ai_phase10_routes.py",
    "name": "ai_phase10_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase11_routes.py",
    "name": "ai_phase11_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase12_routes.py",
    "name": "ai_phase12_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase2_routes.py",
    "name": "ai_phase2_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase5_routes.py",
    "name": "ai_phase5_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase6_routes.py",
    "name": "ai_phase6_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase7_routes.py",
    "name": "ai_phase7_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase8_routes.py",
    "name": "ai_phase8_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/admin/ai_phase9_routes.py",
    "name": "ai_phase9_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz10_routes.py",
    "name": "decision_support_faz10_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz11_routes.py",
    "name": "decision_support_faz11_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz12_routes.py",
    "name": "decision_support_faz12_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz1_ui_safe.py",
    "name": "decision_support_faz1_ui_safe.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz3_routes.py",
    "name": "decision_support_faz3_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz4_routes.py",
    "name": "decision_support_faz4_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz5_routes.py",
    "name": "decision_support_faz5_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz6_routes.py",
    "name": "decision_support_faz6_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz7_routes.py",
    "name": "decision_support_faz7_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz8_routes.py",
    "name": "decision_support_faz8_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/ai/decision_support_faz9_routes.py",
    "name": "decision_support_faz9_routes.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase1_routes.py",
    "name": "phase1_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase2_routes.py",
    "name": "phase2_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase3_routes.py",
    "name": "phase3_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase4_routes.py",
    "name": "phase4_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase5_routes.py",
    "name": "phase5_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase8_routes.py",
    "name": "phase8_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase9a_routes.py",
    "name": "phase9a_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase9b_routes.py",
    "name": "phase9b_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase9c_routes.py",
    "name": "phase9c_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase9d_routes.py",
    "name": "phase9d_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase9_routes.py",
    "name": "phase9_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/communication/phase_family_routes.py",
    "name": "phase_family_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/config/faz6_engine_patch.py",
    "name": "faz6_engine_patch.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/GO_LIVE_PERFORMANCE_FAZ2_3_NORMALIZE_WEIGHT_INPUTS_FIX.md",
    "name": "GO_LIVE_PERFORMANCE_FAZ2_3_NORMALIZE_WEIGHT_INPUTS_FIX.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/institutional/hr_personnel_phase10_routes.py",
    "name": "hr_personnel_phase10_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/institutional/hr_personnel_phase11_routes.py",
    "name": "hr_personnel_phase11_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/institutional/hr_personnel_phase12_routes.py",
    "name": "hr_personnel_phase12_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/institutional/hr_personnel_phase13_routes.py",
    "name": "hr_personnel_phase13_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/models/communication_phase1_models.py",
    "name": "communication_phase1_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/models/communication_phase2_models.py",
    "name": "communication_phase2_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/models/communication_phase3_models.py",
    "name": "communication_phase3_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/models/communication_phase4_models.py",
    "name": "communication_phase4_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/models/communication_phase5_models.py",
    "name": "communication_phase5_models.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/feedback_corporate_cleanup_phase6_routes.py",
    "name": "feedback_corporate_cleanup_phase6_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/feedback_final_gate_phase5_routes.py",
    "name": "feedback_final_gate_phase5_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/feedback_followup_phase4_routes.py",
    "name": "feedback_followup_phase4_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/phase10_scorecard_integration.py",
    "name": "phase10_scorecard_integration.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/process_engine_phase10_reports_routes.py",
    "name": "process_engine_phase10_reports_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/process_engine_phase6_president_approvals_routes.py",
    "name": "process_engine_phase6_president_approvals_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/performance/process_engine_phase8_tracking_routes.py",
    "name": "process_engine_phase8_tracking_routes.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1e_deletion_allowlist.py",
    "name": "faz1e_deletion_allowlist.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1f_family_targets.py",
    "name": "faz1f_family_targets.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1g_selected_merge_specs.py",
    "name": "faz1g_selected_merge_specs.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1h_selected_targets.py",
    "name": "faz1h_selected_targets.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1i_required_merge_spec.py",
    "name": "faz1i_required_merge_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1j_selected_route_melt_spec.py",
    "name": "faz1j_selected_route_melt_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1k_phase_family_spec.py",
    "name": "faz1k_phase_family_spec.py",
    "suffix": ".py",
    "hits": [
      "faz",
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1l_family_melt_spec.py",
    "name": "faz1l_family_melt_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/faz1m_service_delegate_spec.py",
    "name": "faz1m_service_delegate_spec.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/phase_alias_manifest.py",
    "name": "phase_alias_manifest.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/refactor/schema_guard_faz1d_bundle.py",
    "name": "schema_guard_faz1d_bundle.py",
    "suffix": ".py",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase1_service.py",
    "name": "communication_phase1_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase2_service.py",
    "name": "communication_phase2_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase3_service.py",
    "name": "communication_phase3_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase4_service.py",
    "name": "communication_phase4_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase5_service.py",
    "name": "communication_phase5_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase8_service.py",
    "name": "communication_phase8_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase9a_service.py",
    "name": "communication_phase9a_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase9b_service.py",
    "name": "communication_phase9b_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase9c_service.py",
    "name": "communication_phase9c_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase9d_service.py",
    "name": "communication_phase9d_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/communication_phase9_service.py",
    "name": "communication_phase9_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/role_matrix_phase4_gate_service.py",
    "name": "role_matrix_phase4_gate_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/role_matrix_phase5_final_gate_service.py",
    "name": "role_matrix_phase5_final_gate_service.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/ai/FAZ7_ANALIZ_MERKEZI_EXCEL_ONIZLEME.md",
    "name": "FAZ7_ANALIZ_MERKEZI_EXCEL_ONIZLEME.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/DUYURU_YONETIMI_VIDEO_POPUP_FAZ1_NOTU.md",
    "name": "DUYURU_YONETIMI_VIDEO_POPUP_FAZ1_NOTU.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ1_ROUTE_OWNERSHIP.md",
    "name": "FAZ1_ROUTE_OWNERSHIP.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ2_HARDENING_NOTES.md",
    "name": "FAZ2_HARDENING_NOTES.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ3_SURVEY_LIFECYCLE_NOTES.md",
    "name": "FAZ3_SURVEY_LIFECYCLE_NOTES.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ4_ANALYTICS_NOTES.md",
    "name": "FAZ4_ANALYTICS_NOTES.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ5_OPERATIONS_NOTES.md",
    "name": "FAZ5_OPERATIONS_NOTES.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ6_PULSE_CAMPAIGN_NOTES.md",
    "name": "FAZ6_PULSE_CAMPAIGN_NOTES.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ7_CANLI_ONCESI_SON_KONTROL.md",
    "name": "FAZ7_CANLI_ONCESI_SON_KONTROL.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ7_TEST_STRATEJISI.md",
    "name": "FAZ7_TEST_STRATEJISI.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ7_UAT_CHECKLIST.md",
    "name": "FAZ7_UAT_CHECKLIST.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ8_PILOT_RUNBOOK.md",
    "name": "FAZ8_PILOT_RUNBOOK.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9A_ENV_CHECKLIST.md",
    "name": "FAZ9A_ENV_CHECKLIST.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9A_SMOKE_TEST_MATRIX.md",
    "name": "FAZ9A_SMOKE_TEST_MATRIX.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9A_TEKNIK_KILIT_RUNBOOK.md",
    "name": "FAZ9A_TEKNIK_KILIT_RUNBOOK.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9B_DATA_GUVENLIK_RUNBOOK.md",
    "name": "FAZ9B_DATA_GUVENLIK_RUNBOOK.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9B_GECIS_MATRISI.md",
    "name": "FAZ9B_GECIS_MATRISI.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9C_DALGA_GECIS_NOTLARI.md",
    "name": "FAZ9C_DALGA_GECIS_NOTLARI.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9C_PILOT_ACILIS_RUNBOOK.md",
    "name": "FAZ9C_PILOT_ACILIS_RUNBOOK.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9C_PILOT_GERI_BILDIRIM_SABLONU.md",
    "name": "FAZ9C_PILOT_GERI_BILDIRIM_SABLONU.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9D_72SAAT_RUNBOOK.md",
    "name": "FAZ9D_72SAAT_RUNBOOK.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9D_HOTFIX_POLITIKASI.md",
    "name": "FAZ9D_HOTFIX_POLITIKASI.md",
    "suffix": ".md",
    "hits": [
      "faz",
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9D_IZLEME_MATRISI.md",
    "name": "FAZ9D_IZLEME_MATRISI.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9_CANLIYA_GECIS_RUNBOOK.md",
    "name": "FAZ9_CANLIYA_GECIS_RUNBOOK.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9_ILK_72_SAAT.md",
    "name": "FAZ9_ILK_72_SAAT.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/communication/FAZ9_ROLLBACK_CHECKLIST.md",
    "name": "FAZ9_ROLLBACK_CHECKLIST.md",
    "suffix": ".md",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER.md",
    "name": "BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER.md",
    "suffix": ".md",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/completion_phase3_visibility_scope.py",
    "name": "completion_phase3_visibility_scope.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/completion_phase4_third_manager_center.py",
    "name": "completion_phase4_third_manager_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/feedback_aftercare_phase7.py",
    "name": "feedback_aftercare_phase7.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/feedback_aftercare_phase7_person_period.py",
    "name": "feedback_aftercare_phase7_person_period.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/feedback_corporate_cleanup_phase6.py",
    "name": "feedback_corporate_cleanup_phase6.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/feedback_final_gate_phase5.py",
    "name": "feedback_final_gate_phase5.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/feedback_followup_phase4.py",
    "name": "feedback_followup_phase4.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase10_reminder_notification_center.py",
    "name": "phase10_reminder_notification_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase11_period_scope_assignment_center.py",
    "name": "phase11_period_scope_assignment_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase11_reporting_risk_policy.py",
    "name": "phase11_reporting_risk_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase12_final_readiness_policy.py",
    "name": "phase12_final_readiness_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase12_performance_final_gate_center.py",
    "name": "phase12_performance_final_gate_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase1_rule_center.py",
    "name": "phase1_rule_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase2_category_center.py",
    "name": "phase2_category_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase3_backend_route_guard.py",
    "name": "phase3_backend_route_guard.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase3_role_matrix.py",
    "name": "phase3_role_matrix.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase3_visibility_permissions.py",
    "name": "phase3_visibility_permissions.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase4_third_manager_policy.py",
    "name": "phase4_third_manager_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase5_4_status_language.py",
    "name": "phase5_4_status_language.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase5_scorecard_ui_policy.py",
    "name": "phase5_scorecard_ui_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase6_low_score_approval_policy.py",
    "name": "phase6_low_score_approval_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase6_low_score_process_center.py",
    "name": "phase6_low_score_process_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase7_scorecard_archive_center.py",
    "name": "phase7_scorecard_archive_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase7_scorecard_archive_policy.py",
    "name": "phase7_scorecard_archive_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase8_midterm_feedback_center.py",
    "name": "phase8_midterm_feedback_center.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase8_period_scope_policy.py",
    "name": "phase8_period_scope_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/phase9_reminder_policy.py",
    "name": "phase9_reminder_policy.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase10_reports.py",
    "name": "process_engine_phase10_reports.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase3_history.py",
    "name": "process_engine_phase3_history.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase4_flow.py",
    "name": "process_engine_phase4_flow.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase5_notifications.py",
    "name": "process_engine_phase5_notifications.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase6_president_approvals.py",
    "name": "process_engine_phase6_president_approvals.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase7_president_rule.py",
    "name": "process_engine_phase7_president_rule.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase8_tracking.py",
    "name": "process_engine_phase8_tracking.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/services/performance/process_engine_phase9_publish_lock.py",
    "name": "process_engine_phase9_publish_lock.py",
    "suffix": ".py",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz10.css",
    "name": "ai_decision_faz10.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz11.css",
    "name": "ai_decision_faz11.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz12.css",
    "name": "ai_decision_faz12.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz1_executive.css",
    "name": "ai_decision_faz1_executive.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz5_scorecard.css",
    "name": "ai_decision_faz5_scorecard.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz6_low_performance.css",
    "name": "ai_decision_faz6_low_performance.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz7_historical_archive.css",
    "name": "ai_decision_faz7_historical_archive.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz8_period_scope.css",
    "name": "ai_decision_faz8_period_scope.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/ai_decision_faz9_reminder.css",
    "name": "ai_decision_faz9_reminder.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/bys360_phase11_process_engine.css",
    "name": "bys360_phase11_process_engine.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/bys360_phase7_scorecard_ui_v1.css",
    "name": "bys360_phase7_scorecard_ui_v1.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase4_1.css",
    "name": "corporate_information_center_v3_0_phase4_1.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase5.css",
    "name": "corporate_information_center_v3_0_phase5.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase6.css",
    "name": "corporate_information_center_v3_0_phase6.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7.css",
    "name": "corporate_information_center_v3_0_phase7.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_4_release_pro.css",
    "name": "corporate_information_center_v3_0_phase7_4_release_pro.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_7_release_clean.css",
    "name": "corporate_information_center_v3_0_phase7_7_release_clean.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_8_base_header_pro.css",
    "name": "corporate_information_center_v3_0_phase7_8_base_header_pro.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/corporate_information_center_v3_0_phase7_9_base_clean.css",
    "name": "corporate_information_center_v3_0_phase7_9_base_clean.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/faz1_mobile_foundation.css",
    "name": "faz1_mobile_foundation.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/faz27_profile_kapak_hotfix.css",
    "name": "faz27_profile_kapak_hotfix.css",
    "suffix": ".css",
    "hits": [
      "faz",
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/faz2_performance_mobile.css",
    "name": "faz2_performance_mobile.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/faz3_communication_hr_mobile.css",
    "name": "faz3_communication_hr_mobile.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/faz4_support_account_mobile.css",
    "name": "faz4_support_account_mobile.css",
    "suffix": ".css",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/mobile_phase_m1.css",
    "name": "mobile_phase_m1.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase10_reminder.css",
    "name": "performance_completion_phase10_reminder.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase11_period_scope_assignment.css",
    "name": "performance_completion_phase11_period_scope_assignment.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase12_final_gate.css",
    "name": "performance_completion_phase12_final_gate.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase5_scorecard_ui.css",
    "name": "performance_completion_phase5_scorecard_ui.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase6_low_score_process.css",
    "name": "performance_completion_phase6_low_score_process.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase7_scorecard_archive.css",
    "name": "performance_completion_phase7_scorecard_archive.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_completion_phase8_midterm_feedback.css",
    "name": "performance_completion_phase8_midterm_feedback.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_phase3.css",
    "name": "performance_phase3.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/phase5_5_scorecard_mobile.css",
    "name": "phase5_5_scorecard_mobile.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/survey_jotform_phase1.css",
    "name": "survey_jotform_phase1.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/survey_jotform_phase2.css",
    "name": "survey_jotform_phase2.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/survey_jotform_phase3.css",
    "name": "survey_jotform_phase3.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/survey_jotform_phase4.css",
    "name": "survey_jotform_phase4.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/faz1_mobile_foundation.js",
    "name": "faz1_mobile_foundation.js",
    "suffix": ".js",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/faz2_performance_mobile.js",
    "name": "faz2_performance_mobile.js",
    "suffix": ".js",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/faz3_communication_hr_mobile.js",
    "name": "faz3_communication_hr_mobile.js",
    "suffix": ".js",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/faz4_support_account_mobile.js",
    "name": "faz4_support_account_mobile.js",
    "suffix": ".js",
    "hits": [
      "faz"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/mobile_phase_m1.js",
    "name": "mobile_phase_m1.js",
    "suffix": ".js",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/survey_builder_phase1.js",
    "name": "survey_builder_phase1.js",
    "suffix": ".js",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/survey_builder_phase2.js",
    "name": "survey_builder_phase2.js",
    "suffix": ".js",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/survey_builder_phase3.js",
    "name": "survey_builder_phase3.js",
    "suffix": ".js",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/survey_manage_phase1.js",
    "name": "survey_manage_phase1.js",
    "suffix": ".js",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/js/survey_results_phase4.js",
    "name": "survey_results_phase4.js",
    "suffix": ".js",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_01.css",
    "name": "performance_phase3_part_01.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_02.css",
    "name": "performance_phase3_part_02.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_03.css",
    "name": "performance_phase3_part_03.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_04.css",
    "name": "performance_phase3_part_04.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/css/performance_phase3_parts/performance_phase3_part_05.css",
    "name": "performance_phase3_part_05.css",
    "suffix": ".css",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  },
  {
    "path": "app/static/img/about/roadmap-phases.png",
    "name": "roadmap-phases.png",
    "suffix": ".png",
    "hits": [
      "phase"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_rename_candidate"
  }
]
```

## Cleanup Adayları İlk 200

```json
[
  {
    "path": "app/schema_guard_core_repairs.py",
    "name": "schema_guard_core_repairs.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  },
  {
    "path": "app/refactor/hotfix_merge_registry.py",
    "name": "hotfix_merge_registry.py",
    "suffix": ".py",
    "hits": [
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  },
  {
    "path": "app/services/performance/common_admin_scope_hotfix.py",
    "name": "common_admin_scope_hotfix.py",
    "suffix": ".py",
    "hits": [
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  },
  {
    "path": "app/static/css/bys360_live_full_overlay_v2_13_0.css",
    "name": "bys360_live_full_overlay_v2_13_0.css",
    "suffix": ".css",
    "hits": [
      "overlay"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  },
  {
    "path": "app/static/js/bys360_assistant_helpers_v1.js.disabled_by_p14f4",
    "name": "bys360_assistant_helpers_v1.js.disabled_by_p14f4",
    "suffix": ".disabled_by_p14f4",
    "hits": [
      "disabled"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  },
  {
    "path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "name": "bys360_live_full_overlay_v2_13_0.js",
    "suffix": ".js",
    "hits": [
      "overlay"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  },
  {
    "path": "scripts/repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
    "name": "repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/repair_bys360_portal_profile_me_link_v2_10_4.py",
    "name": "repair_bys360_portal_profile_me_link_v2_10_4.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_cic_v4_1b_force_pro_ui.py",
    "name": "repair_cic_v4_1b_force_pro_ui.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_cic_v4_2c_active_passive_hard_patch.py",
    "name": "repair_cic_v4_2c_active_passive_hard_patch.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.py",
    "name": "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase3_dispatch.py",
    "name": "repair_corporate_information_center_v3_0_phase3_dispatch.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase5_control_panel.py",
    "name": "repair_corporate_information_center_v3_0_phase5_control_panel.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase6_1_staff_noon_message.py",
    "name": "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase6_final_uat_live_ready.py",
    "name": "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
    "name": "repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    "name": "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase7_7_release_clean_ui.py",
    "name": "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
    "name": "repair_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.py",
    "name": "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_corporate_information_center_v3_0_phase7_live_release_usage.py",
    "name": "repair_corporate_information_center_v3_0_phase7_live_release_usage.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_daily_weather_mail_v1_0.py",
    "name": "repair_daily_weather_mail_v1_0.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/communication/repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
    "name": "repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py",
    "name": "repair_executive_summary_daily_mail_tasks_v1_3.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/live/check_bys360_live_full_overlay_v2_17_61.py",
    "name": "check_bys360_live_full_overlay_v2_17_61.py",
    "suffix": ".py",
    "hits": [
      "overlay"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
    "name": "repair_bys360_live_full_overlay_v2_17_60.py",
    "suffix": ".py",
    "hits": [
      "overlay",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
    "name": "repair_bys360_live_full_overlay_v2_17_61.py",
    "suffix": ".py",
    "hits": [
      "overlay",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
    "name": "repair_bys360_live_full_overlay_v2_17_62.py",
    "suffix": ".py",
    "hits": [
      "overlay",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
    "name": "bys360_live_full_overlay_v2_13_0.py",
    "suffix": ".py",
    "hits": [
      "overlay"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/performance/repair_bys360_performance_completion_phase2_category_center.py",
    "name": "repair_bys360_performance_completion_phase2_category_center.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/performance/repair_bys360_performance_completion_phase3_visibility_center.py",
    "name": "repair_bys360_performance_completion_phase3_visibility_center.py",
    "suffix": ".py",
    "hits": [
      "phase",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/portal/repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
    "name": "repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/portal/repair_bys360_portal_experience_v3b1_social_post_live.py",
    "name": "repair_bys360_portal_experience_v3b1_social_post_live.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15.py",
    "name": "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15.py",
    "suffix": ".py",
    "hits": [
      "hotfix",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_csrf_main_login_hotfix_v2_15_14.py",
    "name": "repair_bys360_csrf_main_login_hotfix_v2_15_14.py",
    "suffix": ".py",
    "hits": [
      "hotfix",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_logout_base_client_hotfix_v2_15_13.py",
    "name": "repair_bys360_logout_base_client_hotfix_v2_15_13.py",
    "suffix": ".py",
    "hits": [
      "hotfix",
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_logout_force_clear_v2_15_12.py",
    "name": "repair_bys360_logout_force_clear_v2_15_12.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
    "name": "repair_bys360_secure_release_secret_clean_v1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_2.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_3.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_4.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
    "name": "check_bys360_live_full_overlay_v2_13_0.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_60.ps1",
    "name": "check_bys360_live_full_overlay_v2_17_60.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_61.ps1",
    "name": "check_bys360_live_full_overlay_v2_17_61.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_62.ps1",
    "name": "check_bys360_live_full_overlay_v2_17_62.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/repair_bys360_live_portal_db_after_bys36043_v1.py",
    "name": "repair_bys360_live_portal_db_after_bys36043_v1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/repair_bys360_live_portal_db_after_bys36043_v1_2.py",
    "name": "repair_bys360_live_portal_db_after_bys36043_v1_2.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/repair_bys360_live_portal_db_after_bys36043_v1_3.py",
    "name": "repair_bys360_live_portal_db_after_bys36043_v1_3.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
    "name": "rollback_bys360_live_full_overlay_v2_13_0.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_17_60.ps1",
    "name": "rollback_bys360_live_full_overlay_v2_17_60.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate"
  },
  {
    "path": "migrations/versions/523a11510d7d_historical_placeholder.py",
    "name": "523a11510d7d_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "migrations/versions/71d0eccf02c0_historical_placeholder.py",
    "name": "71d0eccf02c0_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "migrations/versions/b31c7a5d9e2f_historical_placeholder.py",
    "name": "b31c7a5d9e2f_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "migrations/versions/c32f8a1e4b9d_historical_placeholder.py",
    "name": "c32f8a1e4b9d_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "migrations/versions/c4a1d9e2f731_historical_placeholder.py",
    "name": "c4a1d9e2f731_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "migrations/versions/d33a9c4e8f10_historical_placeholder.py",
    "name": "d33a9c4e8f10_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "migrations/versions/e8c3f1a9b4d0_historical_placeholder.py",
    "name": "e8c3f1a9b4d0_historical_placeholder.py",
    "suffix": ".py",
    "hits": [
      "old"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate"
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/android/app/src/debug/AndroidManifest.xml",
    "name": "AndroidManifest.xml",
    "suffix": ".xml",
    "hits": [
      "debug"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review"
  }
]
```

## Hard UI Teknik Dil Dosyaları İlk 120

```json
[
  {
    "path": "app/templates/feedback_go_live_center.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 1,
    "review_count": 6,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 223,
        "term": "endpoint",
        "sample": "{% for item in endpoint_checks %}"
      }
    ],
    "review_hits": [
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
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "app/templates/home.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 2,
    "review_count": 11,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 130,
        "term": "endpoint",
        "sample": "<a href=\"{{ safe_url_for(item.endpoint, fallback='#') }}\" class=\"home-faz1-quick-card tone-{{ item.tone }}\">"
      },
      {
        "line": 175,
        "term": "endpoint",
        "sample": "<a href=\"{{ safe_url_for(card.endpoint, fallback='#') }}\" class=\"home-faz1-op-card\">"
      }
    ],
    "review_hits": [
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
        "line": 204,
        "term": "gate",
        "sample": "{% include 'ai_decision/_final_gate_panel.html' ignore missing %}"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "app/templates/hr_attendance.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 3,
    "review_count": 13,
    "likely_false_positive_count": 0,
    "hard_hits": [
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
      }
    ],
    "review_hits": [
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
    "likely_false_positive_hits": []
  },
  {
    "path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "classification": "ui_hard_technical_language",
    "hard_count": 6,
    "review_count": 5,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 105,
        "term": "workflow",
        "sample": "[/\\bworkflow state\\b/gi, \"Süreç durumu\"],"
      },
      {
        "line": 109,
        "term": "endpoint",
        "sample": "[/\\bendpoint\\b/gi, \"bağlantı\"],"
      },
      {
        "line": 104,
        "term": "unauthorized_scope",
        "sample": "[/\\bunauthorized_scope\\b/gi, \"Bu işlem için yetkiniz bulunmamaktadır\"],"
      },
      {
        "line": 111,
        "term": "traceback",
        "sample": "[/\\btraceback\\b/gi, \"hata ayrıntısı\"],"
      },
      {
        "line": 110,
        "term": "exception",
        "sample": "[/\\bexception\\b/gi, \"işlem hatası\"],"
      },
      {
        "line": 113,
        "term": "api error",
        "sample": "[/\\bAPI error\\b/gi, \"Veriler şu anda alınamadı\"]"
      }
    ],
    "review_hits": [
      {
        "line": 106,
        "term": "phase",
        "sample": "[/\\bphase sync\\b/gi, \"Süreç eşitleme\"],"
      },
      {
        "line": 106,
        "term": "sync",
        "sample": "[/\\bphase sync\\b/gi, \"Süreç eşitleme\"],"
      },
      {
        "line": 107,
        "term": "sync",
        "sample": "[/\\bsync\\b/gi, \"eşitleme\"],"
      },
      {
        "line": 108,
        "term": "debug",
        "sample": "[/\\bdebug\\b/gi, \"kontrol\"],"
      },
      {
        "line": 112,
        "term": "json",
        "sample": "[/\\bJSON\\b/g, \"veri\"],"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "app/templates/ai_decision/_faz9_reminder_panel.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 2,
    "review_count": 9,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 2,
        "term": "faz",
        "sample": "<section class=\"ai-faz9-reminder-panel\" data-ai-reminder-endpoint=\"/ai/decision-support/performance/reminders/summary\">"
      },
      {
        "line": 2,
        "term": "endpoint",
        "sample": "<section class=\"ai-faz9-reminder-panel\" data-ai-reminder-endpoint=\"/ai/decision-support/performance/reminders/summary\">"
      }
    ],
    "review_hits": [
      {
        "line": 1,
        "term": "faz",
        "sample": "{# BYS360_AI_DECISION_FAZ9_REMINDER_PANEL #}"
      },
      {
        "line": 3,
        "term": "faz",
        "sample": "<div class=\"ai-faz9-reminder-header\">"
      },
      {
        "line": 5,
        "term": "faz",
        "sample": "<p class=\"ai-faz9-eyebrow\">Karar Destek Merkezi</p>"
      },
      {
        "line": 9,
        "term": "faz",
        "sample": "<span class=\"ai-faz9-badge\">İnsan denetimli takip</span>"
      },
      {
        "line": 12,
        "term": "faz",
        "sample": "<div class=\"ai-faz9-grid\">"
      },
      {
        "line": 15,
        "term": "faz",
        "sample": "<span>{{ ai_decision_faz9_summary.due_soon_count|default('—') }}</span>"
      },
      {
        "line": 20,
        "term": "faz",
        "sample": "<span>{{ ai_decision_faz9_summary.overdue_count|default('—') }}</span>"
      },
      {
        "line": 25,
        "term": "faz",
        "sample": "<span>{{ ai_decision_faz9_summary.critical_overdue_count|default('—') }}</span>"
      },
      {
        "line": 30,
        "term": "faz",
        "sample": "<div class=\"ai-faz9-note\">"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "app/templates/performance/feedback_corporate_cleanup_phase6.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 1,
    "review_count": 0,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 62,
        "term": "endpoint",
        "sample": "<a class=\"bys-live-btn {% if loop.first %}primary{% else %}soft{% endif %}\" href=\"{{ safe_url_for(link.endpoint) }}\"><i class=\"{{ link.icon }}\"></i> {{ link.label }}</a>"
      }
    ],
    "review_hits": [],
    "likely_false_positive_hits": []
  },
  {
    "path": "app/templates/performance/feedback_pipeline.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 3,
    "review_count": 10,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 585,
        "term": "endpoint",
        "sample": "{% if step.endpoint_ok %}"
      },
      {
        "line": 631,
        "term": "endpoint",
        "sample": "{% if step.endpoint_ok %}"
      },
      {
        "line": 633,
        "term": "endpoint",
        "sample": "href=\"{{ safe_url_for(step.endpoint) }}\""
      }
    ],
    "review_hits": [
      {
        "line": 8,
        "term": "phase",
        "sample": "{% include \"performance/_phase5_scorecard_ui_styles.html\" ignore missing %}"
      },
      {
        "line": 223,
        "term": "phase",
        "sample": ".pm-pill.phase { background: var(--cr3); color: var(--cr); }"
      },
      {
        "line": 386,
        "term": "phase",
        "sample": ".pm-state-phase {"
      },
      {
        "line": 576,
        "term": "phase",
        "sample": "{% if step.phase_label %}"
      },
      {
        "line": 577,
        "term": "phase",
        "sample": "<span class=\"pm-pill phase\" style=\"font-size:.68rem;padding:3px 8px;margin-right:6px;\">{{ step.phase_label }}</span>"
      },
      {
        "line": 689,
        "term": "phase",
        "sample": "<span class=\"pm-state-phase\">{{ sm_step.phase_label|default('P?') }}</span>"
      },
      {
        "line": 769,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_BOUND #}"
      },
      {
        "line": 770,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE11_REPORTING_RISK_BOUND #}"
      },
      {
        "line": 771,
        "term": "phase",
        "sample": "{# BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_READINESS_BOUND #}"
      },
      {
        "line": 736,
        "term": "gate",
        "sample": "<a class=\"pm-btn soft\" href=\"{{ safe_url_for('main.performance_feedback_final_gate') }}\" style=\"justify-content:flex-start;\">"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "app/templates/portal/people.html",
    "classification": "ui_hard_technical_language",
    "hard_count": 1,
    "review_count": 0,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 88,
        "term": "endpoint",
        "sample": "<!-- BYS360_PORTAL_PROFILE_ME_LINK_V2_10_3: portal_my_profile endpoint bağlantısı portal_my_profile olarak düzeltildi. -->"
      }
    ],
    "review_hits": [],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/api/mobile_real_api_contract.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 2,
    "review_count": 10,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 18,
        "term": "endpoint",
        "sample": "static const List<String> p0Endpoints = <String>["
      },
      {
        "line": 64,
        "term": "endpoint",
        "sample": "static const List<String> endpoints = <String>["
      }
    ],
    "review_hits": [
      {
        "line": 4,
        "term": "contract",
        "sample": "class MobileRealApiContract {"
      },
      {
        "line": 5,
        "term": "contract",
        "sample": "const MobileRealApiContract._();"
      },
      {
        "line": 34,
        "term": "contract",
        "sample": "// BYS360_MOBILE_V2_8_29_REAL_API_HARDENING_CONTRACT"
      },
      {
        "line": 35,
        "term": "contract",
        "sample": "class MobileRealApiHardeningContract {"
      },
      {
        "line": 36,
        "term": "contract",
        "sample": "const MobileRealApiHardeningContract._();"
      },
      {
        "line": 55,
        "term": "contract",
        "sample": "// BYS360_MOBILE_V2_8_30_PERFORMANCE_EXECUTIVE_P1_CONTRACT"
      },
      {
        "line": 56,
        "term": "contract",
        "sample": "class MobilePerformanceExecutiveP1Contract {"
      },
      {
        "line": 57,
        "term": "contract",
        "sample": "const MobilePerformanceExecutiveP1Contract._();"
      },
      {
        "line": 75,
        "term": "contract",
        "sample": "// BYS360 Mobile V2.8.31 Personnel P1 real API contract"
      },
      {
        "line": 84,
        "term": "contract",
        "sample": "// BYS360_MOBILE_V2_8_72_REFRESH_CONTRACT"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/api/support_survey_mobile_p1_contract.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 7,
    "review_count": 4,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 9,
        "term": "endpoint",
        "sample": "static const String supportTicketsEndpoint = '/api/mobile/support/tickets';"
      },
      {
        "line": 10,
        "term": "endpoint",
        "sample": "static const String supportTicketDetailEndpoint = '/api/mobile/support/tickets/{ticketId}';"
      },
      {
        "line": 11,
        "term": "endpoint",
        "sample": "static const String supportTicketCreateEndpoint = '/api/mobile/support/tickets';"
      },
      {
        "line": 12,
        "term": "endpoint",
        "sample": "static const String supportTicketReplyEndpoint = '/api/mobile/support/tickets/{ticketId}/messages';"
      },
      {
        "line": 15,
        "term": "endpoint",
        "sample": "static const String surveysEndpoint = '/api/mobile/surveys';"
      },
      {
        "line": 16,
        "term": "endpoint",
        "sample": "static const String surveyDetailEndpoint = '/api/mobile/surveys/{surveyId}';"
      },
      {
        "line": 17,
        "term": "endpoint",
        "sample": "static const String surveySubmitEndpoint = '/api/mobile/surveys/{surveyId}/submit';"
      }
    ],
    "review_hits": [
      {
        "line": 19,
        "term": "gate",
        "sample": "// Gate markerlari"
      },
      {
        "line": 5,
        "term": "contract",
        "sample": "class SupportSurveyMobileP1Contract {"
      },
      {
        "line": 32,
        "term": "contract",
        "sample": "// support_contract"
      },
      {
        "line": 35,
        "term": "contract",
        "sample": "// survey_contract"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/auth/auth_controller.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 5,
    "review_count": 4,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 4,
        "term": "exception",
        "sample": "import '../network/api_exception.dart';"
      },
      {
        "line": 18,
        "term": "exception",
        "sample": "throw const ApiException('Kullanıcı adı ve şifre zorunludur.');"
      },
      {
        "line": 27,
        "term": "exception",
        "sample": "throw const ApiException('Giriş yanıtı beklenen formatta değil.');"
      },
      {
        "line": 32,
        "term": "exception",
        "sample": "throw const ApiException('Mobil oturum anahtarı alınamadı. Lütfen tekrar deneyin.');"
      },
      {
        "line": 49,
        "term": "exception",
        "sample": "throw const ApiException('Demo ön izleme kapalı.');"
      }
    ],
    "review_hits": [
      {
        "line": 16,
        "term": "sync",
        "sample": "Future<void> login(String username, String password) async {"
      },
      {
        "line": 47,
        "term": "sync",
        "sample": "Future<void> demoLogin() async {"
      },
      {
        "line": 1,
        "term": "contract",
        "sample": "import '../api/mobile_real_api_contract.dart';"
      },
      {
        "line": 21,
        "term": "contract",
        "sample": "final payload = await _apiClient.post(MobileRealApiContract.login, {"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/bys_mobile_crash_service.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 4,
    "review_count": 4,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 37,
        "term": "sync",
        "sample": "Future<void> _store(String message, StackTrace? stack) async {"
      },
      {
        "line": 31,
        "term": "stacktrace",
        "sample": "PlatformDispatcher.instance.onError = (Object error, StackTrace stack) {"
      },
      {
        "line": 37,
        "term": "stacktrace",
        "sample": "Future<void> _store(String message, StackTrace? stack) async {"
      },
      {
        "line": 28,
        "term": "exception",
        "sample": "unawaited(_store(details.exceptionAsString(), details.stack));"
      }
    ],
    "review_hits": [
      {
        "line": 3,
        "term": "sync",
        "sample": "import 'dart:async';"
      },
      {
        "line": 20,
        "term": "sync",
        "sample": "Future<void> initialize() async {"
      },
      {
        "line": 47,
        "term": "sync",
        "sample": "Future<String?> readLastSafeMessage() async {"
      },
      {
        "line": 52,
        "term": "sync",
        "sample": "Future<void> clear() async {"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/hardening/mobile_hardening_service.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 3,
    "review_count": 1,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 17,
        "term": "exception",
        "sample": "onTimeout: () => throw TimeoutException(MobileErrorTexts.timeoutMessage),"
      },
      {
        "line": 22,
        "term": "exception",
        "sample": "if (error is TimeoutException) {"
      },
      {
        "line": 25,
        "term": "exception",
        "sample": "if (error is SocketException) {"
      }
    ],
    "review_hits": [
      {
        "line": 1,
        "term": "sync",
        "sample": "import 'dart:async';"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/network/api_client.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 8,
    "review_count": 10,
    "likely_false_positive_count": 2,
    "hard_hits": [
      {
        "line": 13,
        "term": "exception",
        "sample": "import 'api_exception.dart';"
      },
      {
        "line": 69,
        "term": "exception",
        "sample": "} on ApiException {"
      },
      {
        "line": 72,
        "term": "exception",
        "sample": "throw ApiException(_connectionMessage(error));"
      },
      {
        "line": 95,
        "term": "exception",
        "sample": "throw const ApiException(_bys360MobileCsrfFriendlyMessage, statusCode: 400);"
      },
      {
        "line": 118,
        "term": "exception",
        "sample": "throw ApiException(message, statusCode: response.statusCode);"
      },
      {
        "line": 122,
        "term": "exception",
        "sample": "throw const ApiException('Bu işlem için yetkiniz bulunmamaktadır.',"
      },
      {
        "line": 135,
        "term": "exception",
        "sample": "throw ApiException(message, statusCode: response.statusCode);"
      },
      {
        "line": 178,
        "term": "exception",
        "sample": "if (error is TimeoutException) {"
      }
    ],
    "review_hits": [
      {
        "line": 3,
        "term": "sync",
        "sample": "import 'dart:async';"
      },
      {
        "line": 26,
        "term": "sync",
        "sample": "Future<Map<String, String>> _headers({bool includeAuth = true}) async {"
      },
      {
        "line": 36,
        "term": "sync",
        "sample": "Future<dynamic> get(String path) async {"
      },
      {
        "line": 40,
        "term": "sync",
        "sample": "Future<dynamic> post(String path, Map<String, dynamic> body) async {"
      },
      {
        "line": 49,
        "term": "sync",
        "sample": "}) async {"
      },
      {
        "line": 81,
        "term": "sync",
        "sample": "}) async {"
      },
      {
        "line": 141,
        "term": "sync",
        "sample": "Future<bool> _refreshAccessToken() async {"
      },
      {
        "line": 57,
        "term": "json",
        "sample": "body: jsonEncode(body ?? <String, dynamic>{}))"
      },
      {
        "line": 99,
        "term": "json",
        "sample": "payload = jsonDecode(text);"
      },
      {
        "line": 150,
        "term": "json",
        "sample": "body: jsonEncode({'refresh_token': refreshToken}),"
      }
    ],
    "likely_false_positive_hits": [
      {
        "line": 29,
        "term": "json",
        "sample": "'Accept': 'application/json',"
      },
      {
        "line": 30,
        "term": "json",
        "sample": "'Content-Type': 'application/json; charset=utf-8',"
      }
    ]
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/network/api_exception.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 2,
    "review_count": 0,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 1,
        "term": "exception",
        "sample": "class ApiException implements Exception {"
      },
      {
        "line": 2,
        "term": "exception",
        "sample": "const ApiException(this.message, {this.statusCode});"
      }
    ],
    "review_hits": [],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 1,
    "review_count": 4,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 27,
        "term": "stacktrace",
        "sample": "'stacktrace',"
      }
    ],
    "review_hits": [
      {
        "line": 29,
        "term": "phase",
        "sample": "'phase',"
      },
      {
        "line": 30,
        "term": "sync",
        "sample": "'sync',"
      },
      {
        "line": 28,
        "term": "workflow",
        "sample": "'workflow',"
      },
      {
        "line": 24,
        "term": "json",
        "sample": "'json',"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 1,
    "review_count": 6,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 49,
        "term": "stacktrace",
        "sample": "lower.contains('stacktrace') ||"
      }
    ],
    "review_hits": [
      {
        "line": 56,
        "term": "phase",
        "sample": "lower.contains('phase') ||"
      },
      {
        "line": 57,
        "term": "sync",
        "sample": "lower.contains('sync') ||"
      },
      {
        "line": 55,
        "term": "workflow",
        "sample": "lower.contains('workflow') ||"
      },
      {
        "line": 58,
        "term": "json",
        "sample": "lower.contains('json') ||"
      },
      {
        "line": 66,
        "term": "json",
        "sample": ".replaceAll('JSON', 'veri')"
      },
      {
        "line": 67,
        "term": "json",
        "sample": ".replaceAll('json', 'veri')"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/core/widgets/bys360_logo.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 2,
    "review_count": 0,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 31,
        "term": "stacktrace",
        "sample": "errorBuilder: (context, error, stackTrace) => _LogoFallback(width: width, height: height),"
      },
      {
        "line": 70,
        "term": "stacktrace",
        "sample": "errorBuilder: (context, error, stackTrace) => Container("
      }
    ],
    "review_hits": [],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/features/auth/login_screen.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 2,
    "review_count": 2,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 5,
        "term": "exception",
        "sample": "import '../../core/network/api_exception.dart';"
      },
      {
        "line": 44,
        "term": "exception",
        "sample": "setState(() => _error = error is ApiException ? BYS360Copy.error(error.message) : BYS360Copy.error(error));"
      }
    ],
    "review_hits": [
      {
        "line": 34,
        "term": "sync",
        "sample": "Future<void> _login() async {"
      },
      {
        "line": 50,
        "term": "sync",
        "sample": "Future<void> _demoLogin() async {"
      }
    ],
    "likely_false_positive_hits": []
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scoring_form_screen.dart",
    "classification": "ui_hard_technical_language",
    "hard_count": 1,
    "review_count": 3,
    "likely_false_positive_count": 0,
    "hard_hits": [
      {
        "line": 130,
        "term": "exception",
        "sample": "return text.replaceFirst('İşlem tamamlanamadı: ', '').replaceFirst('ApiException: ', '').trim().isEmpty ? 'İşlem tamamlanamadı. Lütfen tekrar deneyin.' : text.replaceFirst('İşlem tamamlanamadı: ', '').replaceFirst('ApiException: ', '').trim"
      }
    ],
    "review_hits": [
      {
        "line": 50,
        "term": "sync",
        "sample": "Future<_ScoringFormData> _load() async {"
      },
      {
        "line": 55,
        "term": "sync",
        "sample": "Future<void> _refresh() async {"
      },
      {
        "line": 78,
        "term": "sync",
        "sample": "Future<void> _submit(_ScoringFormData form, {required bool completed}) async {"
      }
    ],
    "likely_false_positive_hits": []
  }
]
```

## Not

Bu rapor dosya silmez, taşımaz veya değiştirmez. A10C aşamasında yalnızca güvenli düzeltme planı hazırlanacaktır.