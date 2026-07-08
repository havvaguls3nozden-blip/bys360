# BYS360 Quality 10/10 P11-C1 — Mobile Performance Read Routes Bridge

Bu paket `app/api/mobile/performance_routes.py` içindeki küçük ve düşük riskli GET/read performans endpointlerini ayrı modüle taşır.

## Taşınan endpoint fonksiyonları

- `mobile_performance_manager_view_v2852`
- `mobile_performance_periods`
- `mobile_performance_weights`
- `mobile_performance_tasks`
- `mobile_performance_manager_tasks`
- `mobile_performance_categories`
- `mobile_performance_reminders`
- `mobile_performance_in_period_note_options_v2853`

## Özellikle dokunulmayan kritik alan

- `mobile_performance_task_score_submit`
- Puanlama / score submit
- Onay / yayın
- POST / PUT / PATCH / DELETE
- commit / rollback

## Uygulama

```powershell
cd C:\bys360

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "C:\bys360\project" -DestinationPath "C:\bys360\BYS360_QUALITY_CHECKPOINT_BEFORE_P11_C1_MOBILE_PERFORMANCE_READ_$stamp.zip" -Force

cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_C1_MOBILE_PERFORMANCE_READ_ROUTES_BRIDGE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_c1_mobile_performance_read_routes_bridge.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_c1_mobile_performance_read_routes_bridge.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

## Beklenen

- P0 sıfır kalır.
- `performance_routes.py` yaklaşık 1600 satır seviyesine iner.
- Büyük dosya uyarısı hemen düşmeyebilir; kritik puanlama fonksiyonu yerinde kalır.
