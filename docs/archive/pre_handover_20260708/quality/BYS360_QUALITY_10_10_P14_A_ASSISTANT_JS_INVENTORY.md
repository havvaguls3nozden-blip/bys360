# BYS360 Quality 10/10 P14-A — Assistant JS Inventory

Bu paket kod değiştirmez. `app/static/js/bys360_assistant_module.js` için envanter çıkarır.

## Amaç

- Dosyadaki fonksiyon/domain dağılımını görmek
- Büyük fonksiyon adaylarını belirlemek
- Fetch/API, CSRF/token, DOM yazma, storage, event listener ve güvenlik hassas satırlarını haritalamak
- P14-B için güvenli split adayları var mı kararına zemin hazırlamak

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_A_ASSISTANT_JS_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p14_a_assistant_js_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 240
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p14_a_assistant_js_inventory_v1.json
reports/quality/bys360_quality_10_10_p14_a_assistant_js_inventory_v1.md
```

## Güvenlik

Bu aşamada kod parçalama yoktur. Asistan JS dosyası ekran zekâsı, DOM davranışı, API çağrıları ve kullanıcı yönlendirme akışını birlikte içerdiği için önce yalnızca envanter çıkarılır.
