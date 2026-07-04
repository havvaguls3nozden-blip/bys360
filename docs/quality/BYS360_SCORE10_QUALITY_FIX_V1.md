# BYS360 Score 10 Quality Fix V1

Bu paket, son kalite analizinde görülen **teslim/paket hijyeni**, **taşınabilir SQLite yolu**, **tanımsız isim riski** ve **kalite kapısı eksikliği** başlıklarını hedefler.

## Düzeltilenler

1. `app/services/cic/misc_context.py`
   - `send_email` ve `create_mail_log` güvenli import edildi.
   - Mail servisi yüklenemezse ekran düşmez, sağlık kontrolü uyarı üretir.

2. `app/api/mobile/services/performance_task_helpers.py`
   - `_DONE` tamamlanmış statü seti helper içine alındı.
   - Helper modülü tek başına yüklendiğinde `NameError/F821` riski giderildi.

3. `config.py`
   - `DATABASE_URL` için platform bağımsız normalizasyon eklendi.
   - Windows'a özel `sqlite:///C:/...` yolu Linux/CI ortamında `instance/bys360_local_dev.sqlite3` yoluna çevrilir.

4. `.env.example` ve `.releaseignore`
   - `.env.example` taşınabilir yerel SQLite örneğine çekildi.
   - Temiz teslim paketinden `.env`, `.venv`, `.git`, cache, log, DB, backup ve runtime dosyaları dışlanır.

5. Kalite ve paketleme scriptleri
   - `scripts/quality/check_bys360_score10_quality_gate_v1.py`
   - `scripts/packaging/build_bys360_clean_release_v1.py`
   - `scripts/windows/repair_bys360_score10_quality_v1.ps1`

## Kullanım

Yerelde önce audit:

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score10_quality_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
```

Temiz teslim paketi üretmek için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score10_quality_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode clean-package -OutputRoot "C:\bys360\releases"
```

Gerçek teslim kapısını `.env` dahil yerel sırları hata sayarak çalıştırmak için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score10_quality_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode gate
```

## Not

Bu paket canlı veritabanına, canlı `.env` dosyasına veya mevcut kullanıcı verilerine dokunmaz. Temiz paket üretirken bu dosyaları dışarıda bırakır.
