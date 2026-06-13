# BYS360 S0F3 Pytest Isolated Update Verify

Tarih: 2026-06-13T10:18:32

## Sonuç

- OK: True
- Karar: S0F3_GREEN_ALL_PIP_AUDIT_FIXED
- Target spec: `pytest>=9.0.3`
- Rollback script: `C:\bys360\project\reports\quality\BYS360_S0F3_ROLLBACK_PYTEST.ps1`
- Pre pytest version: 8.4.2
- Post pytest version: 9.0.3
- Final pytest version: 9.0.3
- Install returncode: 0
- Rollback performed: False
- Pip-audit vulnerability count after: 0

## Validation After Update

```json
{
  "compileall_returncode": 0,
  "pytest_quality_smoke_returncode": 0,
  "pytest_quality_smoke_summary": {
    "passed": 5,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0,
    "warnings": 0
  },
  "pytest_full_returncode": 0,
  "pytest_full_summary": {
    "passed": 744,
    "skipped": 2,
    "deselected": 34,
    "failed": 0,
    "errors": 0,
    "warnings": 0
  },
  "pytest_default_returncode": 0,
  "pytest_default_summary": {
    "passed": 744,
    "skipped": 2,
    "deselected": 34,
    "failed": 0,
    "errors": 0,
    "warnings": 0
  }
}
```

## Pip-Audit By Package After

```json
{}
```

## Remaining Findings

```json
[]
```

## S0A Rerun

```json
{
  "returncode": 0,
  "ok": true,
  "red_flag_count": 1,
  "pip_audit_available": true,
  "pip_audit_vulnerability_count": 0,
  "old_venv_total_mb": 197.11
}
```

## Sonraki Adım

S0G eski .venv_old_* temizliğine geçilebilir.