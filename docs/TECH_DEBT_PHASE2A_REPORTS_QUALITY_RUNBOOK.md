# BYS360 Teknik Borç Faz 2A — reports/quality Arşivleme Runbook

Amaç: `reports/quality` altında biriken geçmiş kalite kanıtlarını sınıflandırmak ve gerekirse proje dışındaki `C:\bys360\archive` alanına taşımak.

Bu faz uygulama kodunu değiştirmez. `dry-run` modu yalnızca plan üretir. `apply` modu dosyaları silmez; dış arşive taşır.

## Dry-run

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2a_reports_quality.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode dry-run `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2a"
```

## Planı oku

```powershell
Get-Content "C:\bys360\reports\tech_debt_phase2a\BYS360_TECH_DEBT_PHASE2A_REPORTS_QUALITY_PLAN.md" -TotalCount 160
Import-Csv "C:\bys360\reports\tech_debt_phase2a\BYS360_TECH_DEBT_PHASE2A_REPORTS_QUALITY_PLAN.csv" | Group-Object action
```

## Apply

Sadece dry-run planı uygun görünürse çalıştırılır:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2a_reports_quality.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode apply `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2a" `
  -ArchiveRoot "C:\bys360\archive"
```

## Git kontrol

```powershell
git status --short
git diff --stat
```

