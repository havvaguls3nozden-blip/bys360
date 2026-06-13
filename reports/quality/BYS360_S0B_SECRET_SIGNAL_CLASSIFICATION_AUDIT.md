# BYS360 S0B Secret Signal Classification Audit

Tarih: 2026-06-13T09:45:01

## Sonuç

- OK: True
- Karar: S0B_SECRET_REVIEW_REQUIRED
- Source S0A OK: True
- Source S0A worktree secret term hit count: 404
- Secret signal count: 414
- High risk count: 22
- Review risk count: 334
- Compileall returncode: 0
- Pytest quality smoke returncode: 0

## Pytest Quality Smoke Summary

```json
{
  "passed": 5,
  "failed": 0,
  "errors": 0,
  "skipped": 0,
  "deselected": 0,
  "warnings": 0
}
```

## By Risk

```json
{
  "LOW": 58,
  "REVIEW": 334,
  "HIGH": 22
}
```

## By Category

```json
{
  "placeholder_or_example_assignment": 16,
  "term_reference": 334,
  "code_env_reference": 27,
  "code_or_script_assignment": 22,
  "documentation_reference": 15
}
```

## By Term

```json
{
  "DATABASE_URL": 113,
  "SECRET_KEY": 142,
  "POSTGRES_PASSWORD": 11,
  "SENTRY_DSN": 82,
  "TCKN_ENCRYPTION_KEY": 24,
  "MAIL_USERNAME": 14,
  "MAIL_PASSWORD": 12,
  "INSTAGRAM_ACCESS_TOKEN": 8,
  "DB_PASSWORD": 6,
  "FLASK_SECRET": 2
}
```

## By Path Top 80

```json
{
  "scripts/quality/bys360_secret_repo_gate.py": 26,
  "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py": 18,
  "scripts/security/validate_a6e_production_env_contract.py": 16,
  "config.py": 12,
  "scripts/quality/bys360_s0a_claude_findings_verification_audit.py": 12,
  "app/security/audit.py": 11,
  "scripts/quality/bys360_s0b_secret_signal_classification_audit.py": 10,
  "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py": 9,
  "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py": 9,
  "scripts/security/repair_bys360_secure_release_secret_clean_v1.py": 8,
  "app/security/startup_audit.py": 7,
  "app/services/config_hardening_service.py": 7,
  "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py": 7,
  "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py": 6,
  "scripts/quality/bys360_mobile_performance_response_gate_p3e.py": 6,
  "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py": 6,
  "scripts/quality/bys360_mobile_support_survey_notifications_response_gate_p3d.py": 6,
  "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py": 6,
  "app/services/settings/constants.py": 5,
  "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py": 5,
  "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py": 5,
  "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py": 5,
  "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py": 5,
  "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py": 5,
  "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py": 5,
  "scripts/security/check_bys360_p0_security_observability_v1.py": 5,
  "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py": 5,
  "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py": 5,
  "tests/integration/test_http_db_core_flows.py": 5,
  ".env.docker.example": 4,
  "tests/conftest.py": 4,
  ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py": 4,
  "app/services/corporate_information_center.py": 4,
  "app/services/security_compliance_final_gate.py": 4,
  "app/services/security_hardening_service.py": 4,
  "app/services/cic/mail_scheduler_service.py": 4,
  "scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v3.py": 4,
  "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py": 4,
  "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py": 4,
  "scripts/quality/bys360_repo_hygiene_p0_3_duplicate_tree_cleanup_v2_17_4.py": 4,
  "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py": 4,
  "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py": 4,
  ".env.production.example": 3,
  "docs/BYS360_OPS_HARDENING_V1_README.md": 3,
  ".venv_old_20260612_200915/Lib/site-packages/flask_login/utils.py": 3,
  "app/config/release_manifest.py": 3,
  "docs/architecture/BYS360_P1C_CONFIG_ENV_SMOKE_HOTFIX.md": 3,
  "scripts/quality/bys360_ci_active_architecture_gate_p2f.py": 3,
  "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py": 3,
  "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py": 3,
  "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py": 3,
  "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py": 3,
  "scripts/quality/bys360_mobile_response_suite_gate_p3f.py": 3,
  "scripts/quality/bys360_pytest_standard_gate_p2d.py": 3,
  "scripts/quality/bys360_repo_hygiene_p0_v2_17_0.py": 3,
  "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py": 3,
  "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py": 3,
  "docs/BYS360_GIT_HISTORY_SECRET_CLEANUP_NOTES.txt": 2,
  ".venv_old_20260612_200915/Lib/site-packages/flask/sansio/app.py": 2,
  "app/executive_summary/mail_engine.py": 2,
  "app/services/communication_phase9a_service.py": 2,
  "app/services/communication_phase9b_service.py": 2,
  "app/services/mail_core.py": 2,
  "app/services/mail_performance_sender.py": 2,
  "app/api/mobile/shared.py": 2,
  "app/docs/communication/FAZ9A_ENV_CHECKLIST.md": 2,
  "docs/architecture/BYS360_P1C_CONFIG_ENV_STRIP_HOTFIX_V2.md": 2,
  "docs/security/BYS360_SECRET_ROTATION_AND_HISTORY_CLEANUP_RUNBOOK.md": 2,
  "scripts/quality/bys360_android_responsive_baseline_gate_p5a.py": 2,
  "scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py": 2,
  "scripts/quality/bys360_android_responsive_inventory_precision_gate_p6c.py": 2,
  "scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py": 2,
  "scripts/quality/bys360_android_responsive_release_suite_gate_p5d_v2.py": 2,
  "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py": 2,
  "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b_v2.py": 2,
  "scripts/quality/bys360_android_responsive_visual_uat_evidence_gate_p5e.py": 2,
  "scripts/quality/bys360_mobile_release_evidence_gate_p4e.py": 2,
  "scripts/quality/bys360_mobile_security_evidence_gate_p4d.py": 2,
  "scripts/quality/bys360_mobile_security_suite_gate_p4c.py": 2,
  "scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py": 2
}
```

## High Risk Findings Top 200

```json
[
  {
    "path": "config.py",
    "line_no": 178,
    "term": "SECRET_KEY",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "9-20",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 107,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 30,
    "term": "SECRET_KEY",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 113,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 43,
    "term": "SECRET_KEY",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 51,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 99,
    "term": "SECRET_KEY",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "21-40",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/check_bys360_p0_security_observability_v1.py",
    "line_no": 116,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "21-40",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "21-40",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": true
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py",
    "line_no": 79,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py",
    "line_no": 100,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
    "line_no": 71,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "9-20",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
    "line_no": 62,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
    "line_no": 17,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
    "line_no": 169,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
    "line_no": 17,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
    "line_no": 180,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
    "line_no": 73,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
    "line_no": 135,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "line_no": 56,
    "term": "SECRET_KEY",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "21-40",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "line_no": 57,
    "term": "DATABASE_URL",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "line_no": 67,
    "term": "SENTRY_DSN",
    "category": "code_or_script_assignment",
    "risk": "HIGH",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": true,
      "length_bucket": "9-20",
      "looks_placeholder": false,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  }
]
```

## Review Findings Top 200

```json
[
  {
    "path": ".env.docker.example",
    "line_no": 39,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": true,
    "is_doc": false,
    "is_example": true,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "alembic.ini",
    "line_no": 15,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "config.py",
    "line_no": 104,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "config.py",
    "line_no": 165,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "config.py",
    "line_no": 166,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "config.py",
    "line_no": 180,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/startup_checks.py",
    "line_no": 81,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 5,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 23,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 97,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask/app.py",
    "line_no": 181,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_login/utils.py",
    "line_no": 37,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_login/utils.py",
    "line_no": 52,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_login/utils.py",
    "line_no": 410,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 31,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 38,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 72,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 87,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/form.py",
    "line_no": 42,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask/sansio/app.py",
    "line_no": 215,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/config/release_manifest.py",
    "line_no": 69,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/config/release_manifest.py",
    "line_no": 70,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/config/release_manifest.py",
    "line_no": 72,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/core/monitoring.py",
    "line_no": 36,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 36,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 37,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 40,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 45,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 105,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 109,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 119,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 126,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 136,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 45,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 54,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 56,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 80,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 81,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/communication_phase9a_service.py",
    "line_no": 77,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/communication_phase9a_service.py",
    "line_no": 78,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/communication_phase9b_service.py",
    "line_no": 177,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/communication_phase9b_service.py",
    "line_no": 247,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 105,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 106,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 107,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 111,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 118,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 133,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/corporate_information_center.py",
    "line_no": 946,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/corporate_information_center.py",
    "line_no": 947,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/corporate_information_center.py",
    "line_no": 1417,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/corporate_information_center.py",
    "line_no": 1418,
    "term": "MAIL_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/go_live_readiness_service.py",
    "line_no": 29,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/instagram_portal_sync.py",
    "line_no": 50,
    "term": "INSTAGRAM_ACCESS_TOKEN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/mail_core.py",
    "line_no": 181,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/mail_core.py",
    "line_no": 182,
    "term": "MAIL_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/mail_performance_sender.py",
    "line_no": 444,
    "term": "MAIL_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/mail_performance_sender.py",
    "line_no": 444,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "MAIL_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_hardening_service.py",
    "line_no": 50,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_hardening_service.py",
    "line_no": 281,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_hardening_service.py",
    "line_no": 286,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/security_hardening_service.py",
    "line_no": 295,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/api/mobile/shared.py",
    "line_no": 80,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/api/mobile/shared.py",
    "line_no": 380,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/ai/final_live_hardening.py",
    "line_no": 354,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/cic/mail_scheduler_service.py",
    "line_no": 140,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/cic/mail_scheduler_service.py",
    "line_no": 141,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/cic/mail_scheduler_service.py",
    "line_no": 212,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/cic/mail_scheduler_service.py",
    "line_no": 213,
    "term": "MAIL_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/performance/core_health_panel.py",
    "line_no": 137,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 18,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 20,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 23,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 25,
    "term": "MAIL_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 26,
    "term": "MAIL_USERNAME",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 94,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 95,
    "term": "POSTGRES_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 96,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 97,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 98,
    "term": "INSTAGRAM_ACCESS_TOKEN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 103,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_baseline_gate_p5a.py",
    "line_no": 233,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_baseline_gate_p5a.py",
    "line_no": 234,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py",
    "line_no": 160,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py",
    "line_no": 161,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_inventory_precision_gate_p6c.py",
    "line_no": 225,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_inventory_precision_gate_p6c.py",
    "line_no": 226,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d_v2.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d_v2.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_targeted_templates_gate_p5c.py",
    "line_no": 653,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": true,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b_v2.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b_v2.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_uat_evidence_gate_p5e.py",
    "line_no": 154,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_uat_evidence_gate_p5e.py",
    "line_no": 155,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 39,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 40,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 40,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 40,
    "term": "POSTGRES_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 41,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 41,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 41,
    "term": "INSTAGRAM_ACCESS_TOKEN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 53,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 53,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 106,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 128,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 277,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 278,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 280,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 62,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 63,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 64,
    "term": "POSTGRES_PASSWORD",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 405,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 405,
    "term": "TCKN_ENCRYPTION_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
    "line_no": 171,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
    "line_no": 173,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
    "line_no": 175,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "line_no": 125,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "line_no": 126,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "line_no": 127,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "line_no": 125,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "line_no": 126,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "line_no": 127,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "line_no": 115,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "line_no": 117,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "line_no": 118,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "line_no": 98,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "line_no": 99,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "line_no": 100,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_domain_smoke_p1f.py",
    "line_no": 131,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 139,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 140,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 253,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 254,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 255,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 140,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 141,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 159,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 160,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 161,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 222,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 223,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 224,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 140,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 141,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 159,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 160,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 161,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 228,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 229,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 230,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_pytest_contract_gate_p2a.py",
    "line_no": 279,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v2.py",
    "line_no": 280,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_release_evidence_gate_p4e.py",
    "line_no": 136,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_release_evidence_gate_p4e.py",
    "line_no": 137,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 203,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 205,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 234,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 236,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 203,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 205,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 234,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 236,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 134,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 135,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 136,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 197,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 198,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 199,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "line_no": 94,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "line_no": 95,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "line_no": 97,
    "term": "SENTRY_DSN",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "line_no": 93,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "line_no": 94,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "line_no": 95,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
    "line_no": 95,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
    "line_no": 96,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
    "line_no": 97,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "line_no": 95,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "line_no": 96,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "line_no": 97,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_evidence_gate_p4d.py",
    "line_no": 137,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_evidence_gate_p4d.py",
    "line_no": 138,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_suite_gate_p4c.py",
    "line_no": 226,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_suite_gate_p4c.py",
    "line_no": 227,
    "term": "SECRET_KEY",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py",
    "line_no": 220,
    "term": "DATABASE_URL",
    "category": "term_reference",
    "risk": "REVIEW",
    "is_env_file": false,
    "is_doc": false,
    "is_example": false,
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": true,
      "looks_url": false,
      "looks_secretish": false
    },
    "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi."
  }
]
```

## Sonraki Adım

HIGH varsa S0B2: değer göstermeden dosya bazlı secret risk kararı ve rotate listesi hazırlanmalı; HIGH yoksa S0C config.py bug fix yapılmalı.