# BYS360 Quality 9 CI-safe Scope Discipline HOTFIX V10

Bu paket, CI-safe test kapsamını tekrar güvenli ve deterministik kalite kapısına indirger.

## Neden gerekliydi?

Önceki düzenleme, `ci_safe` marker'ını çok geniş yorumlayarak eski sprint, refactor, uzman inceleme, canlı HTTP ve fixture gerektiren testleri de CI-safe kapısına dahil etti. Bu nedenle pytest artık gerçek çalışıyordu; ancak CI-safe kapısı eski/ayrı faz test borçlarını da topluca çalıştırdığı için kalite sinyali kirleniyordu.

## Yapılanlar

- `tests/conftest.py` artık tüm testleri otomatik `ci_safe` yapmaz.
- CI-safe kapsamı `tests/quality` altındaki deterministik kalite sözleşmesi testleriyle sınırlandı.
- GitHub Actions test komutu `tests/quality -m "ci_safe"` kapsamına çekildi.
- Quality 9 gate bu yeni kapsam disiplinini kontrol eder.
- `app.compat_endpoint_cleanup` geriye uyum modülü korunur.

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY9_CI_SAFE_SCOPE_HOTFIX_V10_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_ci_safe_scope_hotfix_v10.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests
```

## Not

Bu paket, tam test süitindeki legacy/refactor/sprint dokümantasyon borçlarını yok saymaz; onları CI-safe kapısından ayırır. Tam süit ayrı fazlarda temizlenmelidir.
