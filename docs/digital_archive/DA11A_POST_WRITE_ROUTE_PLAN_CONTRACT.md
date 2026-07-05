# BYS360 DA-11A Dijital Arşiv POST Write Route Plan Contract

## Amaç

DA-11A aşamasında gerçek POST route açılmadan önce Dijital Arşiv yazma akışının route, güvenlik, audit, rollback ve hata davranışı sözleşmeye bağlanmıştır.

Bu aşama gerçek yazma yapmaz.

## Mevcut Güvenli Durum

- POST route açılmamıştır.
- DB yazma yapılmamıştır.
- Canlı ortamda işlem yapılmamıştır.
- `DIGITAL_ARCHIVE_WRITE_ENABLED = False`
- `DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED = False`
- `WRITE_ALLOWED = False`
- `DIGITAL_ARCHIVE_WRITE_SERVICE_MODE = DRY_RUN`

## Planlanan POST Route'ları

Gerçek uygulamaya geçildiğinde aşağıdaki üç yazma akışı planlanır:

| Operasyon | GET Taslak Route | Planlanan POST Route | Tablo |
|---|---|---|---|
| `category_create` | `/digital-archive/categories/new` | `/digital-archive/categories` | `digital_archive_categories` |
| `physical_location_create` | `/digital-archive/physical-locations/new` | `/digital-archive/physical-locations` | `digital_archive_physical_locations` |
| `retention_policy_create` | `/digital-archive/retention-policies/new` | `/digital-archive/retention-policies` | `digital_archive_retention_policies` |

## Zorunlu Güvenlik Sırası

Gerçek POST route açılmadan önce her operasyon için karar sırası aşağıdaki gibi kalmalıdır:

1. Authentication
2. Route permission
3. CSRF
4. Feature flag
5. Field whitelist
6. Payload validation
7. Transaction
8. Audit event
9. Failure handling

## POST Açma Ön Koşulları

Gerçek POST route ancak aşağıdaki koşullar sağlanırsa açılabilir:

- `DIGITAL_ARCHIVE_WRITE_ENABLED` açık olmalıdır.
- `DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED` açık olmalıdır.
- Operasyon için permission tanımı bulunmalıdır.
- CSRF koruması aktif olmalıdır.
- Form payload yalnızca whitelist alanlarından oluşmalıdır.
- Validation sonucu başarılı olmalıdır.
- DB işlemi transaction içinde yapılmalıdır.
- Başarılı işlemde audit event yazılmalıdır.
- Hata durumunda rollback yapılmalıdır.
- Başarılı işlem sonrası güvenli liste ekranına redirect yapılmalıdır.
- Hata durumunda form ekranı kullanıcı dostu mesajla tekrar gösterilmelidir.

## Rollback Davranışı

Gerçek yazma açıldığında aşağıdaki durumlarda işlem geri alınmalıdır:

- Validation hatası
- Permission hatası
- CSRF hatası
- Feature flag kapalı olması
- DB insert hatası
- Audit event yazma hatası
- Beklenmeyen exception

## Hata Mesajı Davranışı

Kullanıcıya teknik exception detayı gösterilmemelidir.

Beklenen davranış:

- Form verisi mümkün olduğu kadar korunur.
- Alan bazlı validasyon hatası kullanıcıya gösterilir.
- Genel hata mesajı sade ve kurumsal olur.
- Audit ve log tarafında teknik detay tutulur.

## DA-11A Sonucu

OK: Dijital Arşiv gerçek POST route açılmadan önce yazma route planı sözleşmeye bağlanmıştır.

Bu aşama hâlâ güvenlidir:

- POST route yoktur.
- DB yazma yoktur.
- Canlıya işlem yapılmamıştır.
