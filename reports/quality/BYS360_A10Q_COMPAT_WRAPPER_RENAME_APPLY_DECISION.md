# BYS360 A10Q Compat Wrapper Rename Apply Kararı

Tarih: 2026-06-12T19:56:56

## Sonuç

- OK: True
- Karar: A10Q_COMPAT_WRAPPER_RENAME_APPLY_GREEN
- A10P OK: True
- Backup root: `C:\bys360\releases\A10Q_COMPAT_WRAPPER_RENAME_BACKUP_20260612_195614`
- Apply candidate count: 3
- Applied count: 3
- Already wrapped count: 0
- Failed count: 0
- Compileall returncode: 0
- Import smoke returncode: 0
- Pytest returncode: 0

## İşlemler

```json
[
  {
    "old_path": "app/schema_guard_core_repairs.py",
    "new_path": "app/schema_guard_core_maintenances.py",
    "backup": "C:\\bys360\\releases\\A10Q_COMPAT_WRAPPER_RENAME_BACKUP_20260612_195614\\app\\schema_guard_core_repairs.py",
    "status": "renamed_and_wrapper_created"
  },
  {
    "old_path": "app/refactor/hotfix_merge_registry.py",
    "new_path": "app/refactor/maintenance_merge_registry.py",
    "backup": "C:\\bys360\\releases\\A10Q_COMPAT_WRAPPER_RENAME_BACKUP_20260612_195614\\app\\refactor\\hotfix_merge_registry.py",
    "status": "renamed_and_wrapper_created"
  },
  {
    "old_path": "app/services/performance/common_admin_scope_hotfix.py",
    "new_path": "app/services/performance/common_admin_scope_maintenance.py",
    "backup": "C:\\bys360\\releases\\A10Q_COMPAT_WRAPPER_RENAME_BACKUP_20260612_195614\\app\\services\\performance\\common_admin_scope_hotfix.py",
    "status": "renamed_and_wrapper_created"
  }
]
```

## Eski Modül Yolları

```json
[
  "app.schema_guard_core_repairs",
  "app.refactor.hotfix_merge_registry",
  "app.services.performance.common_admin_scope_hotfix"
]
```

## Yeni Modül Yolları

```json
[
  "app.schema_guard_core_maintenances",
  "app.refactor.maintenance_merge_registry",
  "app.services.performance.common_admin_scope_maintenance"
]
```

## Import Smoke

```text
A10Q_IMPORT_SMOKE_OK


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

## Not

A10Q yalnızca A10P apply_candidates listesindeki 3 Python dosyasını yeni ada taşıdı ve eski import yollarında compatibility wrapper bıraktı. Static, disabled ve Android debug dosyalarına dokunulmadı.

## Sonraki Adım

A10R: 45 referenced keep + 7 historical placeholder + 4 keep allowlist + 3 wrapper kararlarını final A10 evidence raporunda kapat.