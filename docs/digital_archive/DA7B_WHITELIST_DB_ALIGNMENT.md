# BYS360 DA-7B Dijital Arşiv Whitelist / DB Kolon Hizalaması

## Amaç

DA-7B aşamasında, DA-7A audit raporunda görülen whitelist / DB kolon uyumsuzlukları düzeltilmiştir.

Bu aşama veri yazma açmaz.

## Yapılan Hizalama

### category_create

Önceki sorunlar:

- `title` alanı DB kolonlarında yoktu.
- `parent_id` ve `sort_order` whitelist dışında kalıyordu.

Yeni whitelist:

- `parent_id`
- `code`
- `name`
- `description`
- `is_active`
- `sort_order`

### physical_location_create

Önceki sorunlar:

- `code`, `name`, `building`, `room`, `shelf`, `box`, `description`, `is_active` alanları gerçek DB kolonlarıyla uyuşmuyordu.

Yeni whitelist:

- `archive_room`
- `cabinet_no`
- `shelf_no`
- `box_no`
- `folder_no`
- `file_no`
- `physical_status`

Yazma dışı bırakılan alanlar:

- `delivered_to_user_id`
- `delivered_at`
- `returned_at`

Bu alanlar teslim / iade iş akışına aittir; fiziksel konum oluşturma formundan doğrudan yazılmamalıdır.

### retention_policy_create

Önceki sorunlar:

- `code` alanı DB kolonlarında yoktu.
- `requires_approval` whitelist dışında kalıyordu.

Yeni whitelist:

- `name`
- `retention_years`
- `action`
- `requires_approval`
- `description`
- `is_active`

## Güvenli Durum

- `DIGITAL_ARCHIVE_WRITE_ENABLED = False`
- POST route yoktur.
- DB yazma yoktur.
- Bu aşama yalnızca güvenlik sözleşmesini gerçek DB kolonlarıyla hizalar.
- Canlı ortamda işlem yapılmamıştır.

## Sonuç

OK: Dijital Arşiv whitelist sözleşmesi gerçek DB kolonlarıyla hizalanmıştır.
