# BYS360 S0D Pytest Config ve Backup Collection Hotfix

Tarih: 2026-06-13T10:02:06

## Sonuç

- OK: True
- Karar: S0D_GREEN
- Backup root: `C:\bys360\releases\S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX_BACKUP_20260613_100036`
- Operation count: 2
- Pytest-cov available: False
- Marker count: 8
- Config conflict after: False
- Backup collection hit count: 0
- Compileall returncode: 0
- Collect-only returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0
- Pytest default returncode: 0

## Operations

```json
[
  {
    "type": "write_pytest_ini_single_source",
    "status": "patched",
    "include_cov": false,
    "marker_count": 8
  },
  {
    "type": "remove_pyproject_pytest_ini_options_section",
    "status": "patched",
    "removed_line_count": 6
  }
]
```

## Post State

```json
{
  "pytest_ini_exists": true,
  "pyproject_exists": true,
  "pyproject_has_tool_pytest_ini_options": false,
  "pytest_ini_has_testpaths": true,
  "pytest_ini_has_norecursedirs_reports": true,
  "pytest_ini_has_strict_markers": true,
  "pytest_ini_has_disable_warnings": true,
  "pytest_ini_has_markers": true,
  "pytest_config_conflict_likely": false
}
```

## Backup Tests Detected But Not Deleted

```json
{
  "backup_test_dir_count": 3,
  "backup_test_file_count": 201,
  "backup_test_dirs": [
    {
      "path": "reports/quality/a5_p1_archive_marker_safe_v1_backups_20260612_090923/tests",
      "test_file_count": 82
    },
    {
      "path": "reports/quality/P2_BACKUP/tests",
      "test_file_count": 119
    },
    {
      "path": "reports/quality/P2_BACKUP/tests/_archive_a5_obsolete/20260612_090923/tests",
      "test_file_count": 0
    }
  ],
  "note": "Bu faz backup test klasörlerini silmez; pytest collection dışına alır."
}
```

## Backup Collection Evidence

```json
{
  "backup_collection_hit_count": 0,
  "backup_collection_hits": []
}
```

## S0A Rerun

```json
{
  "returncode": 0,
  "ok": true,
  "pytest_config_conflict_likely": false,
  "backup_test_dir_count": 6,
  "red_flag_count": 3
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

S0E backup test/report arşiv temizliği manifestli yapılabilir.