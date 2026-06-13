# BYS360 P14J — Performans Arşivi Template Restore

Bu paket sadece eksik template dosyasını geri ekler:

```text
app/templates/performance/archive/index.html
```

## Hata

```text
jinja2.exceptions.TemplateNotFound: performance/archive/index.html
```

## Ne yapar?

- Route veya servis koduna dokunmaz.
- Asistan dosyalarına dokunmaz.
- `performance/archive/index.html` dosyasını sade, kurumsal ve güvenli fallback template olarak ekler.
- Template değişkenleri eksik olsa bile patlamayacak şekilde `default` kullanır.
- Jinja syntax kontrolü yapar.

## Kullanım

Çalışan Waitress ekranında `Ctrl + C`.

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PERFORMANCE_ARCHIVE_TEMPLATE_RESTORE_P14J_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\restore_bys360_p14j_performance_archive_template.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\restore_bys360_p14j_performance_archive_template.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_p14j_performance_archive_template.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts
```

Sonra uygulamayı tekrar başlat:

```powershell
python -m waitress --listen=0.0.0.0:8000 --threads=12 --no-log-socket-errors wsgi:app
```

Tarayıcıda arşiv ekranını yeniden aç.
