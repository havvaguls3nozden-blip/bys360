# BYS360 Quality 9 Compat Endpoint Cleanup HOTFIX V9

Bu paket, CI-safe pytest collection aşamasında eksik görünen `app.compat_endpoint_cleanup` modülünü geriye uyum katmanı olarak ekler.

## Kapsam

- `app/compat_endpoint_cleanup.py`
- `scripts/windows/repair_bys360_quality9_compat_endpoint_cleanup_hotfix_v9.ps1`

## Amaç

`tests/test_compat_redirects.py` dosyasının beklediği `_soft_redirect(...)` yardımcısını yeniden sağlar. Yardımcı, eski/taşınmış endpoint çağrılarını Flask `url_for` ve `redirect` ile yeni endpoint'e yönlendirir.

## Çalıştırma

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY9_COMPAT_ENDPOINT_CLEANUP_HOTFIX_V9_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_compat_endpoint_cleanup_hotfix_v9.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests
```
