# BYS360 Quality 10/10 P11-F — Settings Template Envanteri

Bu paket kod değiştirmez. `app/templates/settings.html` dosyasını parçalamadan önce güvenli envanter çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_F_SETTINGS_TEMPLATE_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_f_settings_template_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_f_settings_template_inventory_v1.json
reports/quality/bys360_quality_10_10_p11_f_settings_template_inventory_v1.md
```

## Neden önce envanter?

`settings.html` içinde rol matrisi, kişi bazlı menü görünürlüğü, güvenlik ayarları ve kaydetme davranışları olabilir. Form, input, name/id, CSRF ve script/fetch davranışları korunmalıdır. Bu yüzden ilk aşama yalnızca envanterdir.
