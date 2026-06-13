# BYS360 S0C config.py SECRET_KEY ve exc Hotfix

Tarih: 2026-06-13T09:50:28

## Sonuç

- OK: False
- Karar: S0C_REVIEW_REQUIRED
- Target: config.py
- Backup: `C:\bys360\releases\S0C_CONFIG_SECRETKEY_EXC_HOTFIX_BACKUP_20260613_094947\config.py`
- File changed: True
- Operation count: 2
- Compileall returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0

## Operations

```json
[
  {
    "type": "config_exc_bug_fix",
    "line_no": 148,
    "status": "patched",
    "note": "except Exception -> except Exception as exc"
  },
  {
    "type": "secret_key_env_centered_fallback",
    "line_no": 178,
    "status": "patched",
    "note": "SECRET_KEY sabit değer yerine ortam değişkeni merkezli hale getirildi; değer rapora yazılmadı."
  }
]
```

## Post Scan

```json
{
  "exc_info_exc_line_count": 1,
  "exc_bug_likely_after_patch": false,
  "exc_bug_findings": [
    {
      "line_no": 149,
      "plain_except_nearby": false,
      "as_exc_nearby": true
    }
  ],
  "secret_key_assignment_count": 2,
  "secret_key_assignment_findings": [
    {
      "line_no": 178,
      "uses_env_on_assignment_line": false,
      "note": "Satır değeri rapora yazılmadı."
    },
    {
      "line_no": 191,
      "uses_env_on_assignment_line": true,
      "note": "Satır değeri rapora yazılmadı."
    }
  ],
  "secret_key_env_reference_present": true,
  "flask_secret_env_reference_present": true
}
```

## S0B2 Rerun

```json
{
  "returncode": 0,
  "normalized_high_count": 1,
  "normalized_review_count": 189,
  "decision": "S0B2_HIGH_RISK_MANUAL_SECRET_REVIEW_REQUIRED"
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

S0C raporu incelenmeli; gerekirse backup üzerinden geri dönüş yapılmalı.