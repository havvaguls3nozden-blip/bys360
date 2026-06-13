# BYS360 F821 Cleanup SAFE V2

Bu overlay, SAFE V1 sonrasında kalan 30 F821 bulgusunu ve V1 kaynaklı iki syntax/import sırası problemini düzeltir.

Hedefler:
- `app/api/mobile/services/communication_service.py` future import sırası
- `app/performance/v2_1_11_evaluator_reminder_center_routes.py` bozuk çok satırlı import bloğu
- kalan 30 F821 için güvenli import/helper bağlamaları

Çalıştırma:

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_F821_CLEANUP_SAFE_V2_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_f821_cleanup_safe_v2.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunCompile -RunRuff
```

Yedekler `reports\quality\f821_cleanup_safe_v2_backups_*` altında tutulur.
