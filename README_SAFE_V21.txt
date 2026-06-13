BYS360_TECH_DEBT_CLEANUP_SAFE_V21

Amaç:
- Kod değiştirmez.
- V20 sonrası otomatik/safeish exception adayı kalmadığını doğrular.
- Kalan rollback/db.rollback/control-flow bloklarını manuel risk raporu olarak listeler.
- .env/local SQLite dosyalarının SAFE V17 .gitignore koruması altında olduğunu doğrular.
- Compile ve Quality9 yeşil mi kontrol eder.

Komut:
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_TECH_DEBT_CLEANUP_SAFE_V21_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_technical_debt_cleanup_safe_v21.ps1 -ProjectRoot "C:\bys360\project" -Mode all -OutputRoot "C:\bys360" -RunCompile
