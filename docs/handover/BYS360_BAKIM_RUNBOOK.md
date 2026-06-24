# BYS360 Bakım Runbook

## Günlük kontrol

- `/login` erişilebilir mi?
- `/healthz` doğru JSON dönüyor mu?
- Son 24 saatte 5xx artışı var mı?
- Mail/bildirim görevleri beklenen zamanda çalışmış mı?
- Loglarda tekrarlı hata var mı?

## Haftalık kontrol

- Yedek alınmış mı?
- Disk doluluk oranı güvenli mi?
- Log rotasyonu çalışıyor mu?
- Bekleyen migration var mı?
- Kullanıcı ve rol değişiklikleri audit log’a düşüyor mu?

## Aylık kontrol

- Güvenli release preflight çalıştırılır.
- Yetki matrisi örnek kullanıcılarla test edilir.
- Performans, personel, iletişim/anket ve destek kritik akışları gözden geçirilir.
- Eski log ve geçici dosyalar temizlenir.

## Bakım komutları

```powershell
python -m compileall app config.py scripts migrations
python scripts\quality\bys360_score100_quality_gate_v1.py --project-root . --mode audit --output-dir reports\quality\score100_quality_gate_v1
```

## Beyaz sayfa ilk müdahale

1. Son log incelenir.
2. İlgili tablo var mı kontrol edilir.
3. Template syntax kontrol edilir.
4. Route yetkisi ve login durumu kontrol edilir.
5. Son değişiklik geri alınarak tekrar denenir.
