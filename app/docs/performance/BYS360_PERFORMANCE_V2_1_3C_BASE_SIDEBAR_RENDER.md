# BYS360 Performans V2.1.3C — Sol Şerit Render Düzeltmesi

Bu hotfix, V2.1.3 Personel Kategori Atama ekranının sol şeritte görünmemesi sorununu düzeltir.

## Neden gerekliydi?

V2.1.3A/B paketleri menü registry, canlı kapsam ve rol görünürlüğü tarafını güncelledi. Ancak canlı `app/templates/base.html` dosyası Performans Yönetimi alt sekmelerini registry'den dinamik basmak yerine sabit Jinja satırlarıyla render ediyor. Bu nedenle `performance_personnel_category_card` anahtarı görünür olsa bile ekranda nav satırı oluşmuyordu.

## Yapılan düzeltme

- `base.html` içinde `performance_subsection_visible` hesabına `performance_personnel_category_card` eklendi.
- Performans Yönetimi altında **Personel Kategori Atama** nav satırı eklendi.
- `effective_menu.py` son görünürlük katmanında Admin/Sistem Yöneticisi rolleri için menü anahtarı güvenceye alındı.

## URL

`/performance/v2-1-3-personnel-category-card`

## Başarı çıktısı

`BYS360_PERFORMANCE_V2_1_3C_BASE_SIDEBAR_RENDER_OK`
