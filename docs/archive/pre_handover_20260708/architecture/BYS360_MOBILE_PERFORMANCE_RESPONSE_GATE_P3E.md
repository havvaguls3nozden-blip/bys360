# BYS360 P3E Mobile Performance Response Gate

Bu paket performans mobil endpointleri için response-code smoke kapısı kurar.

Kapsam:
- Performans özet, dönem, görev, karne, onay, kriter, rapor ve dönem içi not endpointleri.
- Flask runtime route haritasında suffix + method eşleşmesi.
- Yetkisiz `test_client` ile 404/405 kırılma kontrolü.
- Canlı veriye yazmaz; yetki katmanı nedeniyle 401/403 gibi cevaplar kabul edilir.

P3E temizse P3A-P3E mobil response kapıları P3F'de tek runner altında birleştirilebilir.
