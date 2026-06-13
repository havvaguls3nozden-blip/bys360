# BYS360 A10R Final Teknik Borç Evidence

Tarih: 2026-06-12T20:01:05

## Sonuç

- OK: True
- Karar: A10R_FINAL_TECH_DEBT_EVIDENCE_GREEN
- Compileall returncode: 0
- Import smoke returncode: 0
- Pytest returncode: 0

## Final Sayımlar

```json
{
  "safe_quarantine_candidate_count": 0,
  "referenced_keep_count": 45,
  "historical_placeholder_keep_count": 7,
  "compat_required_count": 7,
  "compat_apply_candidate_count": 3,
  "compat_keep_allowlist_count": 4,
  "compat_applied_count": 3,
  "compat_failed_count": 0,
  "unclassified_count": 0,
  "non_placeholder_low_risk_count": 0
}
```

## Wrapper Kontrolü

- Wrapper check count: 3
- Wrapper not OK count: 0

```json
[
  {
    "old_path": "app/schema_guard_core_repairs.py",
    "new_path": "app/schema_guard_core_maintenances.py",
    "old_exists": true,
    "new_exists": true,
    "wrapper_has_marker": true,
    "wrapper_mentions_new_module": true,
    "status": "ok"
  },
  {
    "old_path": "app/refactor/hotfix_merge_registry.py",
    "new_path": "app/refactor/maintenance_merge_registry.py",
    "old_exists": true,
    "new_exists": true,
    "wrapper_has_marker": true,
    "wrapper_mentions_new_module": true,
    "status": "ok"
  },
  {
    "old_path": "app/services/performance/common_admin_scope_hotfix.py",
    "new_path": "app/services/performance/common_admin_scope_maintenance.py",
    "old_exists": true,
    "new_exists": true,
    "wrapper_has_marker": true,
    "wrapper_mentions_new_module": true,
    "status": "ok"
  }
]
```

## Import Smoke

```text
A10R_IMPORT_SMOKE_OK


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

## Kalan Kalite İşi

```json
{
  "warnings": 32,
  "next_phase": "A11_WARNING_ZERO",
  "note": "A10 teknik borç temizliği kapandı; kalan 32 warning A11 Warning Zero fazının konusudur."
}
```

## Canlı Notu

Bu A10 kapanışı local/repo kalite kanıtıdır. Canlı ortam için ayrıca gerçek .env, Sentry DSN, DB SSL/TLS, canlı backup ve URL smoke gate yapılmalıdır.

## Evidence ZIP

- ZIP: `C:\bys360\releases\BYS360_A10R_FINAL_TECH_DEBT_EVIDENCE_20260612_200025.zip`
- SHA256: `2D60A8C3A58471F542D3F790FC0A8BF103368FFD2CBE8587D5AF29C25110036E`
- Evidence file count: 54