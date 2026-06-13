# BYS360 A10P Compat Wrapper Rename Plan

Tarih: 2026-06-12T19:52:34

## Sonuç

- OK: True
- Karar: A10P_COMPAT_WRAPPER_RENAME_PLAN_GREEN
- A10O OK: True
- Compat required count: 7
- Apply candidate count: 3
- Keep allowlist count: 4
- Compileall returncode: 0
- Pytest returncode: 0

## Karar Dağılımı

```json
{
  "python_compat_wrapper_candidate": 3,
  "keep_allowlist_referenced_static_asset": 2,
  "keep_allowlist_archived_disabled_asset": 1,
  "keep_allowlist_manual_reason_required": 1
}
```

## Apply Candidates

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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "python_compat_wrapper_candidate",
    "apply_allowed": true,
    "reason": "Python runtime dosyası. Yeni ad oluşturulabilir; eski path için compatibility wrapper bırakılarak import kırılması önlenebilir.",
    "old_path": "app/schema_guard_core_repairs.py",
    "new_path": "app/schema_guard_core_maintenances.py"
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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "python_compat_wrapper_candidate",
    "apply_allowed": true,
    "reason": "Python runtime dosyası. Yeni ad oluşturulabilir; eski path için compatibility wrapper bırakılarak import kırılması önlenebilir.",
    "old_path": "app/refactor/hotfix_merge_registry.py",
    "new_path": "app/refactor/maintenance_merge_registry.py"
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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "python_compat_wrapper_candidate",
    "apply_allowed": true,
    "reason": "Python runtime dosyası. Yeni ad oluşturulabilir; eski path için compatibility wrapper bırakılarak import kırılması önlenebilir.",
    "old_path": "app/services/performance/common_admin_scope_hotfix.py",
    "new_path": "app/services/performance/common_admin_scope_maintenance.py"
  }
]
```

## Keep Allowlist

```json
[
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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "keep_allowlist_referenced_static_asset",
    "apply_allowed": false,
    "reason": "Static CSS/JS dosyası referanslı asset olarak görünüyor. Cache/template/rollback bağı olabileceği için rename yerine keep allowlist daha güvenli.",
    "old_path": "app/static/css/bys360_live_full_overlay_v2_13_0.css",
    "new_path": null
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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "keep_allowlist_archived_disabled_asset",
    "apply_allowed": false,
    "reason": "Devre dışı bırakılmış/arsiv nitelikli dosya; referanslar kalite/restore scriptlerinden geliyor. Rename yapmak yerine keep allowlist daha güvenli.",
    "old_path": "app/static/js/bys360_assistant_helpers_v1.js.disabled_by_p14f4",
    "new_path": null
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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "keep_allowlist_referenced_static_asset",
    "apply_allowed": false,
    "reason": "Static CSS/JS dosyası referanslı asset olarak görünüyor. Cache/template/rollback bağı olabileceği için rename yerine keep allowlist daha güvenli.",
    "old_path": "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "new_path": null
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
    "risk_note": "Bu dosya çalışan runtime veya referans alan dosya olabilir; doğrudan taşınmayacak/silinmeyecek.",
    "a10p_decision": "keep_allowlist_manual_reason_required",
    "apply_allowed": false,
    "reason": "Güvenli otomatik wrapper/rename için yeterli koşul oluşmadı. Keep allowlist veya manuel karar gerekir.",
    "old_path": "mobile_flutter/bys360_mobile_native/android/app/src/debug/AndroidManifest.xml",
    "new_path": null
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

A10Q: apply_candidates listesindeki Python dosyaları için yedekli rename + eski path wrapper uygulanabilir. Keep allowlist dosyaları rename edilmeyecek.