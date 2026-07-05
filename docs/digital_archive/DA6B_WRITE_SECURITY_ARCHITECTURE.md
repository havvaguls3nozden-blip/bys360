# BYS360 DA-6B Dijital Arşiv Yazma Güvenliği Mimari İskeleti

## Amaç

DA-6B aşamasında, Dijital Arşiv modülünde ileride açılabilecek veri yazma işlemleri için mimari güvenlik iskeleti tanımlanmıştır.

Bu aşama veri yazma açmaz.

## Mevcut Güvenli Durum

- Dijital Arşiv route'ları GET-only durumdadır.
- POST route yoktur.
- DB yazma yoktur.
- Taslak formlar disabled durumdadır.
- DA-5E yazma güvenliği sözleşmesi geçerlidir.

## Eklenen Kod İskeleti

`app/digital_archive/security_contract.py`

Bu dosya yalnızca sözleşme ve metadata içerir.

İçerdiği ana başlıklar:

- `DIGITAL_ARCHIVE_WRITE_ENABLED = False`
- `DigitalArchiveWriteOperation`
- Operasyon bazlı izin anahtarları
- Operasyon bazlı audit action anahtarları
- Tablo bazlı whitelist alanları
- Yazma açılmadan önce zorunlu güvenlik gereksinimleri

## Planlanan Yazma Operasyonları

### 1. Arşiv Kategorisi Oluşturma

- Operasyon: `category_create`
- Tablo: `digital_archive_categories`
- Taslak route: `/digital-archive/categories/new`
- Yetki: `digital_archive.category.create`
- Audit action: `digital_archive.category.create`

### 2. Fiziksel Konum Oluşturma

- Operasyon: `physical_location_create`
- Tablo: `digital_archive_physical_locations`
- Taslak route: `/digital-archive/physical-locations/new`
- Yetki: `digital_archive.physical_location.create`
- Audit action: `digital_archive.physical_location.create`

### 3. Saklama Politikası Oluşturma

- Operasyon: `retention_policy_create`
- Tablo: `digital_archive_retention_policies`
- Taslak route: `/digital-archive/retention-policies/new`
- Yetki: `digital_archive.retention_policy.create`
- Audit action: `digital_archive.retention_policy.create`

## Zorunlu Güvenlik Gereksinimleri

Veri yazma açılmadan önce aşağıdaki kontroller uygulanmalıdır:

- Route seviyesinde yetki kontrolü
- CSRF doğrulaması
- Sunucu tarafı validasyon
- Alan whitelist kontrolü
- Audit event üretimi
- Transaction / rollback standardı
- Soft-delete / pasifleştirme politikası
- Canlı öncesi yedek ve deployment kontrolü

## DA-6B Sonucu

OK: Yazma güvenliği mimari iskeleti tanımlanmıştır.

Bu aşama hâlâ POST açmaz ve DB yazmaz.
