BYS360 Route Refactor Inventory P1 V2.17.5

Amaç:
- Refactor yapmadan önce büyük route dosyalarını, phase isimli aktif dosyaları ve bakım scriptlerini envantere almak.
- Bu paket uygulama dosyalarını değiştirmez.

Komutlar:
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_route_refactor_inventory_p1_v2_17_5.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_route_refactor_inventory_p1_v2_17_5.ps1 -ProjectRoot "C:\bys360\project" -Mode health
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_route_refactor_inventory_p1_v2_17_5.ps1 -ProjectRoot "C:\bys360\project" -Mode all

Rapor:
reports\quality\bys360_route_refactor_inventory_p1_v2_17_5_report.md
