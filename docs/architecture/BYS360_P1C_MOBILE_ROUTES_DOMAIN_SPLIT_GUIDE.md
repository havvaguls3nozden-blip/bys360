# BYS360 P1C Mobil API Domain Split Rehberi

Bu paket, P1B sonrasında küçültülen `app/api/mobile/routes.py` dosyasından düşük riskli ilk endpoint alanlarını domain modüllerine taşır.

Taşınan ilk alanlar:

- `auth`
- `dashboard`
- `personnel_read`
- `notifications`
- `support_survey_write`

Hedefler:

- URL ve endpoint sözleşmesini korumak.
- Route decorator sayısını değiştirmemek.
- `routes.py` dosyasını daha da küçültmek.
- P1D/P1E için güvenli domain ayrıştırma zemini oluşturmak.

Üretilen raporlar:

- `reports/architecture/BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.json`
- `reports/architecture/BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.md`
- `docs/architecture/BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.md`

P1D aşamasında iletişim/asistan blokları; P1E aşamasında personel create/all ve KPI blokları ayrılacaktır.
