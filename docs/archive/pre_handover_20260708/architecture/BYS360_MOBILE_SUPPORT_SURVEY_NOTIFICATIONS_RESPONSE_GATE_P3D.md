# BYS360 P3D Mobil Destek/Anket/Bildirim Response Gate

Bu paket, mobil API ana sözleşmesi korunurken destek, anket ve bildirim endpointleri için response-code smoke kapısı ekler.

Kontrol edilen başlıklar:

- Mobil route facade sınırı: `app/api/mobile/routes.py <= 300 satır`
- 24 ana mobil endpoint sözleşmesi
- Destek/anket/bildirim endpointlerinin domain dosyalarında korunması
- Flask `app.url_map` runtime route haritasında suffix + method eşleşmesi
- `test_client` ile 404/405 kırılma kontrolü
- App factory smoke
- Secret gate finding_count = 0
- Targeted pytest

Canlı veriye yazmaz; test ortamında yetkisiz isteklerin 401/400/403/500 gibi route varlığını gösteren cevapları kabul edilir, 404/405 kırılma kabul edilmez.
