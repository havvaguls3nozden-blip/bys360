# BYS360 Güvenli Release ve Secret Temizliği V1.1

Bu runbook, geliştirme klasöründen güvenli release paketi üretmek için kullanılır.

## Amaç

- Gerçek `.env` dosyalarının release paketine girmesini engellemek.
- `.env.example` dosyasını yalnızca örnek anahtarlarla tutmak.
- Sabit ilk şifre kullanımını kaldırmak.
- Secret taramasında gate araçlarının kendi imzalarını yanlışlıkla bulmasını engellemek.

## Kullanım

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\security\repair_bys360_secure_release_secret_clean_v1_1.ps1 -ProjectRoot "C:\bys360\project"
python -m compileall app config.py scripts
powershell -ExecutionPolicy Bypass -File .\scripts\security\check_bys360_secure_release_secret_clean_v1_1.ps1 -ProjectRoot "C:\bys360\project"
powershell -ExecutionPolicy Bypass -File .\scripts\windows\build_bys360_secure_release_v1_1.ps1 -ProjectRoot "C:\bys360\project"
```

## Not

Canlı Sentry DSN ve canlı veritabanı parolası `.env.example` içine yazılmaz. Gerçek değerler sadece sunucudaki `.env` içinde tutulur.
