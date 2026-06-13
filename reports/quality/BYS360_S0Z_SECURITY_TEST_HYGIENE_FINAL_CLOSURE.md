# BYS360 S0Z Güvenlik ve Test Hijyeni Final Kapanış Raporu

Tarih: 2026-06-13T10:25:51

## Sonuç

- OK: True
- Karar: S0Z_GREEN_READY_FOR_PHASE2_ARCHITECTURE
- All phase reports green: True
- Tests green: True
- Security green: True
- S0A red flag count: 0
- Pip-audit vulnerability count: 0
- S0A old venv total MB: 0
- Compileall returncode: 0
- Collect-only returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0
- Pytest default returncode: 0

## Faz Durumları

```json
{
  "S0C3": {
    "path": "C:\\bys360\\project\\reports\\quality\\BYS360_S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX.json",
    "exists": true,
    "ok": true,
    "decision": "S0C3_GREEN",
    "generated_at": "2026-06-13T09:57:10"
  },
  "S0D": {
    "path": "C:\\bys360\\project\\reports\\quality\\BYS360_S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX.json",
    "exists": true,
    "ok": true,
    "decision": "S0D_GREEN",
    "generated_at": "2026-06-13T10:02:06"
  },
  "S0E": {
    "path": "C:\\bys360\\project\\reports\\quality\\BYS360_S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_CLEANUP.json",
    "exists": true,
    "ok": true,
    "decision": "S0E_GREEN",
    "generated_at": "2026-06-13T10:06:14"
  },
  "S0F3": {
    "path": "C:\\bys360\\project\\reports\\quality\\BYS360_S0F3_PYTEST_ISOLATED_UPDATE_VERIFY.json",
    "exists": true,
    "ok": true,
    "decision": "S0F3_GREEN_ALL_PIP_AUDIT_FIXED",
    "generated_at": "2026-06-13T10:18:32"
  },
  "S0G": {
    "path": "C:\\bys360\\project\\reports\\quality\\BYS360_S0G_OLD_VENV_ARCHIVE_CLEANUP.json",
    "exists": true,
    "ok": true,
    "decision": "S0G_GREEN",
    "generated_at": "2026-06-13T10:22:09"
  }
}
```

## S0A Rerun

```json
{
  "returncode": 0,
  "ok": true,
  "red_flag_count": 0,
  "pip_audit_vulnerability_count": 0,
  "old_venv_total_mb": 0
}
```

## Pip-Audit

```json
{
  "available": true,
  "returncode": 0,
  "vulnerability_count": 0,
  "by_package": {}
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

Faz 2A mimari borç haritasına geçilebilir.