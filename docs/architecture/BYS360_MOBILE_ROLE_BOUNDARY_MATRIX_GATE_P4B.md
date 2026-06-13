# BYS360 P4B Mobil Role Boundary Matrix Gate

Bu paket mobil API üzerinde rol/header/token taklidi sınırını güvenli şekilde test eder.

Kapsam:

- Dashboard, kimlik, personel, KPI
- İletişim, destek, anket, bildirim
- Performans görev ve yazma uçları

Kapı canlı veriye yazmaz. Flask `test_client` ile yetkisiz, sahte rol header'ı, unsigned admin/personel bearer ve malformed bearer senaryolarını çalıştırır. Amaç korumalı uçlarda açık `2xx`, `404/405` route kırılması ve beklenmeyen `5xx` oluşmadığını doğrulamaktır.

Rapor:

`reports/architecture/BYS360_MOBILE_ROLE_BOUNDARY_MATRIX_GATE_P4B_REPORT.json`
