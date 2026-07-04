# BYS360 Score 10 Quality Fix V1 Overlay

Bu overlay son kalite analizindeki kritik başlıkları kapatır:

- F821/NameError riski: `send_email`, `_DONE`
- Windows'a özel SQLite yolu nedeniyle CI/test taşınabilirlik sorunu
- `.env`, `.venv`, `.git`, cache, backup, log ve runtime dosyalarının teslim ZIP'ine girmesi
- Temiz paket üretimi ve kalite gate scripti

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_SCORE10_QUALITY_FIX_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score10_quality_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score10_quality_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode clean-package -OutputRoot "C:\bys360\releases"
```

## Canlıya geçiş notu

Bu overlay canlı `.env` dosyasını değiştirmez. Canlıya çıkmadan önce normal yedek alınmalı, sonra kod dosyaları güncellenip servis yeniden başlatılmalıdır.
