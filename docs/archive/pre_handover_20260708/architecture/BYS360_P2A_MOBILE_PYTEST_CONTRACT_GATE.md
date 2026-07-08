# BYS360 P2A Mobil Pytest / Contract Gate

Bu paket P1B-P1E arasında yapılan mobil API domain parçalama çalışmasını test kapısına bağlar.

## Kapsam

- `app/api/mobile/routes.py` dosyasının ince facade seviyesinde kaldığını kontrol eder.
- Mobil domain dosyalarının varlığını kontrol eder.
- Toplam mobil route decorator sayısını 24 olarak doğrular.
- Python compile kontrolü yapar.
- İsteğe bağlı app factory smoke çalıştırır.
- İsteğe bağlı secret gate çalıştırır.
- `tests/mobile/test_mobile_domain_contract_p2a.py` testini üretir/günceller.

## Not

Bu paket gerçek secret içermez. App factory smoke için yalnızca geçici test ortam değişkenleri kullanılır.
