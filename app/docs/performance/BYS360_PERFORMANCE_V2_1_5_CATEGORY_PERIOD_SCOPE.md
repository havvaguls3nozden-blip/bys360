# BYS360 Performans V2.1.5 — Kategoriye Göre Dönem Kapsamı ve Görev Üretimi Hazırlığı

## Kapsam

V2.1.5, kategori bilgisini performans dönemi kapsamına hazırlık seviyesinde bağlar. Bu fazda gerçek dönem kaydı veya değerlendirme görevi değiştirilmez; önce güvenli kapsam planı oluşturulur.

| Alan | Açıklama |
|---|---|
| Kategori dönem kapsam planı | Seçilen kategori, dönem türü, tarih aralığı ve kapsam adıyla plan oluşturulur. |
| Personel ön izleme | Kategoriye bağlı personel sayısı ve yetkili kullanıcı için sınırlı ön izleme sağlanır. |
| Görev üretimi ön kontrolü | Kategori ataması var mı, personel var mı, tarih aralığı uygun mu, görev üretimine hazır mı kontrol edilir. |
| Güvenli yaklaşım | `performance_periods` ve `evaluation_assignments` tablolarına dokunulmaz. |
| Sol şerit | Performans Yönetimi altında Kategori Dönem Kapsamı sekmesi görünür. |

## Veri yapıları

- `performance_category_period_scope_plans`
- `performance_category_period_scope_plan_items`

## Başarı kriterleri

- V2.1.2 kategori tabloları mevcut olmalı.
- V2.1.3 personel kategori servisi çalışmalı.
- V2.1.4 kategori kapsam tablosu mevcut olmalı.
- V2.1.5 plan ve plan item tabloları oluşmalı.
- En az 6 varsayılan kategori listelenmeli.
- Plan oluşturma ve personel ön izleme çalışmalı.
- Sol şeritte **Kategori Dönem Kapsamı** görünmeli.
