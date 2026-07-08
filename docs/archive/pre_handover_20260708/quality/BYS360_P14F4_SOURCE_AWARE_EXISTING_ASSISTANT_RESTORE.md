# BYS360 P14F4 — Kaynak Kontrollü Mevcut Asistan Geri Getirme

Bu paket yeni asistan yapmaz. Kaynak dosyaya bakarak P14-E2 öncesindeki mevcut `bys360_assistant_module.js` dosyasını geri alır.

## Kaynakta tespit edilen durum

- Güncel `base.html` içinde `bys360_assistant_helpers_v1.js` ve `bys360_assistant_module.js` birlikte yükleniyor.
- Güncel `bys360_assistant_module.js` içinde `window.BYS360AssistantHelpersV1...` wrapper referansları var.
- P14-E2 öncesi `.quality_backup` içindeki eski `bys360_assistant_module.js` 6203 satır ve helper wrapper referansı içermiyor.
- Eski `base.html` script versiyonu aynı kaldığı için tarayıcı cache nedeniyle asistan gelmeyebilir.

## Ne yapar?

- En uygun eski asistan JS yedeğini `.quality_backup` içinden seçer.
- `bys360_assistant_module.js` dosyasını bu eski kaynakla değiştirir.
- `base.html` içinden helper script satırını kaldırır.
- `base.html` içinde root div ve module script satırını garanti eder.
- Module script URL’ine `?v=assistant-restore-p14f4-existing` cache-bust ekler.
- Helper dosyasını silmez, `.disabled_by_p14f4` olarak yeniden adlandırır.
- Uygulama öncesi mevcut dosyaları `.quality_backup/p14f4_source_aware_assistant_restore_*` altına yedekler.

## Kullanım

Çalışan Waitress ekranında `Ctrl + C`.

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_ASSISTANT_SOURCE_AWARE_RESTORE_P14F4_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\restore_bys360_p14f4_source_aware_existing_assistant.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\restore_bys360_p14f4_source_aware_existing_assistant.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_p14f4_source_aware_existing_assistant.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts
```

Sonra başlat:

```powershell
python -m waitress --listen=0.0.0.0:8000 --threads=12 --no-log-socket-errors wsgi:app
```

Tarayıcıda `Ctrl + F5` veya gizli pencere kullan.
