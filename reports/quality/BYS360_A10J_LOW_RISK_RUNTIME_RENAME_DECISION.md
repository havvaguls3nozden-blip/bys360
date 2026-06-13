# BYS360 A10J Düşük Riskli Runtime Rename Kararı

Tarih: 2026-06-12T19:24:31

## Sonuç

- OK: True
- Karar: A10J_LOW_RISK_RUNTIME_RENAME_GREEN
- Backup root: `C:\bys360\releases\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318`
- Target count: 7
- Renamed count: 7
- Source missing count: 0
- Target exists count: 0
- Compileall returncode: 0
- Pytest returncode: 0
- Final A10F safe quarantine candidate count: 0
- Final A10F cleanup candidate count: 59
- Final A10F keep or review count: 59
- Final A10I remaining count: 59

## Final A10I Karar Dağılımı

```json
{
  "rename_requires_compat_wrapper_and_import_update": 7,
  "keep_referenced_do_not_rename_now": 45,
  "rename_possible_but_runtime_smoke_required": 7
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

## İşlem Listesi

```json
[
  {
    "source": "app/services/hierarchy_assignment_repair_service.py",
    "target": "app/services/hierarchy_assignment_maintenance_service.py",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\app\\services\\hierarchy_assignment_repair_service.py",
    "status": "renamed"
  },
  {
    "source": "app/static/css/bys360_mobile_white_screen_repair_v6.css",
    "target": "app/static/css/bys360_mobile_white_screen_maintenance_v6.css",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\app\\static\\css\\bys360_mobile_white_screen_repair_v6.css",
    "status": "renamed"
  },
  {
    "source": "app/static/css/HOTFIX_UYGULAMA.txt",
    "target": "app/static/css/maintenance_UYGULAMA.txt",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\app\\static\\css\\HOTFIX_UYGULAMA.txt",
    "status": "renamed"
  },
  {
    "source": "app/static/css/messages_mobile_hotfix.css",
    "target": "app/static/css/messages_mobile_maintenance.css",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\app\\static\\css\\messages_mobile_hotfix.css",
    "status": "renamed"
  },
  {
    "source": "app/static/js/bys360_mobile_white_screen_repair_v6.js",
    "target": "app/static/js/bys360_mobile_white_screen_maintenance_v6.js",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\app\\static\\js\\bys360_mobile_white_screen_repair_v6.js",
    "status": "renamed"
  },
  {
    "source": "app/static/js/messages_mobile_hotfix.js",
    "target": "app/static/js/messages_mobile_maintenance.js",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\app\\static\\js\\messages_mobile_hotfix.js",
    "status": "renamed"
  },
  {
    "source": "migrations/sql/faz7_delegation_audit_column_compat_hotfix.sql",
    "target": "migrations/sql/module7_delegation_audit_column_compat_maintenance.sql",
    "backup": "C:\\bys360\\releases\\A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_20260612_192318\\migrations\\sql\\faz7_delegation_audit_column_compat_hotfix.sql",
    "status": "renamed"
  }
]
```

## Not

Yalnızca A10I düşük riskli rename_possible_but_runtime_smoke_required sınıfı yeniden adlandırıldı. Referanslı ve compatibility wrapper isteyen dosyalara dokunulmadı.