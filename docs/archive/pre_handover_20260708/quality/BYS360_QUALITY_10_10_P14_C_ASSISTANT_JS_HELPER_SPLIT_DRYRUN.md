# BYS360 Quality 10/10 P14-C — Assistant JS Helper Split Dry-Run

Bu paket kod değiştirmez. P14-B’de bulunan düşük riskli yardımcı fonksiyonlar için sadece dry-run split planı üretir.

## Ne yapar?

- `app/static/js/bys360_assistant_module.js` dosyasını değiştirmez.
- `app/static/js/bys360_assistant_helpers_v1.js` dosyasını oluşturmaz.
- Sadece raporlarda helper dosyası preview metni üretir.
- API/fetch, CSRF/token, DOM yazma, event listener, storage ve asistan/chat akışı içeren fonksiyonları taşıma planına almaz.
- İlk planı küçük tutar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_C_ASSISTANT_JS_HELPER_SPLIT_DRYRUN_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p14_c_assistant_js_helper_split_dryrun.ps1 -ProjectRoot "C:\bys360\project" -MaxFunctions 12
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p14_c_assistant_js_helper_split_dryrun_v1.json
reports/quality/bys360_quality_10_10_p14_c_assistant_js_helper_split_dryrun_v1.md
reports/quality/bys360_quality_10_10_p14_c_assistant_helpers_v1_preview.js
```

## Güvenlik

Bu aşamada gerçek split yoktur. P14-D yapılırsa önce checkpoint, sonra seçilen fonksiyonların elle kontrolü, ardından smoke test planı gerekir.
