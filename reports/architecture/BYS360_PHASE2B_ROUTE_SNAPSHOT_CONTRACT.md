# BYS360 Faz 2B Route Snapshot Contract

Tarih: 2026-06-13T10:34:40

## Sonuç

- OK: True
- Karar: PHASE2B_ROUTE_CONTRACT_GREEN
- Snapshot JSON: `C:\bys360\project\tests\architecture\snapshots\phase2b_route_snapshot_baseline.json`
- Test file: `C:\bys360\project\tests\architecture\test_phase2b_route_snapshot_contract.py`
- Route count: 975
- Blueprint count: 17
- Unique contract key count: 946
- Duplicate contract key count: 23
- Compileall returncode: 0
- Contract pytest returncode: 0
- Pytest quality smoke returncode: 0
- Pytest default returncode: 0

## Duplicate Contract Keys Top 50

```json
{
  "/dashboard/yonetici-ozeti|GET": 2,
  "/executive-summary/daily-weather-mail|GET": 2,
  "/executive-summary/daily-weather-mail|GET,POST": 2,
  "/executive-summary/mail-center/logs|GET": 2,
  "/executive-summary/mail-center/recipients|GET,POST": 2,
  "/executive-summary/mail-center/tasks|GET,POST": 2,
  "/manifest.webmanifest|GET": 3,
  "/notifications/<int:notification_id>/read|POST": 2,
  "/offline|GET": 2,
  "/performance/dashboard/heavy-panels|GET": 2,
  "/performance/president-approvals/<int:approval_id>/scorecard|GET": 3,
  "/performance/president-approvals|GET": 3,
  "/performance/reports|GET": 2,
  "/performans/baskan-onaylari/<int:approval_id>/karne|GET": 4,
  "/performans/baskan-onaylari|GET": 3,
  "/performans/stratejik/ai-kpi-analiz|GET": 2,
  "/performans/stratejik/hedefler|GET": 2,
  "/performans/stratejik/kpi-dashboard|GET": 2,
  "/performans/stratejik/oz-degerlendirme|GET,POST": 2,
  "/performans/stratejik/yetkinlik-kutuphanesi|GET": 2,
  "/surveys/<int:survey_id>/submit|POST": 2,
  "/workflow/executive-dashboard|GET": 2,
  "/yonetici-ozeti/gunluk-hava-maili|GET,POST": 2
}
```

## Contract Pytest Summary

```json
{
  "passed": 2,
  "failed": 0,
  "errors": 0,
  "skipped": 0,
  "deselected": 0,
  "warnings": 0
}
```

## Pytest Default Summary

```json
{
  "passed": 746,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Sonraki Adım

Faz 2C wildcard import explicit import planına geçilebilir.