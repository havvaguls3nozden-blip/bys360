# BYS360 P4A Mobil Auth Guard Matrix Gate

Bu paket mobil API ana yüzeyleri için yetkisiz ve hatalı token davranışını güvenli smoke testi olarak standardize eder.

Kapsam:

- Auth, kimlik, dashboard, asistan
- Personel, KPI, iletişim
- Destek, anket, bildirim
- Performans ana mobil uçları

Kapı canlı veriye yazmaz. Flask `test_client` ile yetkisiz ve hatalı bearer token denemeleri yapar. Amaç 404/405 route kırılması, beklenmeyen 5xx ve korumalı endpointte açık 2xx cevabı olmadığını doğrulamaktır.

Rapor:

`reports/architecture/BYS360_MOBILE_AUTH_GUARD_MATRIX_GATE_P4A_REPORT.json`
