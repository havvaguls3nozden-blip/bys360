# BYS360 Quality 10/10 P9.2 — Güvenli Teknik Dil False-Positive Temizliği

P9.1 sonrasında kalan `TECHNICAL_UI_TERM` kayıtlarının önemli kısmı gerçek kullanıcı metni değil; test cümleleri, dahili sabitler, filtre listeleri, güvenli bağlantı adları ve JS/Dart iç değişkenleridir.

Bu paket:

- API/rota adreslerini bozmaz.
- `endpoint:` gibi mobil named-argument satırlarına dokunmaz.
- Yalnızca güvenli test/metin/filtre/yerel değişken satırlarını düzenler.
- Değişikliklerden önce `.quality_backup` altında yedek alır.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P9_2_TECHNICAL_UI_SAFE_FALSE_POSITIVE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_2_technical_ui_safe_false_positive.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_2_technical_ui_safe_false_positive.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p9_technical_ui_terms.ps1 -ProjectRoot "C:\bys360\project" -Limit 260 -ShowLines
```

Beklenen:

- P0 sıfır kalır.
- P1 düşer.
- `TECHNICAL_UI_TERM` azalır.
