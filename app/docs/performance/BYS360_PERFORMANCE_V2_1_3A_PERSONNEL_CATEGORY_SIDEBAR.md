# BYS360 Performans V2.1.3A — Sol Şerit Menü Bağlantısı

## Amaç

V2.1.3 ekranı çalışır hale geldikten sonra kullanıcının ekrana doğrudan sol şeritten ulaşabilmesi gerekir. Bu hotfix, **Personel Kategori Atama** ekranını Performans Yönetimi menüsüne ekler.

## Menü tanımı

| Alan | Değer |
|---|---|
| Menü anahtarı | `performance_personnel_category_card` |
| Görünen ad | Personel Kategori Atama |
| Ana modül | Performans Yönetimi |
| Endpoint | `main.performance_v2_1_3_personnel_category_card` |
| URL | `/performance/v2-1-3-personnel-category-card` |
| Rol kapsamı | Admin, Sistem Yöneticisi |

## Yapılan teknik işlem

- `app/menu_registry_data_sections.py` içine performans menü maddesi eklenir.
- `app/live_scope.py` canlı menü anahtarları listesine menü anahtarı eklenir.
- `app/menu_registry_data_performance.py` rol varsayılanlarına menü anahtarı eklenir.
- `app/menu_registry.py` içinde runtime emniyet bloğu eklenir.
- `role_menu_defaults` tablosuna görünür kayıtları seed edilir.

## Gate kontrolü

- V2.1.3 route dosyası var mı?
- Menü maddesi flatten edilmiş menü listesinde görünüyor mu?
- Canlı kapsam filtresi menü anahtarını kabul ediyor mu?
- Endpoint URL üretilebiliyor mu?
- Role default kayıtları yazılmış mı?

## Rollback

Script çalışırken değişen dosyaların `.bak_v2_1_3a_*` yedeği alınır. Gerekirse aşağıdaki dosyalar yedekten geri alınabilir:

- `app/menu_registry_data_sections.py`
- `app/live_scope.py`
- `app/menu_registry_data_performance.py`
- `app/menu_registry.py`

DB tarafında `role_menu_defaults` içindeki `performance_personnel_category_card` kayıtları pasife alınabilir veya silinebilir.
