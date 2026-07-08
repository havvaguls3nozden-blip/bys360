# BYS360 P0C Source Secret Sanitizer V1

Bu paket P0B gate sonrasında kalan kaynak kod içi gerçek secret bulgularını hedefler.

Hedef dosyalar:
- `config.py`
- `app/services/config_hardening_service.py`
- eski maintenance/security kontrol scriptleri
- `tests/integration/test_http_db_core_flows.py`

Yaklaşım:
- Gerçek secret/string fallback değerleri env referansına alınır.
- Gerçek DB URL içindeki parola placeholder ile değiştirilir.
- Test default DB bağlantısı gerekiyorsa `sqlite:///:memory:` kullanılır.
- Gerçek Sentry DSN yerine `SENTRY_DSN` ortam değişkeni kullanılır.

Kritik not: Bu paket gerçek `.env` oluşturmaz. Canlı/local secret değerleri dışarıdan sağlanmalıdır.
