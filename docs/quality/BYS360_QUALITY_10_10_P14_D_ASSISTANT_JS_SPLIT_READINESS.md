# BYS360 Quality 10/10 P14-D — Assistant JS Split Readiness

Bu paket kod değiştirmez. P14-C dry-run’da seçilen 12 helper adayının gerçek uygulamaya hazır olup olmadığını ve smoke test planını çıkarır.

## Ne yapar?

- P14-C raporunu okur.
- Seçili 12 adayı global referans, yasaklı bağımlılık, cross-call ve dış kullanım açısından kontrol eder.
- P14-E hazırlanabilir mi kararını üretir.
- Tarayıcı smoke test planı üretir.
- Uygulama koduna dokunmaz.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_D_ASSISTANT_JS_SPLIT_READINESS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p14_d_assistant_js_split_readiness.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p14_d_assistant_js_split_readiness_v1.json
reports/quality/bys360_quality_10_10_p14_d_assistant_js_split_readiness_v1.md
reports/quality/bys360_quality_10_10_p14_d_assistant_js_smoke_plan_v1.md
```

## Güvenlik

P14-D sadece readiness raporu üretir. P14-E yapılacaksa önce checkpoint alınmalı, gerçek uygulama varsayılan dry-run olmalı ve smoke test tamamlanmalıdır.
