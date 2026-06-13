# BYS360 Quality 10/10 — P1 Sessiz Except Loglama Notları

Bu paket P0 denetimindeki `SILENT_EXCEPT_PASS` bulgularını kapatmak için hazırlanmıştır.

## Amaç

`except: pass` veya `except Exception: pass` gibi sessiz hata yutma blokları canlı sistemde gizli arıza üretir. Bu paket, bu blokları davranışı bozmadan loglanabilir hale getirir.

Örnek dönüşüm:

```python
except Exception:
    pass
```

şuna dönüşür:

```python
except Exception:
    logger.exception("BYS360 kalite denetimi: sessiz except bloğu loglandı: app/example.py:123")
```

## Güvenlik

- Hata yine yutulur; sistem davranışı değiştirilmez.
- Sadece sessiz kalan hata artık loga düşer.
- Değişen dosyalar `.quality_backup` altında yedeklenir.
- Sonrasında mutlaka `python -m compileall app scripts` çalıştırılmalıdır.

## Sıra

1. Repair scripti çalıştırılır.
2. `compileall` çalıştırılır.
3. Kalite denetimi önce `-FailOn never` ile tekrar alınır.
4. P0 sıfıra yaklaşınca `-FailOn P0` aktif kalite kapısı olarak kullanılır.
