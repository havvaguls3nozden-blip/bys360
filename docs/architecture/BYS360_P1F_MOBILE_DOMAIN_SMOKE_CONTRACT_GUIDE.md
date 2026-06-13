# BYS360 P1F Mobil Domain Smoke / Contract Kapısı

Bu paket kod davranışını değiştirmez. P1B-P1E ile ayrılan mobil API domain yapısının bozulmadığını kontrol eden kalite kapısı ekler.

Kontroller:

- `app/api/mobile/routes.py` ince facade seviyesinde mi?
- Beklenen mobil domain dosyaları mevcut mu?
- Mobil route decorator sayısı önceki P1E sözleşmesiyle aynı mı?
- Domain dosyaları compile oluyor mu?
- App factory smoke `APP_FACTORY_OK` dönüyor mu?
- Secret gate `finding_count=0` dönüyor mu?

Yeni mobil endpointler mümkün olduğunca `routes.py` içine değil, ilgili `app/api/mobile/domains/*.py` dosyasına eklenmelidir.
