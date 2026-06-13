# BYS360 Quality 10/10 P10.1 — Güvenli Kalan Teknik İsimlendirme

P10 triage sonucu kalan 59 P1 içinde yalnızca 6 kayıt `TEXT_OR_SCOPE_REVIEW` olarak ayrılmıştır. Bunların 5'i güvenli iç isimlendirme düzeltmesidir.

Bu paket:

- `_threadsEndpoint` → `_threadsPath`
- `_buildEndpointAttempts` → `_buildPathAttempts`
- `mobile_scoring_form_endpoint.dart` → `mobile_scoring_form_path.dart`
- `performance_scoring_form_screen.dart` import yolunu günceller
- Gerçek API adreslerini değiştirmez
- `ApiException` sınıfına dokunmaz

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P10_1_SAFE_REMAINING_TECH_NAMING_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p10_1_safe_remaining_tech_naming.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p10_1_safe_remaining_tech_naming.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
cd C:\bys360\project

python -m compileall app scripts

cd C:\bys360\project\mobile_flutter\bys360_mobile_native
flutter analyze

cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 120
```

Beklenen:

- P0 sıfır kalır.
- Flutter analyze temiz kalır.
- P1 59'dan birkaç puan daha düşebilir.
- Kalanlar ağırlıkla false-positive, refactor planı ve süreç planıdır.
