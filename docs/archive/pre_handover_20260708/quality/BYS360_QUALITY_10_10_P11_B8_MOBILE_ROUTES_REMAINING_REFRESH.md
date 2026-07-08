# BYS360 Quality 10/10 P11-B8 — Mobile Routes Remaining Refresh

Bu paket kod değiştirmez. B2-B7 route ayrıştırmalarından sonra `app/api/mobile/routes.py` içinde kalan route fonksiyonlarını yeniden haritalar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_B8_MOBILE_ROUTES_REMAINING_REFRESH_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_b8_mobile_routes_remaining_refresh.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_b8_mobile_routes_remaining_refresh_v1.json
reports/quality/bys360_quality_10_10_p11_b8_mobile_routes_remaining_refresh_v1.md
```

## Amaç

Artık küçük communication/support/survey GET route’larının çoğu ayrıldığı için, kalan route’larda hangi grubun güvenli olduğunu tekrar görmek gerekir. Bu analiz özellikle personel/performance endpointlerine yanlışlıkla riskli müdahale edilmesini engeller.
