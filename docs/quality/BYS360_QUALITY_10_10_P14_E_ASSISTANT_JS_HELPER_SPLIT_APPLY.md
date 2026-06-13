# BYS360 Quality 10/10 P14-E — Assistant JS Helper Split Apply

Bu paket P14-D tarafından hazır görülen 12 küçük helper fonksiyonu için kontrollü split uygular.

## Çok önemli

Varsayılan mod **dry-run** modudur. Kod değiştirmez.

Gerçek uygulama için açıkça `-Apply` verilmelidir.

## Ne yapar?

Dry-run modunda:

- `bys360_assistant_module.js` için güncellenmiş preview üretir.
- `bys360_assistant_helpers_v1.js` helper preview üretir.
- Template script tag güncelleme planını raporlar.
- Hiçbir uygulama dosyasını değiştirmez.

Apply modunda:

- `app/static/js/bys360_assistant_helpers_v1.js` oluşturur.
- `app/static/js/bys360_assistant_module.js` içindeki 12 helper fonksiyonunu wrapper ile değiştirir.
- Assistant module script tag’inden önce helper script tag’i ekler.
- `.quality_backup` altında yedek alır.
- Silme yapmaz.

## Önce checkpoint al

```powershell
cd C:\bys360

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "C:\bys360\project" -DestinationPath "C:\bys360\BYS360_CHECKPOINT_BEFORE_P14_E_ASSISTANT_JS_SPLIT_$stamp.zip" -Force
```

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_E_ASSISTANT_JS_HELPER_SPLIT_APPLY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_e_assistant_js_helper_split_apply.ps1 -ProjectRoot "C:\bys360\project"
```

Dry-run doğruysa gerçek uygulama:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_e_assistant_js_helper_split_apply.ps1 -ProjectRoot "C:\bys360\project" -Apply
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

Tarayıcı smoke test:

1. Ana sayfayı aç, F12 Console’da hata var mı bak.
2. BYS360 Asistan panelini aç/kapat.
3. Asistana “merhaba” yaz.
4. Asistana “bu ekranda ne yapabilirim” yaz.
5. Performans/personel/destek ekranlarında yönlendirme cevabını kontrol et.
6. Hava durumu/yerel cevap akışını tetikle.
7. Console’da `undefined`, `missing function`, CSP veya fetch hatası olmamalı.

## Beklenen

Bu ilk split küçük olduğu için `LARGE_FILE_HARD` hemen düşmeyebilir. Ama güvenli helper dosyası mimarisi kurulmuş olur.
