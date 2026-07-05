# BYS360 DA-8A Dijital Arşiv Server-Side Validation Contract

## Amaç

DA-8A aşamasında, Dijital Arşiv modülünde ileride açılabilecek veri yazma işlemleri için sunucu tarafı validasyon sözleşmesi hazırlanmıştır.

Bu aşama veri yazma açmaz.

## Eklenen Dosya

`app/digital_archive/validation_contract.py`

Bu dosya yalnızca saf validasyon fonksiyonları içerir.

## Güvenlik İlkeleri

- POST route açılmaz.
- DB yazma yapılmaz.
- `request.form` kullanılmaz.
- `db.session.add` kullanılmaz.
- `db.session.commit` kullanılmaz.
- Validasyon sadece operasyon anahtarı ve payload sözlüğü üzerinden çalışır.
- Whitelist dışı alanlar reddedilir.
- Zorunlu alanlar kontrol edilir.
- Maksimum uzunluk kontrolü yapılır.
- Boolean alanlar normalize edilir.
- Integer alanlar normalize edilir.
- `retention_years` negatif olamaz.

## Operasyonlar

### category_create

Zorunlu alan:

- `name`

Tip kontrolleri:

- `parent_id`: integer
- `sort_order`: integer
- `is_active`: boolean

### physical_location_create

Zorunlu alan:

- `archive_room`

Alanlar:

- `archive_room`
- `cabinet_no`
- `shelf_no`
- `box_no`
- `folder_no`
- `file_no`
- `physical_status`

### retention_policy_create

Zorunlu alanlar:

- `name`
- `retention_years`
- `action`

Tip kontrolleri:

- `retention_years`: integer
- `requires_approval`: boolean
- `is_active`: boolean

## Sonuç

OK: Server-side validation sözleşmesi hazırlanmıştır.

Mevcut aşama hâlâ güvenlidir:

- POST yoktur.
- DB yazma yoktur.
- Canlıya işlem yapılmamıştır.

Not: retention_years negatif olamaz.

