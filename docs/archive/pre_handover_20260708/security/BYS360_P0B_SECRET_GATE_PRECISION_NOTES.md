# BYS360 P0B Secret Gate Precision Notes

Bu hotfix, P0 sonrası yeniden oluşturulan `.venv` klasörünün ve üretilmiş rapor/yedek/karantina klasörlerinin secret gate tarafından taranmasını engeller.

## Amaç

- Gerçek secret sızıntılarını yakalamaya devam etmek.
- Environment variable referanslarını ve placeholder değerlerini gerçek secret sanmamak.
- `.venv`, `reports`, `backups`, `quarantine`, `releases`, `archive`, `node_modules`, `build`, `dist` gibi klasörleri tarama dışında bırakmak.

## Çalıştırma

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_SCORE_UPLIFT_P0B_SECRET_GATE_PRECISION_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p0b_secret_gate_precision_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunGate
```
