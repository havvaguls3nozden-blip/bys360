# BYS360 Technical Debt Cleanup SAFE V16

Bu paket kod değiştirmez. V15 sonrası kalan riskli exception bloklarını, UI kalıntılarını ve .env/local DB hijyenini raporlar.

Komut:

```powershell
cd C:ys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_TECH_DEBT_CLEANUP_SAFE_V16_OVERLAY.zip" -DestinationPath "C:ys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windowsepair_bys360_technical_debt_cleanup_safe_v16.ps1 -ProjectRoot "C:ys360\project" -Mode all -OutputRoot "C:ys360" -RunCompile
```
