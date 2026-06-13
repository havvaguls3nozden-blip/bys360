# BYS360 Quality 10/10 P14-F — Assistant JS Split Verification

Bu paket kod değiştirmez. P14-E2 apply sonrasında doğrulama yapar.

## Ne yapar?

- `bys360_assistant_helpers_v1.js` oluşmuş mu kontrol eder.
- `bys360_assistant_module.js` içinde 12 helper wrapper var mı kontrol eder.
- `base.html` içinde helper script tag’i module script tag’inden önce mi kontrol eder.
- Clean audit ve P7 P1 analizini çalıştırır.
- P1 artışının hangi rule’dan geldiğini delta olarak raporlar.
- Tarayıcı smoke test planı üretir.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_F_ASSISTANT_JS_SPLIT_VERIFICATION_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p14_f_assistant_js_split_verification.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p14_f_assistant_js_split_verification_v1.json
reports/quality/bys360_quality_10_10_p14_f_assistant_js_split_verification_v1.md
```

## Beklenen

```text
verification_ok=True
P0=0
helper_loaded_before_module=True
missing_wrapper_count=0
missing_export_count=0
```

P1 artışı varsa bu rapor hangi rule’dan geldiğini gösterir.
