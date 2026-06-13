# BYS360 P3B V3 Mobile Auth/Dashboard/Assistant Response Gate

Bu paket P3B için ayrı V3 kalite scripti ve ayrı rapor yolu oluşturur. Runtime route haritası doğrudan Flask `app.url_map` üzerinden okunur; büyük stdout çıktısı parse edilmez.

Kontroller:
- Mobil API facade: `app/api/mobile/routes.py` 300 satır altında ve route dekoratörü içermez.
- Mobil endpoint sözleşmesi: 24 endpoint korunur, duplicate yoktur.
- Auth, Dashboard ve BYS360 Asistanı endpointleri doğru domain dosyalarında durur.
- Flask runtime route haritasında beklenen suffix ve HTTP metodları görünür.
- `test_client` ile 404/405 kırılması olmadan cevap kodu smoke yapılır.
- App factory, secret gate ve hedefli pytest çalışır.
