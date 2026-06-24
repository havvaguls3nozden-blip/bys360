# BYS360 Canlıya Alma Rehberi

## 1. Canlıya alma prensibi

Canlıya alma; kod, veritabanı, görev zamanlayıcı, mail/bildirim ve rollback planı birlikte hazır olduğunda yapılır. Sadece dosya kopyalamak canlıya alma değildir.

## 2. Ön kontrol

```powershell
cd C:\bys360\project
git status --short
python -m compileall app config.py scripts migrations
pytest tests/integration/test_http_core_smoke.py
```

## 3. Yedek

`BACKUP_RUNBOOK.md` uygulanır. DB ve kod yedeği alınmadan canlı güncelleme yapılmaz.

## 4. Migration

Staging veya lokal kopyada denenir. Canlı migration komutu:

```powershell
flask db upgrade
```

## 5. Canlı görev yönetimi

```powershell
Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80" -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
```

Portta eski process kalırsa kontrollü kapatılır.

## 6. Smoke test

- `/login`
- `/healthz`
- Performans ana ekranı
- Personel listesi
- Mesaj/duyuru ekranı
- Anket/destek ekranı
- Yönetici dashboard

## 7. Başarısızlık halinde

- Yeni görev durdurulur.
- Son çalışan kod yedeği geri alınır.
- Migration geri dönüşü gerekiyorsa DB restore planı uygulanır.
- Olay kayıt altına alınır.
