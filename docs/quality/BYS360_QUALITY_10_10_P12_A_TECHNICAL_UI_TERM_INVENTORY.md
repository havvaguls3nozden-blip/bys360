# BYS360 Quality 10/10 P12-A — Technical UI Term Inventory

Bu paket kod değiştirmez. Kalan `TECHNICAL_UI_TERM` P1 bulgularını dosya, satır, metin, karar türü ve güvenli düzeltme adayı olarak raporlar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P12_A_TECHNICAL_UI_TERM_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p12_a_technical_ui_term_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 200
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p12_a_technical_ui_term_inventory_v1.json
reports/quality/bys360_quality_10_10_p12_a_technical_ui_term_inventory_v1.md
```

## Güvenlik

Bu paket dosya değiştirmez. P12-B yalnızca kullanıcıya görünen string literal veya HTML görünür metinleri için hazırlanmalıdır. Kod sembolleri, importlar, route/url/id/name/data-* alanları, API client, controller, provider, contract gibi mimari isimler otomatik değiştirilmemelidir.
