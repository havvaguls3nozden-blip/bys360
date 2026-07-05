# BYS360 DA-12C Dijital Arşiv Category Guard-Only POST Route

## Amaç

DA-12C aşamasında Dijital Arşiv kategori oluşturma için ilk kontrollü POST route eklenmiştir.

Bu aşama gerçek DB yazma yapmaz.

## Eklenen POST Route

- Route: `/digital-archive/categories`
- Method: `POST`
- Operasyon: `category_create`
- Mod: `guard-only`
- DB yazma: `Yok`

## Beklenen Davranış

POST isteği geldiğinde:

1. Form payload `build_digital_archive_write_intent("category_create", ...)` ile dry-run olarak değerlendirilir.
2. `WRITE_ALLOWED = False` olduğu için kayıt oluşturulmaz.
3. Kullanıcıya güvenli bilgilendirme mesajı verilir.
4. `/digital-archive/categories` liste ekranına geri dönülür.

## Güvenli Durum

- Sadece kategori POST route açılmıştır.
- `physical_location_create` POST route açılmamıştır.
- `retention_policy_create` POST route açılmamıştır.
- DB yazma yapılmamıştır.
- Canlı ortamda işlem yapılmamıştır.
- `DIGITAL_ARCHIVE_WRITE_ENABLED = False`
- `DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED = False`
- `WRITE_ALLOWED = False`

## Sonuç

OK: Kategori için guard-only POST route eklenmiştir. Bu route yazma yapmaz; yalnızca güvenlik kapısının çalışmasını sağlar.
