# BYS360 P2C Mobile Request-Level Smoke Gate V3B

Bu overlay P2C request-level smoke kapısını V3B seviyesinde düzeltir.

- Static/domain contract P2B mantığıyla korunur.
- Flask test_client request-level smoke sonucu raporlanır.
- Pytest kurulu olup lokal plugin/ortam kaynaklı hata verse bile direct contract + behavior + request-level smoke temizse gate başarısız sayılmaz; durum raporda `pytest_failed_direct_contract_fallback` olarak açıkça görünür.
- Gerçek secret içermez.


Not: V3B, V3 paketindeki stdout_tail string kaçış hatasını düzeltir ve aynı kalite kapısını çalıştırır.
