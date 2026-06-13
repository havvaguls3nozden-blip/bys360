# BYS360 S0C2 config.py SECRET_KEY ve exc Final Evidence

Tarih: 2026-06-13T09:57:10

## Sonuç

- OK: True
- Karar: S0C2_GREEN
- Compileall returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0
- Exc bug likely after patch: False
- SECRET_KEY high risk count: 0
- Repo normalized high count: 0

## Exc Scan

```json
{
  "exc_info_exc_line_count": 1,
  "exc_bug_likely_after_patch": false,
  "findings": [
    {
      "line_no": 149,
      "plain_except_nearby": false,
      "except_exception_as_exc_nearby": true,
      "bug_likely": false
    }
  ]
}
```

## SECRET_KEY Scan

```json
{
  "secret_key_block_count": 2,
  "secret_key_high_risk_count": 0,
  "secret_key_blocks": [
    {
      "line_no": 178,
      "decision": "ENV_CENTERED_WITH_LOCAL_DEV_ONLY_FALLBACK",
      "normalized_risk": "LOW",
      "has_env_secret": true,
      "has_env_flask_secret": true,
      "has_prod_guard": true,
      "has_local_dev_fallback": true,
      "note": "Blok içeriği/değer rapora yazılmadı; yalnızca güvenli şekil bilgisi tutuldu."
    },
    {
      "line_no": 191,
      "decision": "ENV_CENTERED_WITH_LOCAL_DEV_ONLY_FALLBACK",
      "normalized_risk": "LOW",
      "has_env_secret": true,
      "has_env_flask_secret": true,
      "has_prod_guard": true,
      "has_local_dev_fallback": true,
      "note": "Blok içeriği/değer rapora yazılmadı; yalnızca güvenli şekil bilgisi tutuldu."
    }
  ]
}
```

## Repo Secret Scan

```json
{
  "classified_signal_count": 471,
  "normalized_high_count": 0,
  "normalized_review_count": 159,
  "by_risk": {
    "REVIEW": 159,
    "LOW": 312
  },
  "by_decision": {
    "REFERENCE_REVIEW": 34,
    "EXAMPLE_OR_TEMPLATE": 9,
    "ENV_LOOKUP_REFERENCE": 48,
    "DOC_REFERENCE": 17,
    "TEST_REFERENCE": 4,
    "SCHEMA_OR_GUARDRAIL_REFERENCE": 238,
    "AUDIT_OR_TOOLING_REFERENCE": 121
  },
  "by_term": {
    "DATABASE_URL": 114,
    "SECRET_KEY": 166,
    "POSTGRES_PASSWORD": 13,
    "SENTRY_DSN": 83,
    "FLASK_SECRET": 21,
    "TCKN_ENCRYPTION_KEY": 26,
    "MAIL_USERNAME": 16,
    "MAIL_PASSWORD": 14,
    "INSTAGRAM_ACCESS_TOKEN": 10,
    "DB_PASSWORD": 8
  },
  "by_path_top_80": {
    "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py": 28,
    "scripts/quality/bys360_secret_repo_gate.py": 26,
    "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py": 20,
    "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py": 18,
    "scripts/security/validate_a6e_production_env_contract.py": 16,
    "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py": 14,
    "scripts/quality/bys360_s0a_claude_findings_verification_audit.py": 12,
    "config.py": 11,
    "app/security/audit.py": 11,
    "scripts/quality/bys360_s0b2_secret_risk_decision_matrix.py": 10,
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
    "scripts/quality/bys360_mobile_security_suite_gate_p4c.py": 2
  },
  "review_findings_top_200": [
    {
      "path": ".env",
      "line_no": 2,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "alembic.ini",
      "line_no": 15,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "config.py",
      "line_no": 104,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "docker-compose.yml",
      "line_no": 12,
      "term": "POSTGRES_PASSWORD",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/startup_checks.py",
      "line_no": 81,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "tests/conftest.py",
      "line_no": 5,
      "term": "SECRET_KEY",
      "decision": "TEST_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "tests/conftest.py",
      "line_no": 107,
      "term": "DATABASE_URL",
      "decision": "TEST_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 36,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 37,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 40,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 45,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 109,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 119,
      "term": "SENTRY_DSN",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 126,
      "term": "SENTRY_DSN",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/audit.py",
      "line_no": 136,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/startup_audit.py",
      "line_no": 45,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/startup_audit.py",
      "line_no": 54,
      "term": "SENTRY_DSN",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/startup_audit.py",
      "line_no": 56,
      "term": "SENTRY_DSN",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/security/startup_audit.py",
      "line_no": 81,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/communication_phase9b_service.py",
      "line_no": 247,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/config_hardening_service.py",
      "line_no": 105,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/config_hardening_service.py",
      "line_no": 106,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/config_hardening_service.py",
      "line_no": 107,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/config_hardening_service.py",
      "line_no": 118,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/config_hardening_service.py",
      "line_no": 133,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/instagram_portal_sync.py",
      "line_no": 50,
      "term": "INSTAGRAM_ACCESS_TOKEN",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/mail_performance_sender.py",
      "line_no": 444,
      "term": "MAIL_PASSWORD",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/mail_performance_sender.py",
      "line_no": 444,
      "term": "MAIL_USERNAME",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/security_compliance_final_gate.py",
      "line_no": 191,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/security_compliance_final_gate.py",
      "line_no": 191,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/security_compliance_final_gate.py",
      "line_no": 191,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/security_compliance_final_gate.py",
      "line_no": 191,
      "term": "MAIL_PASSWORD",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/security_hardening_service.py",
      "line_no": 286,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/security_hardening_service.py",
      "line_no": 295,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "app/services/ai/final_live_hardening.py",
      "line_no": 354,
      "term": "SECRET_KEY",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
      "line_no": 39,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
      "line_no": 53,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
      "line_no": 53,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
      "line_no": 106,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
      "line_no": 128,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
      "line_no": 62,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
      "line_no": 63,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
      "line_no": 64,
      "term": "POSTGRES_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
      "line_no": 405,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
      "line_no": 405,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
      "line_no": 173,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
      "line_no": 175,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
      "line_no": 100,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
      "line_no": 95,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
      "line_no": 97,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
      "line_no": 97,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_2.py",
      "line_no": 75,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_2.py",
      "line_no": 209,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py",
      "line_no": 46,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py",
      "line_no": 47,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py",
      "line_no": 48,
      "term": "DB_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py",
      "line_no": 48,
      "term": "POSTGRES_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.py",
      "line_no": 48,
      "term": "MAIL_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_3_duplicate_tree_cleanup_v2_17_4.py",
      "line_no": 34,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_3_duplicate_tree_cleanup_v2_17_4.py",
      "line_no": 105,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_v2_17_0.py",
      "line_no": 113,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_repo_hygiene_p0_v2_17_0.py",
      "line_no": 343,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0a_claude_findings_verification_audit.py",
      "line_no": 598,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0a_claude_findings_verification_audit.py",
      "line_no": 598,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 130,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 137,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 139,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 145,
      "term": "FLASK_SECRET",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 147,
      "term": "FLASK_SECRET",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 167,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 170,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 396,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 408,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 417,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c2_config_secretkey_exc_final_evidence.py",
      "line_no": 451,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 90,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 92,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 95,
      "term": "FLASK_SECRET",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 97,
      "term": "FLASK_SECRET",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 109,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 152,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 182,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 369,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 381,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 393,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 423,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c3_remaining_secretkey_block_hotfix.py",
      "line_no": 430,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 139,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 147,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 164,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 193,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 212,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 217,
      "term": "FLASK_SECRET",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 357,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_s0c_config_secretkey_exc_hotfix.py",
      "line_no": 416,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 25,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 44,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 45,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 46,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 46,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "DB_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "POSTGRES_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 51,
      "term": "INSTAGRAM_ACCESS_TOKEN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "TCKN_ENCRYPTION_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "DB_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "POSTGRES_PASSWORD",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/bys360_secret_repo_gate.py",
      "line_no": 55,
      "term": "INSTAGRAM_ACCESS_TOKEN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/quality/repair_bys360_sqlite_postgres_db_compat_v2_17_50.py",
      "line_no": 261,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/build_bys360_secure_release_v1_3.py",
      "line_no": 41,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_security_observability_v1.py",
      "line_no": 18,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_security_observability_v1.py",
      "line_no": 118,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_security_observability_v1.py",
      "line_no": 120,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py",
      "line_no": 11,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py",
      "line_no": 123,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py",
      "line_no": 147,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py",
      "line_no": 149,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 26,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 62,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 79,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 82,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 27,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 82,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 100,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 103,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 15,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 71,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 72,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
      "line_no": 61,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
      "line_no": 62,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
      "line_no": 66,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 16,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 17,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 22,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 168,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
      "line_no": 169,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 16,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 17,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 22,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 179,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
      "line_no": 180,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 72,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 73,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 76,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 134,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 135,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
      "line_no": 138,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
      "line_no": 56,
      "term": "SECRET_KEY",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
      "line_no": 57,
      "term": "DATABASE_URL",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
      "line_no": 67,
      "term": "SENTRY_DSN",
      "decision": "AUDIT_OR_TOOLING_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "scripts/windows/a8_live_cutover_guard.ps1",
      "line_no": 87,
      "term": "DATABASE_URL",
      "decision": "REFERENCE_REVIEW",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "tests/integration/test_http_db_core_flows.py",
      "line_no": 18,
      "term": "DATABASE_URL",
      "decision": "TEST_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    },
    {
      "path": "tests/integration/test_http_db_core_flows.py",
      "line_no": 37,
      "term": "DATABASE_URL",
      "decision": "TEST_REFERENCE",
      "normalized_risk": "REVIEW",
      "note": "Satır/değer rapora yazılmadı."
    }
  ]
}
```

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

## Pytest Full Summary

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

S0D pytest config çatışması ve backup test collection düzeltmesine geçilebilir.