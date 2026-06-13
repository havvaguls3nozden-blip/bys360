# BYS360 F821 Cleanup SAFE V1

Amaç: `ruff check app --select F821` bulgularını güvenli ve geri alınabilir şekilde azaltmak/sıfırlamak.

Kurulum:

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_F821_CLEANUP_SAFE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_f821_cleanup_safe_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunCompile -RunRuff
```

Rapor: `reports\quality\BYS360_F821_CLEANUP_SAFE_V1_REPORT.json`

Geri dönüş: patch öncesi dosyalar `reports\quality\f821_cleanup_safe_v1_backups_*` altında saklanır.
