# BYS360 A10M Placeholder Rename Fix Kararı

Tarih: 2026-06-12T19:40:07

## Sonuç

- OK: True
- Karar: A10M_PLACEHOLDER_RENAME_FIX_GREEN
- Backup root: `C:\bys360\releases\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854`
- Restored count: 7
- Bad missing count: 0
- Invalid count: 0
- Compileall returncode: 0
- Pytest returncode: 0
- Final A10F safe quarantine candidate count: 0
- Final A10F cleanup candidate count: 59
- Final A10I remaining count: 59
- Final A10K remaining low risk count: 7

## Final A10I Karar Dağılımı

```json
{
  "rename_requires_compat_wrapper_and_import_update": 7,
  "keep_referenced_do_not_rename_now": 45,
  "rename_possible_but_runtime_smoke_required": 7
}
```

## Final A10K Karar Dağılımı

```json
{
  "rename_with_custom_suggestion": 7
}
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

## Düzeltmeler

```json
[
  {
    "source": "migrations/versions/523a11510d7d_historical_placeholder.py",
    "target": "migrations/versions/523a11510d7d_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\523a11510d7d_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  },
  {
    "source": "migrations/versions/71d0eccf02c0_historical_placeholder.py",
    "target": "migrations/versions/71d0eccf02c0_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\71d0eccf02c0_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  },
  {
    "source": "migrations/versions/b31c7a5d9e2f_historical_placeholder.py",
    "target": "migrations/versions/b31c7a5d9e2f_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\b31c7a5d9e2f_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  },
  {
    "source": "migrations/versions/c32f8a1e4b9d_historical_placeholder.py",
    "target": "migrations/versions/c32f8a1e4b9d_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\c32f8a1e4b9d_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  },
  {
    "source": "migrations/versions/c4a1d9e2f731_historical_placeholder.py",
    "target": "migrations/versions/c4a1d9e2f731_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\c4a1d9e2f731_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  },
  {
    "source": "migrations/versions/d33a9c4e8f10_historical_placeholder.py",
    "target": "migrations/versions/d33a9c4e8f10_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\d33a9c4e8f10_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  },
  {
    "source": "migrations/versions/e8c3f1a9b4d0_historical_placeholder.py",
    "target": "migrations/versions/e8c3f1a9b4d0_historical_placeharchiveer.py",
    "backup_bad_target": "C:\\bys360\\releases\\A10M_PLACEHOLDER_RENAME_FIX_BACKUP_20260612_193854\\migrations\\versions\\e8c3f1a9b4d0_historical_placeharchiveer.py",
    "status": "restored_to_original_placeholder_name"
  }
]
```

## Not

A10L sonrasında oluşan placeharchiveer dosya adları kalite nedeniyle orijinal historical_placeholder adına geri alındı. Bu dosyalar Alembic tarihsel placeholder olarak korunacaktır.