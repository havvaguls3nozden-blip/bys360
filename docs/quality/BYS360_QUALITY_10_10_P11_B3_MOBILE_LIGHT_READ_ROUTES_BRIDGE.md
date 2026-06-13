# BYS360 Quality 10/10 P11-B3 — Mobile Light Read Routes Bridge

Bu paket `app/api/mobile/routes.py` içindeki küçük ve düşük riskli GET/read endpointlerini ayrı modüle taşır:

- `mobile_ai_insights`
- `mobile_assistant_suggestions`
- `mobile_settings_summary`

## Neye dokunmaz?

- Auth/token/password endpointleri
- Personel oluşturma
- POST/PUT/PATCH/DELETE işlemleri
- Commit/rollback yapan fonksiyonlar
- Büyük personel/asistan route fonksiyonları

## Uygulama

```powershell
cd C:\bys360

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "C:\bys360\project" -DestinationPath "C:\bys360\BYS360_QUALITY_CHECKPOINT_BEFORE_P11_B3_MOBILE_LIGHT_READ_$stamp.zip" -Force

cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_B3_MOBILE_LIGHT_READ_ROUTES_BRIDGE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_b3_mobile_light_read_routes_bridge.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_b3_mobile_light_read_routes_bridge.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

## Beklenen

- P0 sıfır kalır.
- `routes.py` biraz daha küçülür.
- Büyük dosya uyarısı hemen düşmeyebilir; kontrollü route ayrıştırma devam eder.
