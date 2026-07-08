# BYS360 Mobile Smoke Baseline P1.11 V2.17.21

Bu paket uygulama dosyalarını değiştirmez. Mobil API refactor dalı sonrası:

- `app/api/mobile/routes.py` ve `performance_routes.py` fonksiyon/delegasyon özetini çıkarır.
- Flask URL map içinden mobil route listesini üretir.
- Parametresiz GET mobil endpointlerini smoke adayı olarak listeler.
- `compileall` ve `create_app` sağlık kontrolü yapar.

Bu paket, performans route refactor'una geçmeden önce güvenli temel ölçüm almak için hazırlanmıştır.
