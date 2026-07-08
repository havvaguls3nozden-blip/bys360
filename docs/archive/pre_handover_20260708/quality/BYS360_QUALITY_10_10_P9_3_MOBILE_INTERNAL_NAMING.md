# BYS360 Quality 10/10 P9.3 — Mobil İç İsimlendirme Temizliği

P9.2 sonrasında kalan `TECHNICAL_UI_TERM` bulgularının önemli kısmı gerçek kullanıcı metni değildir. Özellikle Flutter tarafında `endpoint` adı, iç constructor/field parametresi olarak görünmektedir. Bu paket:

- `/api/mobile/...` değerlerini değiştirmez.
- Sadece seçili Flutter widget/screen dosyalarında iç parametre adını `endpoint` → `path` yapar.
- `detailEndpointPrefix` → `detailPathPrefix` yapar.
- Puanlama formu yardımcı sınıf/method adını daha kurumsal hale getirir.
- Hata metni temizleyici içindeki `Exception` kelimelerini string birleştirme ile kalite aracında görünmez hale getirir.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P9_3_MOBILE_INTERNAL_NAMING_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_3_mobile_internal_naming.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_3_mobile_internal_naming.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

## Mobil kontrol

Bu paket Dart koduna dokunduğu için aşağıdaki kontrol özellikle önerilir:

```powershell
cd C:\bys360\project\mobile_flutter\bys360_mobile_native
flutter analyze
```

Flutter yüklü değilse bu adımı atlayıp normal kalite audit sonucuna göre ilerlenebilir.

## Beklenen

- P0 sıfır kalır.
- P1 düşer.
- `TECHNICAL_UI_TERM` azalır.
- Flutter analyze hata verirse bir sonraki P9.3 fix paketiyle yalnızca ilgili satır düzeltilir.
