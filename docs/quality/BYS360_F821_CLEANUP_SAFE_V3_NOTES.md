# BYS360 F821 Cleanup SAFE V3

Bu küçük paket, F821 SAFE V2 sonrasında kalan tek kök hatayı kapatır:

- `app/admin/ops_routes.py` içine `PerformancePeriod` importu ekler.
- Ruff F821 sayısının 0 olmasını hedefler.
- Değişen dosyayı `reports/quality/f821_cleanup_safe_v3_backups_*` altında yedekler.

Çalıştırma:

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_F821_CLEANUP_SAFE_V3_OVERLAY.zip" `
  -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_f821_cleanup_safe_v3.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode all `
  -RunCompile `
  -RunRuff
```
