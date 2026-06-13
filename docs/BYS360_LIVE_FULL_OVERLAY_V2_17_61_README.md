# BYS360 LIVE FULL OVERLAY V2.17.61 HOTFIX

Bu hotfix, V2.17.60 kontrolünde `ExitCode=2` alınması ihtimaline karşı daha dayanıklı canlı toparlama ve daha açıklayıcı check raporu üretir.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_LIVE_FULL_OVERLAY_V2_17_61_HOTFIX.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_live_full_overlay_v2_17_61.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_live_full_overlay_v2_17_61.ps1 -ProjectRoot "C:\bys360\project"
```

Rapor yolu:

`reports\quality\bys360_live_full_overlay_v2_17_61_report.md`

Bu paket `.env`, şifre veya canlı veri içermez.
