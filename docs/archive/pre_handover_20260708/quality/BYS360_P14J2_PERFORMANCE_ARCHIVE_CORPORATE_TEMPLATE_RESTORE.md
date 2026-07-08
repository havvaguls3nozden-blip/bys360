# BYS360 P14J2 — Performans Arşivi Kurumsal Template Restore

P14J sade fallback template tasarımı geçici olarak sayfayı açtırdı fakat gerçek Geçmiş Karne Arşivi tasarım hissini bozdu. Bu paket sadece o template’i kurumsal performans yüzeyiyle değiştirir.

## Ne yapar?

- Sadece `app/templates/performance/archive/index.html` dosyasını değiştirir.
- Route, servis, asistan, base.html ve kalite kapanış dosyalarına dokunmaz.
- Mevcut route değişkenleriyle çalışır:
  - `rows`
  - `summary`
  - `years`
  - `selected_year`
  - `q`
  - `can_manage_archive`
  - `visibility_context`
  - `display_name`
- `bys360_performance_surfaces_elite_v2.css` yüzeyiyle uyumlu kurumsal arşiv ekranı oluşturur.
- P14J’nin sade fallback görünümünü kaldırır.

## Kullanım

Çalışan Waitress ekranında `Ctrl + C`.

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PERFORMANCE_ARCHIVE_TEMPLATE_CORPORATE_RESTORE_P14J2_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\restore_bys360_p14j2_performance_archive_corporate_template.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\restore_bys360_p14j2_performance_archive_corporate_template.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_p14j2_performance_archive_corporate_template.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts
```

Sonra başlat:

```powershell
python -m waitress --listen=0.0.0.0:8000 --threads=12 --no-log-socket-errors wsgi:app
```

Tarayıcıda `Ctrl + F5` yaparak `/performans/gecmis-karne-arsivi` ekranını tekrar aç.
