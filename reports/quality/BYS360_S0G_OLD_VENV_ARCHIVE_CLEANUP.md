# BYS360 S0G Old Venv Archive Cleanup

Tarih: 2026-06-13T10:22:09

## Sonuç

- OK: True
- Karar: S0G_GREEN
- Archive root: `C:\bys360\releases\S0G_OLD_VENV_ARCHIVE_20260613_102048`
- Restore script: `C:\bys360\releases\S0G_OLD_VENV_ARCHIVE_20260613_102048\RESTORE_S0G_OLD_VENV.ps1`
- Candidate count: 1
- Operation count: 1
- Error count: 0
- Old venv dir count before: 1
- Old venv total MB before: 197.11
- Old venv dir count after: 0
- Old venv total MB after: 0
- Compileall returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0
- Pytest default returncode: 0

## Before State

```json
{
  "old_venv_dir_count": 1,
  "old_venv_total_mb": 197.11,
  "old_venv_dirs": [
    {
      "path": ".venv_old_20260612_200915",
      "file_count": 8935,
      "dir_count": 991,
      "size_mb": 197.11
    }
  ]
}
```

## Operations

```json
[
  {
    "type": "move_old_venv_to_release_archive",
    "status": "moved",
    "source": ".venv_old_20260612_200915",
    "destination": "C:\\bys360\\releases\\S0G_OLD_VENV_ARCHIVE_20260613_102048\\moved\\.venv_old_20260612_200915",
    "before": {
      "source": ".venv_old_20260612_200915",
      "file_count": 8935,
      "dir_count": 991,
      "size_mb": 197.11
    },
    "after": {
      "destination": "C:\\bys360\\releases\\S0G_OLD_VENV_ARCHIVE_20260613_102048\\moved\\.venv_old_20260612_200915",
      "destination_exists": true,
      "source_exists_after_move": false,
      "destination_file_count": 8935,
      "destination_dir_count": 991,
      "destination_size_mb": 197.11
    }
  }
]
```

## Errors

```json
[]
```

## After State

```json
{
  "old_venv_dir_count": 0,
  "old_venv_total_mb": 0,
  "old_venv_dirs": []
}
```

## S0A Rerun

```json
{
  "returncode": 0,
  "ok": true,
  "red_flag_count": 0,
  "pip_audit_available": true,
  "pip_audit_vulnerability_count": 0,
  "old_venv_dir_count": 0,
  "old_venv_total_mb": 0
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

S0Z final güvenlik/test hijyen kapanış raporu üretilebilir.