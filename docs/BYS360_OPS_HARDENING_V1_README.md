# BYS360 Operasyonel Sağlamlaştırma V1

Bu overlay, kıdemli kod incelemesinde belirtilen **Dockerfile yok**, **CI/CD eksik**, **.env/example standardı zayıf**, **print/except ölçümü yok** başlıklarını kapatmak için hazırlanmıştır.

## Eklenenler

- `Dockerfile` — Python 3.12, non-root kullanıcı, healthcheck, Gunicorn.
- `.dockerignore` — `.env`, `.venv`, log, backup, overlay ve paket artefaktlarını imaj dışında bırakır.
- `docker-compose.yml` — local/pilot Postgres + Redis + web servis omurgası.
- `.env.docker.example` — secretsiz Docker ortam şablonu.
- `docker/gunicorn.conf.py` — üretim process ayarları.
- `docker/entrypoint.sh` — opsiyonel migration/compile kontrollü entrypoint.
- `.github/workflows/bys360-ci.yml` — compile, ops audit, ruff syntax/import sanity, dependency audit.
- `scripts/quality/bys360_ops_audit.py` — Docker/CI/env/print/except/syntax denetim raporu.
- `scripts/windows/repair_bys360_ops_hardening_v1.ps1` — Windows yerel uygulama ve kontrol scripti.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_OPS_HARDENING_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ops_hardening_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Docker local test

Önce `.env.docker.local` dosyasını kontrol edin. Script yoksa `.env.docker.example` üzerinden oluşturur.

```powershell
docker compose build
docker compose up -d
docker compose ps
```

Sağlık kontrolü:

```powershell
curl http://127.0.0.1:8000/health
# veya
curl http://127.0.0.1:8000/healthz
```

## Canlı için dikkat

- `.env.docker.local` canlı pakete konmaz.
- Gerçek `SECRET_KEY`, `DATABASE_URL`, `SENTRY_DSN` ve mail bilgileri yalnızca sunucu/gizli ortam yönetiminde tutulur.
- Docker local örneğinde `sslmode=disable` sadece yerel Postgres içindir. Canlı dış veritabanında `sslmode=require` kullanılmalıdır.
- `except Exception` temizliği tek seferde otomatik dönüştürülmeyecek; rapordaki öncelik sırasına göre dosya dosya azaltılacaktır.

## Beklenen rapor

Script sonunda şu raporlar oluşur:

- `reports/quality/BYS360_OPS_HARDENING_V1_REPORT.md`
- `reports/quality/BYS360_OPS_HARDENING_V1_REPORT.json`

Bu rapor, sonraki fazda print ve broad exception azaltma bütçesinin temel ölçümü olarak kullanılacaktır.
