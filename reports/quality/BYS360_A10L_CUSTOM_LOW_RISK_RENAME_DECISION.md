# BYS360 A10L Custom Low Risk Rename Kararı

Tarih: 2026-06-12T19:35:50

## Sonuç

- OK: True
- Karar: A10L_CUSTOM_LOW_RISK_RENAME_GREEN
- Backup root: `C:\bys360\releases\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435`
- Target count: 7
- Renamed count: 7
- Source missing count: 0
- Target exists count: 0
- Invalid count: 0
- Same path count: 0
- Compileall returncode: 0
- Pytest returncode: 0
- Final A10F safe quarantine candidate count: 0
- Final A10F cleanup candidate count: 52
- Final A10I remaining count: 52
- Final A10K remaining low risk count: 0

## Refresh Returncodes

```json
{
  "a10a": 0,
  "a10b": 0,
  "a10f": 0,
  "a10i": 0,
  "a10k": 0
}
```

## Final A10I Karar Dağılımı

```json
{
  "rename_requires_compat_wrapper_and_import_update": 7,
  "keep_referenced_do_not_rename_now": 45
}
```

## Final A10K Karar Dağılımı

```json
{}
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

## İşlemler

```json
[
  {
    "source": "migrations/versions/523a11510d7d_historical_placeholder.py",
    "target": "migrations/versions/523a11510d7d_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\523a11510d7d_historical_placeholder.py",
    "status": "renamed"
  },
  {
    "source": "migrations/versions/71d0eccf02c0_historical_placeholder.py",
    "target": "migrations/versions/71d0eccf02c0_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\71d0eccf02c0_historical_placeholder.py",
    "status": "renamed"
  },
  {
    "source": "migrations/versions/b31c7a5d9e2f_historical_placeholder.py",
    "target": "migrations/versions/b31c7a5d9e2f_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\b31c7a5d9e2f_historical_placeholder.py",
    "status": "renamed"
  },
  {
    "source": "migrations/versions/c32f8a1e4b9d_historical_placeholder.py",
    "target": "migrations/versions/c32f8a1e4b9d_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\c32f8a1e4b9d_historical_placeholder.py",
    "status": "renamed"
  },
  {
    "source": "migrations/versions/c4a1d9e2f731_historical_placeholder.py",
    "target": "migrations/versions/c4a1d9e2f731_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\c4a1d9e2f731_historical_placeholder.py",
    "status": "renamed"
  },
  {
    "source": "migrations/versions/d33a9c4e8f10_historical_placeholder.py",
    "target": "migrations/versions/d33a9c4e8f10_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\d33a9c4e8f10_historical_placeholder.py",
    "status": "renamed"
  },
  {
    "source": "migrations/versions/e8c3f1a9b4d0_historical_placeholder.py",
    "target": "migrations/versions/e8c3f1a9b4d0_historical_placeharchiveer.py",
    "backup": "C:\\bys360\\releases\\A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_20260612_193435\\migrations\\versions\\e8c3f1a9b4d0_historical_placeholder.py",
    "status": "renamed"
  }
]
```

## Not

A10K custom suggestion üreten düşük riskli dosyalar yedekli yeniden adlandırıldı. Keep allowlist adaylarına ve referanslı dosyalara dokunulmadı.