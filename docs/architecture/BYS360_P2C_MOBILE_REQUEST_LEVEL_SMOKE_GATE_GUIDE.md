# BYS360 P2C Mobile Request-Level Smoke Gate

Bu paket kodu bozmaz; P1 mobil domain bölme zincirini request-level smoke kapısıyla güçlendirir.

Kontroller:

- `app/api/mobile/routes.py` facade olarak kalır.
- 24 mobil endpoint decorator sözleşmesi korunur.
- Domain sahipliği auth/dashboard/personel/KPI/iletişim/asistan/destek/anket/bildirim başlıklarında doğrulanır.
- Flask `test_client` oluşturulur.
- Mobil blueprint local hafif app-factory bağlamında kayıtlıysa örnek endpointler 5xx üretmeden denenir.
- Mobil blueprint kayıtlı değilse bu durum raporlanır ve static/domain sözleşme kapısı geçerli kabul edilir.
- pytest yoksa iç runner fallback modu kullanılır; CI ortamında pytest kuruluysa test dosyası doğrudan çalışır.

Rapor:

`reports/architecture/BYS360_MOBILE_REQUEST_LEVEL_SMOKE_GATE_P2C_REPORT.json`
