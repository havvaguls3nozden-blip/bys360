# BYS360 Performans V2.1.4 — Kategori Bazlı Görünürlük ve Performans Kapsam Hazırlığı

## Kapsam

V2.1.4, personel kategori bilgisini performans dönemi kapsamına bağlamadan önce güvenli hazırlık katmanı oluşturur.

| Başlık | Açıklama |
|---|---|
| Kategori kapsam özeti | Her kategori için atanmış personel sayısı ve kapsam durumu gösterilir. |
| Kişi detayı kilidi | Personel dışı rollerde kişi detayının ayrıştırılacağı sonraki faza hazırlık yapılır. |
| Kapsam taslağı | Güvenlik/Temizlik gibi kategoriler için özel dönem kapsam taslağı oluşturulur. |
| Gate kontrolü | V2.1.2, V2.1.3 ve V2.1.4 tabloları/servisleri doğrulanır. |
| Sol şerit bağlantısı | Performans Yönetimi altında Kategori Kapsam Hazırlığı sekmesi görünür. |

## Veri yaklaşımı

Yeni tablo:

- `performance_category_scope_drafts`

Bu tablo performans dönemini doğrudan değiştirmez. Yalnızca ileride dönem kapsamı oluşturulurken kullanılacak kategori kapsam taslaklarını tutar.

## Kullanım

1. Kategori atamaları V2.1.3 ekranında yapılır.
2. V2.1.4 ekranında kategori bazlı sayı ve kapsam özetleri görülür.
3. Gerekirse kategori için kapsam taslağı oluşturulur.
4. V2.1.5 dönem kapsam motoru bu taslakları gerçek dönem kapsamına bağlar.

## Başarı kriterleri

- V2.1.2 kategori tabloları mevcut olmalı.
- V2.1.3 personel kategori kartı servisi mevcut olmalı.
- Kategori kapsam taslak tablosu oluşmalı.
- En az 6 varsayılan kategori listelenmeli.
- Ekran `/performance/v2-1-4-category-scope` yolundan açılmalı.
- Sol şerit altında **Kategori Kapsam Hazırlığı** görünmeli.
