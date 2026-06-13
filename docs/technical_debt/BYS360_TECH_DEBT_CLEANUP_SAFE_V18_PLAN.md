# SAFE V18 Plan

## Hedef

`effective_menu.py` içinde V16 raporuna göre kalan 10 güvenli sayılabilecek `manual_fallback_assignment` bloğunu loglu hale getirmek.

## Hariç tutulanlar

- `_rollback(...) + return` gibi kontrol akışı olan bloklar.
- `raise`, `return`, `try`, döngü veya karmaşık gövdeler.
- `corporate_information_center.py` içindeki DB rollback blokları.
- UI, `.env`, local DB ve migration dosyaları.

## Güvenlik

- Önce yedek alınır.
- Değişiklikler satır bazında raporlanır.
- Her değişiklik sonrası hedef dosya compile edilir.
- Genel compile ve Quality 9 gate opsiyonel çalıştırılır.
