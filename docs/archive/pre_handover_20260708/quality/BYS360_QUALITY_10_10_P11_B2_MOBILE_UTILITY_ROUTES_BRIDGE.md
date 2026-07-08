# BYS360 Quality 10/10 P11-B2 — Mobile Utility Routes Bridge

Bu paket `app/api/mobile/routes.py` içindeki düşük riskli utility GET endpointlerini ayrı modüle taşır:

- `mobile_health`
- `mobile_kpi_goals`

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
Compress-Archive -Path "C:\bys360\project" -DestinationPath "C:\bys360\BYS360_QUALITY_CHECKPOINT_BEFORE_P11_B2_MOBILE_UTILITY_$stamp.zip" -Force

cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_B2_MOBILE_UTILITY_ROUTES_BRIDGE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_b2_mobile_utility_routes_bridge.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_b2_mobile_utility_routes_bridge.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

Opsiyonel mobil smoke:

```powershell
# Uygulama çalışıyorsa:
# Invoke-WebRequest http://127.0.0.1:8000/api/mobile/health
# Invoke-WebRequest http://127.0.0.1:8000/api/mobile/kpi/goals
```

## Beklenen

- P0 sıfır kalır.
- `routes.py` birkaç satır küçülür.
- Büyük dosya uyarısı hemen düşmeyebilir; bu ilk güvenli route bridge adımıdır.
