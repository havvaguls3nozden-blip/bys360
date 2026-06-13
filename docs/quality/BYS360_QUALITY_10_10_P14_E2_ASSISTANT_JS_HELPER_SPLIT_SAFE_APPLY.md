# BYS360 Quality 10/10 P14-E2 — Assistant JS Helper Split Safe Apply

P14-E dry-run `HELPER_JS_SANITY_FAILED` verdiyse bu paket kullanılmalıdır.

## Neden P14-E2?

P14-E’deki JS denge kontrolü regex literal içindeki parantezleri gerçek parantez sanabilir. P14-E2 regex-aware sanity kontrolü kullanır ve adayları tek tek doğrular. Sorunlu aday olursa otomatik dışarıda bırakır.

## Varsayılan davranış

Varsayılan mod **dry-run** modudur. Kod değiştirmez.

Gerçek uygulama için açıkça `-Apply` verilmelidir.

## Önce checkpoint

```powershell
cd C:\bys360

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "C:\bys360\project" -DestinationPath "C:\bys360\BYS360_CHECKPOINT_BEFORE_P14_E2_ASSISTANT_JS_SPLIT_$stamp.zip" -Force
```

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_E2_ASSISTANT_JS_HELPER_SPLIT_SAFE_APPLY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_e2_assistant_js_helper_split_safe_apply.ps1 -ProjectRoot "C:\bys360\project"
```

Dry-run doğruysa gerçek uygulama:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_e2_assistant_js_helper_split_safe_apply.ps1 -ProjectRoot "C:\bys360\project" -Apply
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

Tarayıcı smoke test:

1. Ana sayfayı aç, F12 Console’da hata yok.
2. BYS360 Asistan panelini aç/kapat.
3. “merhaba” sor.
4. “bu ekranda ne yapabilirim” sor.
5. Performans/personel/destek ekranlarında yönlendirme cevabını kontrol et.
6. Hava durumu/yerel cevap akışını test et.
7. Console’da undefined, missing function, CSP veya fetch hatası olmamalı.
