# BYS360 Mobile Contract Runtime Import Fix V2

Amaç: V1 sonrası `routes.py` 300 satır altına inmişken runtime importta kırılan `require_mobile_user` export'unu geri vermek.

Bu paket yeni endpoint veya yeni özellik eklemez. Sadece `performance_routes.py` tarafından kullanılan mobil auth helper'ın ince facade `routes.py` üzerinden tekrar erişilebilir olmasını sağlar.

Beklenen sonuç:
- `routes.py` 300 satır altında kalır.
- `routes.py` içinde route decorator bulunmaz.
- Domain route decorator sayısı 24 kalır.
- `from .routes import require_mobile_user` artık çalışır.
- Mobil real API startup ImportError vermez.

Komutlar:

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MOBILE_CONTRACT_RUNTIME_IMPORT_FIX_V2_OVERLAY_FLAT.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_mobile_contract_runtime_import_fix_v2.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_mobile_contract_runtime_import_fix_v2.ps1 -ProjectRoot "C:\bys360\project" -Mode fix-safe -RunCompile
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_mobile_contract_runtime_import_fix_v2.ps1 -ProjectRoot "C:\bys360\project" -Mode verify -RunCompile
```
