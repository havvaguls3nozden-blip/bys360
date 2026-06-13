# BYS360 P3B Mobile Auth/Dashboard/Assistant Response Gate

Bu paket mobil API mimari kalite zincirinin P3B adımıdır. Kod davranışını değiştirmez; kalite kapısı ekler.

Kontroller:

- `app/api/mobile/routes.py` ince facade olarak 300 satır altında kalır.
- Mobil contract route sayısı 24 olarak korunur.
- Auth, dashboard ve asistan domain dosyaları beklenen endpointleri taşır.
- Flask runtime route haritasında ilgili endpoint ve HTTP metotları görünür.
- Flask `test_client` ile auth/dashboard/asistan endpointleri response-code smoke seviyesinde çalıştırılır.
- Secret gate ve app factory smoke temiz kalır.
- Pytest hedefli P3B testi çalışır.

Lightweight SQLite/test ortamında DB şeması yoksa 500 dönen endpointler hard fail yapılmaz; ancak 404/405 hard fail sayılır. Bu davranış canlı veriye yazmadan route ve cevap kodu seviyesinde güvenli smoke sağlar.
