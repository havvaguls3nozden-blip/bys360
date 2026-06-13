BYS360_TECH_DEBT_CLEANUP_SAFE_V20

Amaç:
- app\services\corporate_information_center.py içinde V19 raporunda kalan 2 safeish exception bloğuna logging ekler.
- DB rollback, rollback+return, raise, continue ve riskli kontrol akışı bloklarına dokunmaz.
- Her patch sonrası hedef dosyayı compile eder; hata olursa yedekten geri alır.

Komut:
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_TECH_DEBT_CLEANUP_SAFE_V20_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_technical_debt_cleanup_safe_v20.ps1 -ProjectRoot "C:\bys360\project" -Mode all -OutputRoot "C:\bys360" -MaxPatches 2 -RunCompile
