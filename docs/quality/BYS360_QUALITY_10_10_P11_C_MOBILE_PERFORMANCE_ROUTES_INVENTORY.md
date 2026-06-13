# BYS360 Quality 10/10 P11-C — Mobile Performance Routes Envanteri

Bu paket kod değiştirmez. `app/api/mobile/performance_routes.py` dosyasını parçalamadan önce route, fonksiyon, risk ve domain haritası çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_C_MOBILE_PERFORMANCE_ROUTES_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_c_mobile_performance_routes_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_c_mobile_performance_routes_inventory_v1.json
reports/quality/bys360_quality_10_10_p11_c_mobile_performance_routes_inventory_v1.md
```

## Güvenlik

Performans puanlama, değerlendirme kaydetme, onay, yayın ve POST işlemleri kritik olduğundan ilk aşama yalnızca envanterdir.
