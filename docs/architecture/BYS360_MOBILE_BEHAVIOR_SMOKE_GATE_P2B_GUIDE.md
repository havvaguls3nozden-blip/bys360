# BYS360 P2B Mobile Behavior Smoke Gate

Bu paket P1B-P1F ile ayrılan mobil API domain mimarisini davranışsal sözleşme kapısına bağlar.

Kontrol ettiği alanlar:

- `app/api/mobile/routes.py` facade olarak kalır ve 300 satır altında olmalıdır.
- Mobil endpoint decorator toplamı 24 olarak korunur.
- Endpointler doğru domain dosyalarının içinde bulunmalıdır.
- Auth, dashboard, notifications, personnel, KPI, communication, support/survey ve assistant domainleri smoke seviyesinde doğrulanır.
- Duplicate route decorator olmamalıdır.
- Pytest yoksa aynı sözleşme iç runner ile kontrol edilir; pytest kurulu CI ortamında `tests/architecture/test_mobile_api_behavior_smoke_p2b.py` doğrudan çalışır.
