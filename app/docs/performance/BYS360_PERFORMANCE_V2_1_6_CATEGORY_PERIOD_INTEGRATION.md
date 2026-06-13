# BYS360 Performans V2.1.6 — Kategori Dönem Entegrasyonu

## Kapsam

V2.1.6, V2.1.5 kategori dönem kapsam planını gerçek performans dönemi kaydına bağlar. Bu faz, görev üretiminden önceki son güvenli entegrasyon katmanıdır.

| Alan | Açıklama |
|---|---|
| Plan → Dönem Bağlantısı | V2.1.5 planı gerçek `performance_periods` kaydına dönüştürülür veya mevcut bağlantı güncellenir. |
| Kategori Kapsamı | Dönem `scope_type='category'` ve ilgili kategori etiketiyle işaretlenir. |
| Ön Entegrasyon | Kategoriye bağlı personel dönem kapsam filtresiyle karşılaştırılır. |
| Amir Ön Kontrolü | Personelde yönetici sicil alanları var mı kontrol edilir. |
| Güvenli Mod | Bu faz gerçek `evaluation_assignments` üretmez. |

## Başarı kriterleri

- V2.1.5 plan tablosu mevcut olmalı.
- Entegrasyon tablosu oluşmalı.
- V2.1.5 planı gerçek dönem kaydına bağlanabilmeli.
- Bağlanan dönem kategori kapsamıyla çalışmalı.
- Ön entegrasyon satırları üretilebilmeli.
- `evaluation_assignments` tablosuna kurulum sırasında görev yazılmamalı.
