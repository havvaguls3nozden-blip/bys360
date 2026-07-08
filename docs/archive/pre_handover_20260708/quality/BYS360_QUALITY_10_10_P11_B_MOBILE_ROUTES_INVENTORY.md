# BYS360 Quality 10/10 P11-B — Mobile Routes Envanteri

Bu paket kod değiştirmez. `app/api/mobile/routes.py` dosyasını domain bazlı parçalamadan önce route, fonksiyon, risk ve modül aday haritası çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_B_MOBILE_ROUTES_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_b_mobile_routes_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_b_mobile_routes_inventory_v1.json
reports/quality/bys360_quality_10_10_p11_b_mobile_routes_inventory_v1.md
```

## Güvenlik

Mobil route dosyaları doğrudan API davranışını etkiler. URL path, auth/token davranışı, JSON cevap formatı ve Flutter app beklentileri korunmadan taşıma yapılmamalıdır. Bu yüzden ilk adım yalnızca envanterdir.
