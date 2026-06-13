# BYS360 Quality 10/10 P11-D — Menu Registry Envanteri

Bu paket kod değiştirmez. `app/menu_registry.py` dosyasını parçalamadan önce menü kayıt defteri, domain dağılımı, büyük sabit bloklar ve fonksiyon haritası çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_D_MENU_REGISTRY_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_d_menu_registry_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_d_menu_registry_inventory_v1.json
reports/quality/bys360_quality_10_10_p11_d_menu_registry_inventory_v1.md
```

## Güvenlik

`menu_registry.py` içinde menü anahtarları ve rol görünürlüğü için kullanılan sabitler olabilir. `menu_key` değerleri ve dış public fonksiyon adları değişmemelidir. İlk gerçek refactor sadece bridge yapısıyla planlanmalıdır.
