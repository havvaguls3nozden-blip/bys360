# BYS360 P2A Mobile Pytest Contract Gate V3

Bu overlay mobil API domain split sonrası sözleşme kapısını kalıcı hale getirir.

- `app/api/mobile/routes.py` facade seviyesinde kalmalı.
- Mobil endpoint sayısı 24 olarak korunmalı.
- Domain dosyaları eksiksiz olmalı.
- Duplicate route decorator olmamalı.
- Pytest kuruluysa gerçek pytest çalışır.
- Pytest yoksa aynı sözleşme kontrolü iç runner ile geçerli kabul edilir.
