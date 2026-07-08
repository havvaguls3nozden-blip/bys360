# BYS360 Quality 10/10 P11-E — Effective Menu Envanteri

Bu paket kod değiştirmez. `app/services/settings/effective_menu.py` dosyasını parçalamadan önce fonksiyon/domain envanteri çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_E_EFFECTIVE_MENU_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_e_effective_menu_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_e_effective_menu_inventory_v1.json
reports/quality/bys360_quality_10_10_p11_e_effective_menu_inventory_v1.md
```

## Neden önce envanter?

`effective_menu.py` kişi bazlı menü görünürlüğü, rol matrisi, yetki ve fallback davranışlarını etkileyebilir. Bu dosyada yanlış refactor beyaz sayfa, yanlış menü görünürlüğü veya erişim sapması üretebilir. Bu yüzden ilk adım yalnızca envanterdir.
