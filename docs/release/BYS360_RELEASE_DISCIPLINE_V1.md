# BYS360 V4 Release Discipline V1

Amaç: BYS360 teslim ziplerinin doğrudan klasör sıkıştırmasıyla değil, sadece `scripts/release/build_bys360_safe_release.py` çıktısıyla üretilmesini sağlamak.

Bu paket:

- `build_bys360_safe_release.py` dosyasını filtreli release builder haline getirir.
- `.gitignore` içine release hijyen bloğu ekler.
- `instance/`, `logs/`, `.venv/`, `.git/`, `.env`, SQLite, DB, log, backup ve anahtar dosyalarının release zipine girmesini engeller.
- Release üretiminden sonra bağımsız zip audit çalıştırır.

Kullanım:

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_V4_RELEASE_DISCIPLINE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_v4_release_discipline_v1.ps1 -ProjectRoot "C:\bys360\project" -OutputRoot "C:\bys360\releases" -Mode all -RunCompile
```

Başarı ölçütü:

- Komut sonunda `TEMİZ RELEASE HAZIR` görünmeli.
- Rapor JSON içinde `ok: true` olmalı.
- Oluşan zip içinde `.env`, `.venv`, `instance/`, `logs/`, `.git/`, `*.sqlite3`, `*.log` bulunmamalı.
