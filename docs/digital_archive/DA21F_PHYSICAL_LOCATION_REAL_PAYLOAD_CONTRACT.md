# BYS360 DA-21F Physical Location Real Payload Contract

## Amaç

DA-21F aşamasında physical_location_create dry-run kontratı gerçek fiziksel lokasyon şemasına göre düzeltilmiştir.

## Gerçek Payload Alanları

- archive_room
- cabinet_no
- shelf_no
- box_no
- folder_no
- file_no
- physical_status
- delivered_to_user_id
- delivered_at
- returned_at

## Sonuç

- code/name artık fiziksel lokasyon payload alanı kabul edilmez.
- Gerçek fiziksel lokasyon payload temizleme fonksiyonu eklendi.
- physical_location_create intent gerçek konum alanlarıyla valid döner.
- Intent write allowed False kalır.
- Yeni POST route açılmadı.
- DB satır sayıları değişmedi.

## Sonraki Aşama

DA-21G aşamasında fiziksel lokasyon guard-only POST, gerçek payload alanlarıyla tekrar doğrulanmalıdır.
