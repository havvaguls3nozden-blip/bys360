# BYS360 DA-14A Dijital Arşiv Category Local SQLite Write Smoke

## Amaç

DA-14A aşamasında kategori oluşturma POST route'u yalnızca local SQLite test koşullarında gerçek kayıt oluşturabilecek hale getirilmiştir.

Bu aşama canlıya işlem yapmaz.

## Güvenlik Sınırı

Gerçek kayıt yalnızca aşağıdaki koşullar birlikte sağlanırsa oluşturulur:

- `current_app.config["TESTING"] = True`
- DB driver SQLite olmalıdır.
- `BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST = 1` olmalıdır.
- Route yalnızca `/digital-archive/categories` POST için çalışır.
- Operasyon yalnızca `category_create` ile sınırlıdır.

## Beklenen Davranış

- Local test POST ile 1 kategori kaydı oluşturulur.
- `digital_archive_categories` satır sayısı 1 artar.
- `digital_archive_physical_locations` değişmez.
- `digital_archive_retention_policies` değişmez.
- POST sonrası `/digital-archive/categories` adresine redirect döner.

## Canlı Güvenliği

Canlı ortamda `TESTING=True` ve local test environment değişkeni birlikte bulunmadığı için route yazma yapmaz.

## Sonuç

OK: İlk local SQLite kategori yazma smoke testi için güvenli local-only kapı hazırlanmıştır.
