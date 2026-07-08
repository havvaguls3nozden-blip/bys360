# BYS360 Quality 10/10 P11-H — Performans CSS Envanteri

Bu paket kod değiştirmez. `app/static/css/performance_phase3.css` dosyasını bölmeden önce güvenli envanter çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_H_CSS_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_h_css_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_h_css_inventory_v1.json
reports/quality/bys360_quality_10_10_p11_h_css_inventory_v1.md
```

## Neden önce envanter?

CSS dosyası görsel cascade sırasına duyarlıdır. Doğrudan parçalama yerine önce selector, media query ve blok türleri görülmelidir. Sonraki P11-H1 paketi, bu envantere göre dry-run destekli güvenli wrapper split hazırlayacaktır.
