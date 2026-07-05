# BYS360 Teknik Borç Faz 1 Runbook

Bu fazın amacı canlı davranışı değiştirmek değil, proje klasörünü ölçmek ve temiz kaynak paketini güvenli biçimde üretmektir.

## Faz 1 kapsamı

- `.env` temiz kaynak paketine alınmaz.
- `.git` geçmişi temiz kaynak paketine alınmaz.
- `.venv`, Python cache, Ruff cache, Flutter build cache temiz kaynak paketine alınmaz.
- `logs`, `instance`, yerel SQLite veritabanı, nested release zipleri temiz kaynak paketine alınmaz.
- Kod davranışı değiştirilmez.
- Mevcut proje klasörü silinmez.

## 1. Audit çalıştırma

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_TECH_DEBT_PHASE1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit -OutputRoot "C:\bys360\reports\tech_debt_phase1"
```

## 2. Temiz kaynak kopyası üretme

Audit raporu mantıklıysa:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase1.ps1 -ProjectRoot "C:\bys360\project" -Mode clean-copy -OutputRoot "C:\bys360\reports\tech_debt_phase1"
```

## 3. Kontrol

Üretilen temiz kaynakta şu dosyalar olmamalıdır:

- `.env`
- `.git/`
- `.venv/`
- `logs/`
- `instance/*.sqlite3`
- `dist_secure/*.zip`
- `archive/`
- `backups/`
- `.dart_tool/`
- `.gradle/`
- `__pycache__/`
- `.pyc`

## 4. Sonraki faza geçiş şartı

Faz 2'ye geçmeden önce:

1. Temiz kaynak ZIP üretilmiş olmalı.
2. Manifest oluşmuş olmalı.
3. Temiz kaynakta `.env` ve yerel DB bulunmamalı.
4. Mevcut proje klasörü silinmemiş olmalı.
5. Git çalışma alanı temiz olmalı veya değişiklikler ayrı branch/tag altında tutulmalı.
