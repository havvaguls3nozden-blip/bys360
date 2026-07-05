# BYS360 DA-21C Physical Location Guard-Only POST Plan

## Amaç

DA-21C aşamasında fiziksel lokasyon kayıt akışı için guard-only POST planı hazırlanmıştır.

Bu aşama route açmaz, POST test çalıştırmaz ve DB yazma yapmaz.

## DA-21B Ön Koşul Sonucu

- physical_location_create write_service dry-run intent hazırdır.
- Intent valid: True
- Intent write allowed: False
- Security write allowed: False
- Yeni POST route açılmamıştır.
- digital_archive_physical_locations kayıt sayısı 0 olarak kalmıştır.

## Planlanan Route

- URL: /digital-archive/physical-locations
- Method: POST
- İlk aşama: guard-only
- DB yazma: kapalı
- Başarısız/kapalı durumda redirect: /digital-archive/physical-locations

## Güvenlik Sırası

1. login_required
2. write_service physical_location_create intent üretimi
3. Security contract write_allowed kontrolü
4. Validation sonucu kontrolü
5. Guard-only kapalıysa redirect + flash
6. DB yazma sonraki faza bırakılır

## İlk Guard-Only Davranış

- physical_location_create intent valid olsa bile write_allowed False kalacaktır.
- Route DB session add/commit kullanmayacaktır.
- Tablo satır sayıları değişmeyecektir.
- POST route sayısı /digital-archive/categories ve /digital-archive/physical-locations olacak şekilde kontrollü artacaktır.

## Sonraki Aşama

DA-21D aşamasında fiziksel lokasyon guard-only POST route eklenecek ve DB yazmadan redirect davranışı doğrulanacaktır.
