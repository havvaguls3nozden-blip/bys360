# BYS360 S0B2 Secret Risk Decision Matrix

Tarih: 2026-06-13T09:50:28

## Sonuç

- OK: True
- Karar: S0B2_HIGH_RISK_MANUAL_SECRET_REVIEW_REQUIRED
- Source S0B OK: True
- Source S0B high risk count: 22
- Source S0B review risk count: 334
- Classified item count: 222
- Normalized high count: 1
- Normalized review count: 189
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

## By Normalized Risk

```json
{
  "HIGH": 1,
  "REVIEW": 189,
  "LOW": 32
}
```

## By Decision

```json
{
  "POSSIBLE_HARDCODED_CONFIG_VALUE": 1,
  "TEST_REFERENCE": 4,
  "SCHEMA_OR_GUARDRAIL_REFERENCE": 30,
  "AUDIT_OR_TOOLING_REFERENCE": 135,
  "EXAMPLE_OR_TEMPLATE": 2,
  "REFERENCE_REVIEW": 50
}
```

## Rotate Review Terms

```json
[
  "SECRET_KEY"
]
```

## Rotate Review Paths

```json
[
  "config.py"
]
```

## High Decisions

```json
[
  {
    "path": "config.py",
    "line_no": 178,
    "term": "SECRET_KEY",
    "original_risk": "HIGH",
    "normalized_risk": "HIGH",
    "decision": "POSSIBLE_HARDCODED_CONFIG_VALUE",
    "action": "Sabit değer atanmış olabilir. Canlı secret mı, test/dev fallback mi manuel doğrulanmalı.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  }
]
```

## Review Decisions

```json
[
  {
    "path": "tests/conftest.py",
    "line_no": 107,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "TEST_REFERENCE",
    "action": "Test fixture veya test fallback olabilir; canlı secret kabul edilmez, ayrı doğrulanmalı.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/check_bys360_p0_security_observability_v1.py",
    "line_no": 116,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/check_bys360_p0_sentry_dbssl_csp_v2.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_1.py",
    "line_no": 79,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_2.py",
    "line_no": 100,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
    "line_no": 71,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "9-20",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1.py",
    "line_no": 62,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
    "line_no": 17,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_1.py",
    "line_no": 169,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
    "line_no": 17,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_2.py",
    "line_no": 180,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "1-8",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
    "line_no": 73,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
    "line_no": 135,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "line_no": 56,
    "term": "SECRET_KEY",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "21-40",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "line_no": 57,
    "term": "DATABASE_URL",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "41-80",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/security/repair_bys360_secure_release_secret_clean_v1_4.py",
    "line_no": 67,
    "term": "SENTRY_DSN",
    "original_risk": "HIGH",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "assignment",
    "value_shape": {
      "has_value": true,
      "length_bucket": "9-20",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "alembic.ini",
    "line_no": 15,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "config.py",
    "line_no": 104,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "config.py",
    "line_no": 165,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "config.py",
    "line_no": 166,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "config.py",
    "line_no": 180,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/startup_checks.py",
    "line_no": 81,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 5,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "TEST_REFERENCE",
    "action": "Test fixture veya test fallback olabilir; canlı secret kabul edilmez, ayrı doğrulanmalı.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 23,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "TEST_REFERENCE",
    "action": "Test fixture veya test fallback olabilir; canlı secret kabul edilmez, ayrı doğrulanmalı.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "tests/conftest.py",
    "line_no": 97,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "TEST_REFERENCE",
    "action": "Test fixture veya test fallback olabilir; canlı secret kabul edilmez, ayrı doğrulanmalı.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_login/utils.py",
    "line_no": 37,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_login/utils.py",
    "line_no": 52,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 31,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 38,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 72,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/csrf.py",
    "line_no": 87,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask_wtf/form.py",
    "line_no": 42,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": ".venv_old_20260612_200915/Lib/site-packages/flask/sansio/app.py",
    "line_no": 215,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/config/release_manifest.py",
    "line_no": 69,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/config/release_manifest.py",
    "line_no": 70,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/config/release_manifest.py",
    "line_no": 72,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 36,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 37,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 40,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 45,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 109,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 119,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 126,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/audit.py",
    "line_no": 136,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 45,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 54,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 56,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/security/startup_audit.py",
    "line_no": 81,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/communication_phase9b_service.py",
    "line_no": 247,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 105,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 106,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 107,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 118,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/config_hardening_service.py",
    "line_no": 133,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/instagram_portal_sync.py",
    "line_no": 50,
    "term": "INSTAGRAM_ACCESS_TOKEN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/mail_performance_sender.py",
    "line_no": 444,
    "term": "MAIL_PASSWORD",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/mail_performance_sender.py",
    "line_no": 444,
    "term": "MAIL_USERNAME",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/security_compliance_final_gate.py",
    "line_no": 191,
    "term": "MAIL_PASSWORD",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/security_hardening_service.py",
    "line_no": 286,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/security_hardening_service.py",
    "line_no": 295,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/ai/final_live_hardening.py",
    "line_no": 354,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 18,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 20,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 23,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 25,
    "term": "MAIL_PASSWORD",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "app/services/settings/constants.py",
    "line_no": 26,
    "term": "MAIL_USERNAME",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "REFERENCE_REVIEW",
    "action": "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 94,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 95,
    "term": "POSTGRES_PASSWORD",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 96,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 97,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 98,
    "term": "INSTAGRAM_ACCESS_TOKEN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/maintenance/bys360_tech_debt_cleanup_safe_v1.py",
    "line_no": 103,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_baseline_gate_p5a.py",
    "line_no": 233,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_baseline_gate_p5a.py",
    "line_no": 234,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py",
    "line_no": 160,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_final_evidence_gate_p5f.py",
    "line_no": 161,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_inventory_precision_gate_p6c.py",
    "line_no": 225,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_inventory_precision_gate_p6c.py",
    "line_no": 226,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d_v2.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_release_suite_gate_p5d_v2.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b_v2.py",
    "line_no": 162,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_regression_evidence_suite_gate_p6b_v2.py",
    "line_no": 163,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_uat_evidence_gate_p5e.py",
    "line_no": 154,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_android_responsive_visual_uat_evidence_gate_p5e.py",
    "line_no": 155,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 39,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 40,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 40,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 40,
    "term": "POSTGRES_PASSWORD",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 41,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 41,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 41,
    "term": "INSTAGRAM_ACCESS_TOKEN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 53,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 53,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 106,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 128,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 269,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 277,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 278,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0e_final_secret_gate.py",
    "line_no": 280,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 62,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 63,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 64,
    "term": "POSTGRES_PASSWORD",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 405,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_claude_score_uplift_p0_security_repo_hygiene.py",
    "line_no": 405,
    "term": "TCKN_ENCRYPTION_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
    "line_no": 171,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
    "line_no": 173,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_local_sqlite_persistent_db_hotfix_v2.py",
    "line_no": 175,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "line_no": 125,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "line_no": 126,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "line_no": 127,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "line_no": 125,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "line_no": 126,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "line_no": 127,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "line_no": 115,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "line_no": 117,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "line_no": 118,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "line_no": 98,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "line_no": 99,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_auth_guard_matrix_gate_p4a.py",
    "line_no": 100,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_domain_smoke_p1f.py",
    "line_no": 131,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 139,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 140,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 253,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 254,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_performance_response_gate_p3e.py",
    "line_no": 255,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 140,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 141,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 159,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 160,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 161,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 222,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 223,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "line_no": 224,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 140,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 141,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 142,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 159,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 160,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 161,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 228,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 229,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2.py",
    "line_no": 230,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_pytest_contract_gate_p2a.py",
    "line_no": 279,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_pytest_contract_gate_p2a_v2.py",
    "line_no": 280,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_release_evidence_gate_p4e.py",
    "line_no": 136,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_release_evidence_gate_p4e.py",
    "line_no": 137,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 203,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 205,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 234,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v2.py",
    "line_no": 236,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 203,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 205,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 234,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_level_smoke_gate_p2c_v3.py",
    "line_no": 236,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 134,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 135,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 136,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 197,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 198,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_request_scenario_gate_p3a.py",
    "line_no": 199,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "line_no": 94,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "line_no": 95,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_response_suite_gate_p3f.py",
    "line_no": 97,
    "term": "SENTRY_DSN",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "line_no": 93,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "line_no": 94,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "line_no": 95,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
    "line_no": 95,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
    "line_no": 96,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v2.py",
    "line_no": 97,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "line_no": 95,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "line_no": 96,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "list_tuple_set_or_literal_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "line_no": 97,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "term_reference",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_evidence_gate_p4d.py",
    "line_no": 137,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_evidence_gate_p4d.py",
    "line_no": 138,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_suite_gate_p4c.py",
    "line_no": 226,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_suite_gate_p4c.py",
    "line_no": 227,
    "term": "SECRET_KEY",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  },
  {
    "path": "scripts/quality/bys360_mobile_security_suite_gate_p4c_v2.py",
    "line_no": 220,
    "term": "DATABASE_URL",
    "original_risk": "REVIEW",
    "normalized_risk": "REVIEW",
    "decision": "AUDIT_OR_TOOLING_REFERENCE",
    "action": "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez.",
    "expression_kind": "dict_key_or_schema",
    "value_shape": {
      "has_value": false,
      "length_bucket": "empty",
      "looks_placeholder": false,
      "looks_env_ref": false,
      "looks_url": false,
      "looks_jinja_or_format": false,
      "looks_secretish": false
    },
    "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu."
  }
]
```

## Sonraki Adım

HIGH varsa S0B3 manuel rotate karar raporu; HIGH yoksa S0C config.py bug fix.