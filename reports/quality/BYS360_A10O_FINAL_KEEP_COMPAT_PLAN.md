# BYS360 A10O Final Keep / Compat Plan

Tarih: 2026-06-12T19:49:26

## Sonuç

- OK: True
- Karar: A10O_FINAL_KEEP_COMPAT_PLAN_GREEN
- A10N OK: True
- Compileall returncode: 0
- Pytest returncode: 0
- A10F safe quarantine candidate count: 0
- A10F cleanup candidate count: 59
- A10I remaining count: 59
- A10K remaining low risk count: 7
- Compat required count: 7
- Referenced keep count: 45
- Historical placeholder keep count: 7
- Non-placeholder low risk count: 0
- Unclassified count: 0

## Refresh Returncodes

```json
{
  "a10a": 0,
  "a10b": 0,
  "a10f": 0,
  "a10i": 0,
  "a10k": 0
}
```

## Compat Required

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
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 2,
    "references_sample": [
      {
        "path": "app/schema_guard.py",
        "hit_terms": [
          "app.schema_guard_core_repairs",
          "schema_guard_core_repairs.py",
          "schema_guard_core_repairs"
        ]
      },
      {
        "path": "app/schema_guard_engine.py",
        "hit_terms": [
          "app.schema_guard_core_repairs",
          "schema_guard_core_repairs"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 2,
    "references_now_sample": [
      {
        "path": "app/schema_guard.py",
        "hit_terms": [
          "app.schema_guard_core_repairs",
          "schema_guard_core_repairs.py",
          "schema_guard_core_repairs"
        ]
      },
      {
        "path": "app/schema_guard_engine.py",
        "hit_terms": [
          "app.schema_guard_core_repairs",
          "schema_guard_core_repairs"
        ]
      }
    ],
    "suggested_new_path": "app/schema_guard_core_maintenances.py",
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "app/refactor/hotfix_merge_registry.py",
    "name": "hotfix_merge_registry.py",
    "suffix": ".py",
    "hits": [
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "app/refactor/faz1f_family_targets.py",
        "hit_terms": [
          "app/refactor/hotfix_merge_registry.py",
          "hotfix_merge_registry.py",
          "hotfix_merge_registry"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "app/refactor/faz1f_family_targets.py",
        "hit_terms": [
          "app/refactor/hotfix_merge_registry.py",
          "hotfix_merge_registry.py",
          "hotfix_merge_registry"
        ]
      }
    ],
    "suggested_new_path": "app/refactor/maintenance_merge_registry.py",
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "app/services/performance/common_admin_scope_hotfix.py",
    "name": "common_admin_scope_hotfix.py",
    "suffix": ".py",
    "hits": [
      "hotfix"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 2,
    "references_sample": [
      {
        "path": "app/refactor/faz1e_deletion_allowlist.py",
        "hit_terms": [
          "app/services/performance/common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix"
        ]
      },
      {
        "path": "app/refactor/hotfix_merge_registry.py",
        "hit_terms": [
          "app/services/performance/common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 2,
    "references_now_sample": [
      {
        "path": "app/refactor/faz1e_deletion_allowlist.py",
        "hit_terms": [
          "app/services/performance/common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix"
        ]
      },
      {
        "path": "app/refactor/hotfix_merge_registry.py",
        "hit_terms": [
          "app/services/performance/common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix.py",
          "common_admin_scope_hotfix"
        ]
      }
    ],
    "suggested_new_path": "app/services/performance/common_admin_scope_maintenance.py",
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "app/static/css/bys360_live_full_overlay_v2_13_0.css",
    "name": "bys360_live_full_overlay_v2_13_0.css",
    "suffix": ".css",
    "hits": [
      "overlay"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "app/static/css/bys360_live_full_overlay_v2_13_0.css",
          "bys360_live_full_overlay_v2_13_0.css",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/quality/bys360_a10d_hard_ui_precision_decision.py",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "app/static/css/bys360_live_full_overlay_v2_13_0.css",
          "bys360_live_full_overlay_v2_13_0.css",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/quality/bys360_a10d_hard_ui_precision_decision.py",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "app/static/js/bys360_assistant_helpers_v1.js.disabled_by_p14f4",
    "name": "bys360_assistant_helpers_v1.js.disabled_by_p14f4",
    "suffix": ".disabled_by_p14f4",
    "hits": [
      "disabled"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 6,
    "references_sample": [
      {
        "path": "scripts/quality/analyze_p14_c_assistant_js_helper_split_dryrun_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/analyze_p14_f_assistant_js_split_verification_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/apply_p14_e_assistant_js_helper_split_apply_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/check_p14f4_source_aware_existing_assistant_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/restore_p14f4_source_aware_existing_assistant_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 6,
    "references_now_sample": [
      {
        "path": "scripts/quality/analyze_p14_c_assistant_js_helper_split_dryrun_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/analyze_p14_f_assistant_js_split_verification_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/apply_p14_e_assistant_js_helper_split_apply_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/check_p14f4_source_aware_existing_assistant_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      },
      {
        "path": "scripts/quality/restore_p14f4_source_aware_existing_assistant_v1.py",
        "hit_terms": [
          "bys360_assistant_helpers_v1.js"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "name": "bys360_live_full_overlay_v2_13_0.js",
    "suffix": ".js",
    "hits": [
      "overlay"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "app/static/js/bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/quality/bys360_a10d_hard_ui_precision_decision.py",
        "hit_terms": [
          "app/static/js/bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "app/static/js/bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/quality/bys360_a10d_hard_ui_precision_decision.py",
        "hit_terms": [
          "app/static/js/bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0.js",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "mobile_flutter/bys360_mobile_native/android/app/src/debug/AndroidManifest.xml",
    "name": "AndroidManifest.xml",
    "suffix": ".xml",
    "hits": [
      "debug"
    ],
    "classification": "app_user_or_runtime_review",
    "a10b_classification": "runtime_cleanup_review",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/bys360_mobile_v2_8_73_quality_router_fcm_tests.py",
        "hit_terms": [
          "AndroidManifest.xml",
          "AndroidManifest"
        ]
      }
    ],
    "a10f_decision": "runtime_keep_rename_later",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/bys360_mobile_v2_8_73_quality_router_fcm_tests.py",
        "hit_terms": [
          "AndroidManifest.xml",
          "AndroidManifest"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "rename_requires_compat_wrapper_and_import_update",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  }
]
```

## Referenced Keep İlk 120

```json
[
  {
    "path": "scripts/repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
    "name": "repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/check_bys360_compileall_legacy_script_syntax_v2_13_3.py",
        "hit_terms": [
          "scripts/repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
          "repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
          "repair_bys360_portal_delete_route_dedupe_v2_10_1"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/check_bys360_compileall_legacy_script_syntax_v2_13_3.py",
        "hit_terms": [
          "scripts/repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
          "repair_bys360_portal_delete_route_dedupe_v2_10_1.py",
          "repair_bys360_portal_delete_route_dedupe_v2_10_1"
        ]
      }
    ],
    "suggested_new_path": "scripts/maintenance_bys360_portal_delete_route_dedupe_v2_10_1.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/repair_bys360_portal_profile_me_link_v2_10_4.py",
    "name": "repair_bys360_portal_profile_me_link_v2_10_4.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/check_bys360_compileall_legacy_script_syntax_v2_13_3.py",
        "hit_terms": [
          "scripts/repair_bys360_portal_profile_me_link_v2_10_4.py",
          "repair_bys360_portal_profile_me_link_v2_10_4.py",
          "repair_bys360_portal_profile_me_link_v2_10_4"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/check_bys360_compileall_legacy_script_syntax_v2_13_3.py",
        "hit_terms": [
          "scripts/repair_bys360_portal_profile_me_link_v2_10_4.py",
          "repair_bys360_portal_profile_me_link_v2_10_4.py",
          "repair_bys360_portal_profile_me_link_v2_10_4"
        ]
      }
    ],
    "suggested_new_path": "scripts/maintenance_bys360_portal_profile_me_link_v2_10_4.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/communication/repair_cic_v4_1b_force_pro_ui.py",
    "name": "repair_cic_v4_1b_force_pro_ui.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_cic_v4_1b_force_pro_ui.py",
        "hit_terms": [
          "scripts/communication/repair_cic_v4_1b_force_pro_ui.py",
          "repair_cic_v4_1b_force_pro_ui.py",
          "repair_cic_v4_1b_force_pro_ui"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_cic_v4_1b_force_pro_ui.py",
        "hit_terms": [
          "scripts/communication/repair_cic_v4_1b_force_pro_ui.py",
          "repair_cic_v4_1b_force_pro_ui.py",
          "repair_cic_v4_1b_force_pro_ui"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_cic_v4_1b_force_pro_ui.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/communication/repair_cic_v4_2c_active_passive_hard_patch.py",
    "name": "repair_cic_v4_2c_active_passive_hard_patch.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_cic_v4_2d_active_passive_syntax_fix.py",
        "hit_terms": [
          "repair_cic_v4_2c_active_passive_hard_patch.py",
          "repair_cic_v4_2c_active_passive_hard_patch"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_cic_v4_2d_active_passive_syntax_fix.py",
        "hit_terms": [
          "repair_cic_v4_2c_active_passive_hard_patch.py",
          "repair_cic_v4_2c_active_passive_hard_patch"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_cic_v4_2c_active_passive_hard_patch.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 5,
    "references_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase2_3.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.py",
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 5,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase2_3.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.py",
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module2_3_csrf_recipient_ux.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase3_dispatch"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module3_dispatch.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase5_control_panel"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module5_control_panel.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 5,
    "references_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase6_1_staff_noon_message.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 5,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase6_1_staff_noon_message.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_1_staff_noon_message"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module6_1_staff_noon_message.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase6_final_uat_live_ready"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module6_final_uat_live_ready.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
          "repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py",
          "repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module7_3_flat_css_link_fix.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
          "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
          "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module7_6_quality_script_maintenance.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_7_release_clean_ui"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module7_7_release_clean_ui.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 5,
    "references_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 5,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro.py",
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_8_base_header_pro"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module7_8_base_header_pro.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module7_9_base_real_newlines_fix.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_corporate_information_center_v3_0_phase7_live_release_usage"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_corporate_information_center_v3_0_module7_live_release_usage.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/communication/repair_daily_weather_mail_v1_0.py",
    "name": "repair_daily_weather_mail_v1_0.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_daily_weather_mail_v1_0_5.py",
        "hit_terms": [
          "repair_daily_weather_mail_v1_0"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_daily_weather_mail_v1_0_5.py",
        "hit_terms": [
          "repair_daily_weather_mail_v1_0"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_daily_weather_mail_v1_0.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/communication/repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
    "name": "repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_daily_weather_mail_v1_0_5.py",
        "hit_terms": [
          "scripts/communication/repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
          "repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
          "repair_daily_weather_mail_v1_0_5_premium_exec_menu"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_daily_weather_mail_v1_0_5.py",
        "hit_terms": [
          "scripts/communication/repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
          "repair_daily_weather_mail_v1_0_5_premium_exec_menu.py",
          "repair_daily_weather_mail_v1_0_5_premium_exec_menu"
        ]
      }
    ],
    "suggested_new_path": "scripts/communication/maintenance_daily_weather_mail_v1_0_5_premium_exec_menu.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py",
    "name": "repair_executive_summary_daily_mail_tasks_v1_3.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_executive_summary_daily_mail_tasks_v1_3.py",
        "hit_terms": [
          "scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py",
          "repair_executive_summary_daily_mail_tasks_v1_3.py",
          "repair_executive_summary_daily_mail_tasks_v1_3"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_executive_summary_daily_mail_tasks_v1_3.py",
        "hit_terms": [
          "scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py",
          "repair_executive_summary_daily_mail_tasks_v1_3.py",
          "repair_executive_summary_daily_mail_tasks_v1_3"
        ]
      }
    ],
    "suggested_new_path": "scripts/executive/maintenance_executive_summary_daily_mail_tasks_v1_3.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/live/check_bys360_live_full_overlay_v2_17_61.py",
    "name": "check_bys360_live_full_overlay_v2_17_61.py",
    "suffix": ".py",
    "hits": [
      "overlay"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 2,
    "references_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_61.py",
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_61.ps1",
        "hit_terms": [
          "scripts\\live\\check_bys360_live_full_overlay_v2_17_61.py",
          "check_bys360_live_full_overlay_v2_17_61.py",
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 2,
    "references_now_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_61.py",
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_61.ps1",
        "hit_terms": [
          "scripts\\live\\check_bys360_live_full_overlay_v2_17_61.py",
          "check_bys360_live_full_overlay_v2_17_61.py",
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 2,
    "references_sample": [
      {
        "path": "scripts/quality/check_bys360_live_full_overlay_v2_17_60.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_17_60.ps1",
        "hit_terms": [
          "scripts\\live\\repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 2,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_bys360_live_full_overlay_v2_17_60.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_17_60.ps1",
        "hit_terms": [
          "scripts\\live\\repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60.py",
          "repair_bys360_live_full_overlay_v2_17_60"
        ]
      }
    ],
    "suggested_new_path": "scripts/live/maintenance_bys360_live_full_overlay_v2_17_60.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 3,
    "references_sample": [
      {
        "path": "scripts/live/check_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/quality/check_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 3,
    "references_now_sample": [
      {
        "path": "scripts/live/check_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/quality/check_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61.py",
          "repair_bys360_live_full_overlay_v2_17_61"
        ]
      }
    ],
    "suggested_new_path": "scripts/live/maintenance_bys360_live_full_overlay_v2_17_61.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/quality/check_bys360_live_full_overlay_v2_17_62.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
          "repair_bys360_live_full_overlay_v2_17_62.py",
          "repair_bys360_live_full_overlay_v2_17_62"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/quality/check_bys360_live_full_overlay_v2_17_62.py",
        "hit_terms": [
          "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
          "repair_bys360_live_full_overlay_v2_17_62.py",
          "repair_bys360_live_full_overlay_v2_17_62"
        ]
      }
    ],
    "suggested_new_path": "scripts/live/maintenance_bys360_live_full_overlay_v2_17_62.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
    "name": "bys360_live_full_overlay_v2_13_0.py",
    "suffix": ".py",
    "hits": [
      "overlay"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 3,
    "references_sample": [
      {
        "path": "scripts/quality/bys360_a10d_hard_ui_precision_decision.py",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "scripts\\overlay\\bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "scripts\\overlay\\bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 3,
    "references_now_sample": [
      {
        "path": "scripts/quality/bys360_a10d_hard_ui_precision_decision.py",
        "hit_terms": [
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "scripts\\overlay\\bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0"
        ]
      },
      {
        "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
        "hit_terms": [
          "scripts\\overlay\\bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0.py",
          "bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER.md",
        "hit_terms": [
          "scripts/performance/repair_bys360_performance_completion_phase2_category_center.py",
          "repair_bys360_performance_completion_phase2_category_center.py",
          "repair_bys360_performance_completion_phase2_category_center"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER.md",
        "hit_terms": [
          "scripts/performance/repair_bys360_performance_completion_phase2_category_center.py",
          "repair_bys360_performance_completion_phase2_category_center.py",
          "repair_bys360_performance_completion_phase2_category_center"
        ]
      }
    ],
    "suggested_new_path": "scripts/performance/maintenance_bys360_performance_completion_module2_category_center.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER.md",
        "hit_terms": [
          "scripts/performance/repair_bys360_performance_completion_phase3_visibility_center.py",
          "repair_bys360_performance_completion_phase3_visibility_center.py",
          "repair_bys360_performance_completion_phase3_visibility_center"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "app/docs/performance/BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER.md",
        "hit_terms": [
          "scripts/performance/repair_bys360_performance_completion_phase3_visibility_center.py",
          "repair_bys360_performance_completion_phase3_visibility_center.py",
          "repair_bys360_performance_completion_phase3_visibility_center"
        ]
      }
    ],
    "suggested_new_path": "scripts/performance/maintenance_bys360_performance_completion_module3_visibility_center.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/portal/repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
    "name": "repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py",
        "hit_terms": [
          "scripts/portal/repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
          "repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
          "repair_bys360_portal_experience_v3a1_press_news_sidebar"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py",
        "hit_terms": [
          "scripts/portal/repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
          "repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
          "repair_bys360_portal_experience_v3a1_press_news_sidebar"
        ]
      }
    ],
    "suggested_new_path": "scripts/portal/maintenance_bys360_portal_experience_v3a1_press_news_sidebar.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/portal/repair_bys360_portal_experience_v3b1_social_post_live.py",
    "name": "repair_bys360_portal_experience_v3b1_social_post_live.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py",
        "hit_terms": [
          "scripts/portal/repair_bys360_portal_experience_v3b1_social_post_live.py",
          "repair_bys360_portal_experience_v3b1_social_post_live.py",
          "repair_bys360_portal_experience_v3b1_social_post_live"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py",
        "hit_terms": [
          "scripts/portal/repair_bys360_portal_experience_v3b1_social_post_live.py",
          "repair_bys360_portal_experience_v3b1_social_post_live.py",
          "repair_bys360_portal_experience_v3b1_social_post_live"
        ]
      }
    ],
    "suggested_new_path": "scripts/portal/maintenance_bys360_portal_experience_v3b1_social_post_live.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_csrf_form_token_and_referrer_maintenance_v2_15_15.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_csrf_main_login_hotfix_v2_15_14"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_csrf_main_login_maintenance_v2_15_14.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
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
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_logout_base_client_hotfix_v2_15_13"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_logout_base_client_maintenance_v2_15_13.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/security/repair_bys360_logout_force_clear_v2_15_12.py",
    "name": "repair_bys360_logout_force_clear_v2_15_12.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 4,
    "references_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 4,
    "references_now_sample": [
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v2.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v3.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      },
      {
        "path": "scripts/windows/apply_bys360_cic_v3_0_live_final_release_resume_v4.ps1",
        "hit_terms": [
          "repair_bys360_logout_force_clear_v2_15_12"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_logout_force_clear_v2_15_12.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
    "name": "repair_bys360_secure_release_secret_clean_v1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 7,
    "references_sample": [
      {
        "path": "scripts/security/build_bys360_secure_release_v1_4.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_5.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 7,
    "references_now_sample": [
      {
        "path": "scripts/security/build_bys360_secure_release_v1_4.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_5.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      },
      {
        "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_secure_release_secret_clean_v1.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1_1"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1_1"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_secure_release_secret_clean_v1_1.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_2.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1_2"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1_2"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_secure_release_secret_clean_v1_2.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_3.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
          "repair_bys360_secure_release_secret_clean_v1_3.py",
          "repair_bys360_secure_release_secret_clean_v1_3"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "hit_terms": [
          "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
          "repair_bys360_secure_release_secret_clean_v1_3.py",
          "repair_bys360_secure_release_secret_clean_v1_3"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_secure_release_secret_clean_v1_3.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "name": "repair_bys360_secure_release_secret_clean_v1_4.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "general_review",
    "a10b_classification": "cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/security/build_bys360_secure_release_v1_4.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1_4"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/security/build_bys360_secure_release_v1_4.py",
        "hit_terms": [
          "repair_bys360_secure_release_secret_clean_v1_4"
        ]
      }
    ],
    "suggested_new_path": "scripts/security/maintenance_bys360_secure_release_secret_clean_v1_4.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_13_0.ps1",
    "name": "check_bys360_live_full_overlay_v2_13_0.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "scripts\\windows\\check_bys360_live_full_overlay_v2_13_0.ps1",
          "check_bys360_live_full_overlay_v2_13_0.ps1",
          "check_bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "scripts\\windows\\check_bys360_live_full_overlay_v2_13_0.ps1",
          "check_bys360_live_full_overlay_v2_13_0.ps1",
          "check_bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_60.ps1",
    "name": "check_bys360_live_full_overlay_v2_17_60.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_60.ps1",
          "check_bys360_live_full_overlay_v2_17_60"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_60.ps1",
          "check_bys360_live_full_overlay_v2_17_60"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_61.ps1",
    "name": "check_bys360_live_full_overlay_v2_17_61.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 2,
    "references_sample": [
      {
        "path": "scripts/live/check_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_61.ps1",
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 2,
    "references_now_sample": [
      {
        "path": "scripts/live/check_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      },
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_61.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_61.ps1",
          "check_bys360_live_full_overlay_v2_17_61"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/check_bys360_live_full_overlay_v2_17_62.ps1",
    "name": "check_bys360_live_full_overlay_v2_17_62.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_62.ps1",
          "check_bys360_live_full_overlay_v2_17_62"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py",
        "hit_terms": [
          "check_bys360_live_full_overlay_v2_17_62.ps1",
          "check_bys360_live_full_overlay_v2_17_62"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/repair_bys360_live_portal_db_after_bys36043_v1.py",
    "name": "repair_bys360_live_portal_db_after_bys36043_v1.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 3,
    "references_sample": [
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1.ps1",
        "hit_terms": [
          "scripts\\windows\\repair_bys360_live_portal_db_after_bys36043_v1.py",
          "repair_bys360_live_portal_db_after_bys36043_v1.py",
          "repair_bys360_live_portal_db_after_bys36043_v1"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_2.ps1",
        "hit_terms": [
          "repair_bys360_live_portal_db_after_bys36043_v1"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_3.ps1",
        "hit_terms": [
          "repair_bys360_live_portal_db_after_bys36043_v1"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 3,
    "references_now_sample": [
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1.ps1",
        "hit_terms": [
          "scripts\\windows\\repair_bys360_live_portal_db_after_bys36043_v1.py",
          "repair_bys360_live_portal_db_after_bys36043_v1.py",
          "repair_bys360_live_portal_db_after_bys36043_v1"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_2.ps1",
        "hit_terms": [
          "repair_bys360_live_portal_db_after_bys36043_v1"
        ]
      },
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_3.ps1",
        "hit_terms": [
          "repair_bys360_live_portal_db_after_bys36043_v1"
        ]
      }
    ],
    "suggested_new_path": "scripts/windows/maintenance_bys360_live_portal_db_after_bys36043_v1.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/repair_bys360_live_portal_db_after_bys36043_v1_2.py",
    "name": "repair_bys360_live_portal_db_after_bys36043_v1_2.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_2.ps1",
        "hit_terms": [
          "scripts\\windows\\repair_bys360_live_portal_db_after_bys36043_v1_2.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_2.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_2"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_2.ps1",
        "hit_terms": [
          "scripts\\windows\\repair_bys360_live_portal_db_after_bys36043_v1_2.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_2.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_2"
        ]
      }
    ],
    "suggested_new_path": "scripts/windows/maintenance_bys360_live_portal_db_after_bys36043_v1_2.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/repair_bys360_live_portal_db_after_bys36043_v1_3.py",
    "name": "repair_bys360_live_portal_db_after_bys36043_v1_3.py",
    "suffix": ".py",
    "hits": [
      "repair"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_3.ps1",
        "hit_terms": [
          "scripts\\windows\\repair_bys360_live_portal_db_after_bys36043_v1_3.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_3.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_3"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/windows/check_bys360_live_portal_db_after_bys36043_v1_3.ps1",
        "hit_terms": [
          "scripts\\windows\\repair_bys360_live_portal_db_after_bys36043_v1_3.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_3.py",
          "repair_bys360_live_portal_db_after_bys36043_v1_3"
        ]
      }
    ],
    "suggested_new_path": "scripts/windows/maintenance_bys360_live_portal_db_after_bys36043_v1_3.py",
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_13_0.ps1",
    "name": "rollback_bys360_live_full_overlay_v2_13_0.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "scripts\\windows\\rollback_bys360_live_full_overlay_v2_13_0.ps1",
          "rollback_bys360_live_full_overlay_v2_13_0.ps1",
          "rollback_bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/overlay/bys360_live_full_overlay_v2_13_0.py",
        "hit_terms": [
          "scripts\\windows\\rollback_bys360_live_full_overlay_v2_13_0.ps1",
          "rollback_bys360_live_full_overlay_v2_13_0.ps1",
          "rollback_bys360_live_full_overlay_v2_13_0"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  },
  {
    "path": "scripts/windows/rollback_bys360_live_full_overlay_v2_17_60.ps1",
    "name": "rollback_bys360_live_full_overlay_v2_17_60.ps1",
    "suffix": ".ps1",
    "hits": [
      "overlay"
    ],
    "classification": "windows_script_review",
    "a10b_classification": "windows_legacy_script_cleanup_candidate",
    "reference_count": 1,
    "references_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
        "hit_terms": [
          "rollback_bys360_live_full_overlay_v2_17_60.ps1",
          "rollback_bys360_live_full_overlay_v2_17_60"
        ]
      }
    ],
    "a10f_decision": "referenced_keep_review",
    "reference_count_now": 1,
    "references_now_sample": [
      {
        "path": "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py",
        "hit_terms": [
          "rollback_bys360_live_full_overlay_v2_17_60.ps1",
          "rollback_bys360_live_full_overlay_v2_17_60"
        ]
      }
    ],
    "suggested_new_path": null,
    "a10i_decision": "keep_referenced_do_not_rename_now",
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek."
  }
]
```

## Historical Placeholder Keep

```json
[
  {
    "path": "migrations/versions/523a11510d7d_historical_placeholder.py",
    "name": "523a11510d7d_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/523a11510d7d_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/71d0eccf02c0_historical_placeholder.py",
    "name": "71d0eccf02c0_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/71d0eccf02c0_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/b31c7a5d9e2f_historical_placeholder.py",
    "name": "b31c7a5d9e2f_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/b31c7a5d9e2f_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/c32f8a1e4b9d_historical_placeholder.py",
    "name": "c32f8a1e4b9d_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/c32f8a1e4b9d_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/c4a1d9e2f731_historical_placeholder.py",
    "name": "c4a1d9e2f731_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/c4a1d9e2f731_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/d33a9c4e8f10_historical_placeholder.py",
    "name": "d33a9c4e8f10_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/d33a9c4e8f10_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  },
  {
    "path": "migrations/versions/e8c3f1a9b4d0_historical_placeholder.py",
    "name": "e8c3f1a9b4d0_historical_placeholder.py",
    "hits": [
      "old"
    ],
    "reference_count_now": 0,
    "existing_suggested_new_path": null,
    "custom_suggested_new_path": "migrations/versions/e8c3f1a9b4d0_historical_placeharchiveer.py",
    "a10k_decision": "rename_with_custom_suggestion",
    "reason": "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
  }
]
```

## Pytest Özeti

```json
{
  "warnings": 32,
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## Sonraki Adım

A10P: compat_required listesindeki 7 dosya için wrapper/import-update planı hazırlanmalı; referenced_keep ve historical_placeholder dosyaları keep allowlist olarak korunmalı.