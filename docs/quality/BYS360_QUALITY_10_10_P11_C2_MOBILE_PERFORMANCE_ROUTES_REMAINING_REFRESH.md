# BYS360 Quality 10/10 P11-C2 — Mobile Performance Routes Remaining Refresh

Bu paket kod değiştirmez. P11-C1 sonrasında `app/api/mobile/performance_routes.py` içinde kalan performans route fonksiyonlarını yeniden haritalar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_C2_MOBILE_PERFORMANCE_ROUTES_REMAINING_REFRESH_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_c2_mobile_performance_routes_remaining_refresh.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_c2_mobile_performance_routes_remaining_refresh_v1.json
reports/quality/bys360_quality_10_10_p11_c2_mobile_performance_routes_remaining_refresh_v1.md
```

## Amaç

C1 sonrası güvenli düşük riskli GET endpoint kalıp kalmadığını görmek. Eğer kalanlar puanlama/onay/yayın/POST tarafına kaydıysa bu dosyada durmak daha güvenlidir.
