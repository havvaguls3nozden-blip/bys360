# BYS360 Performans Tamamlama Faz 3 — Görünürlük ve Yetki Sınırları

Bu overlay, Faz 3 kapanışını tek sözleşmeye bağlar.

## Kapanış ilkeleri

- Personel yalnızca kendi karnesini ve kendi kategori/grup ortalamasını görür.
- Kategori/grup ortalaması kişi detayı göstermeden üretilir.
- Koordinatör yalnızca kendi çalışma grubu/kapsamındaki personel ve ortalamaları görür.
- Grup Başkanı yalnızca kendi grup/üst birim kapsamını görür.
- Başkan ve Admin/Sistem Yöneticisi kurum geneli görünürlük alır.
- Menü görünürlüğü ile backend route/query kapsamı birlikte denetlenir.
- URL elle yazıldığında yetkisiz kullanıcı veri alamaz; kurumsal 403 ekranı gösterilir.

## Paket dosyaları

- `app/services/performance/completion_phase3_visibility_scope.py`
- `app/services/performance/phase3_backend_route_guard.py`
- `app/services/performance/phase3_role_matrix.py`
- `scripts/performance/check_bys360_performance_completion_phase3_visibility_center.py`
- `scripts/performance/repair_bys360_performance_completion_phase3_visibility_center.py`
- `scripts/windows/repair_bys360_performance_completion_phase3_visibility_center.ps1`

## Başarı çıktısı

```text
BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_CENTER_APPLY_OK
```
