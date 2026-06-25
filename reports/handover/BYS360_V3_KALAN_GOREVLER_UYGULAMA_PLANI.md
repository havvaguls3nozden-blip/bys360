# BYS360 V3 Kalan Görevler Uygulama Planı

Bu paket, 25 Haziran 2026 tarihli V3 karşılaştırma raporundaki hızlı kazanım maddelerini uygular.

## Uygulanan maddeler

1. `bys360-ci.yml` içine integration + architecture test adımı eklendi.
2. `bys360-ci.yml` içine `mypy app/services` adımı eklendi.
3. `CONTRIBUTING.md` içine yeni geliştirici onboarding bölümü eklendi.
4. `docker/nginx.conf.example` eklendi.
5. `build_bys360_secure_release_v1_5.py` release dışlama kuralları `.git`, `.venv`, `backups`, `archive`, `payload`, `overlay_payload`, `logs`, `instance`, `uploads` için sertleştirildi.
6. `scripts/windows/build_bys360_secure_release_and_preflight_v1.ps1` eklendi. Release üretimi ve preflight tek komutta çalışır.

## Yerelde uygulama

```powershell
cd C:ys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_V3_REPORT_FIXES_OVERLAY.zip" -DestinationPath "C:ys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windowsuild_bys360_secure_release_and_preflight_v1.ps1 -ProjectRoot "C:ys360\project"
```

## Sonraki sıra

- Aktif script azaltma: yeni script üretmeme kuralı uygulanacak; mevcut tekil scriptler raporlanıp `scripts/quality`, `scripts/security`, `scripts/release` altında birleştirilecek.
- God-object bölme: önce `app/admin/ops_routes.py`, sonra `app/admin/ai_routes.py`, sonra `app/admin/routes.py` parçalara ayrılacak. Her bölme öncesi mimari test yazılacak.
