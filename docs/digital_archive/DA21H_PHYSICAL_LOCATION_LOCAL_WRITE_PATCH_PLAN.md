# BYS360 DA-21H Physical Location Local Write Patch Plan

## Amaç

DA-21H aşamasında fiziksel lokasyon kayıt akışı için local write patch planı hazırlanmıştır.

Bu aşama POST çalıştırmaz ve DB yazma yapmaz.

## DA-21G Ön Koşul Sonucu

- Guard-only POST route gerçek fiziksel lokasyon payload alanlarıyla doğrulandı.
- Gerçek payload clean valid: True
- physical_location_create intent valid: True
- Intent write allowed: False
- Real POST status: 302
- Commit called: False
- digital_archive_physical_locations kayıt sayısı 0 olarak kaldı.
- Eski code/name payload valid değildir.

## Gerçek Physical Location Payload Alanları

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

## Local Write Açma Koşulları

Fiziksel lokasyon DB yazması yalnızca aşağıdaki üç koşul birlikte sağlanırsa açılmalıdır:

1. Flask app TESTING=True olmalıdır.
2. DB driver SQLite olmalıdır.
3. BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST=1 env değeri aktif olmalıdır.

Bu koşullar dışında route guard-only kalmalı ve DB yazmamalıdır.

## Planlanan Route Davranışı

- URL: /digital-archive/physical-locations
- Method: POST
- Valid payload + local write koşulları yoksa: redirect + flash
- Valid payload + local write koşulları varsa: DigitalArchivePhysicalLocation kaydı oluşturulur.
- Commit sonrası redirect: /digital-archive/physical-locations
- Invalid payload: DB yazmadan redirect

## Yazılacak Model Alanları

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

## Güvenlik Notu

Bu patch canlı yazma açmaz. Yazma yalnızca local test koşulları altında çalışacak şekilde sınırlandırılmalıdır.

## Sonraki Aşama

DA-21I aşamasında fiziksel lokasyon local write patch uygulanmalı ve tek kayıt oluşturma smoke testi yapılmalıdır.
