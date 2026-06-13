# BYS360 A10G Güvenli Cleanup Karantina Kararı

Tarih: 2026-06-12T19:14:58

## Sonuç

- OK: False
- Karar: A10G_SAFE_CLEANUP_QUARANTINE_NOT_GREEN
- Quarantine root: `C:\bys360\releases\A10G_SAFE_CLEANUP_QUARANTINE_20260612_191407`
- Safe candidate count before: 200
- Moved count: 200
- Missing before move count: 0
- Compileall returncode: 0
- A10A returncode: 0
- A10B returncode: 0
- A10F returncode: 0
- Safe quarantine candidate count after: 87
- Cleanup candidate count after: 136
- Keep or review count after: 49
- Pytest returncode: 0

## Pytest Özeti

```json
{
  "warnings": 32,
  "passed": 744,
  "skipped": 2,
  "deselected": 34
}
```

## A10F Son Karar Dağılımı

```json
{
  "runtime_keep_rename_later": 12,
  "safe_quarantine_candidate": 87,
  "referenced_keep_review": 37
}
```

## Not

Yalnızca A10F safe_quarantine_candidate sınıfı taşındı. Runtime, template, mobile, migration ve referans alan dosyalara dokunulmadı.