# BYS360 DA-9C Dijital Arşiv Security Integration Contract

## Amaç

DA-9C aşamasında Dijital Arşiv modülünün mevcut BYS360 güvenlik omurgasına nasıl bağlanacağı kod sözleşmesi olarak hazırlanmıştır.

Bu aşama veri yazma açmaz.

## Eklenen Dosya

`app/digital_archive/security_integration_contract.py`

## Temel İlke

İlk uygulama doğrudan POST route açmak değildir.

Önce aşağıdaki güvenlik sözleşmesi sabitlenmiştir:

1. Oturum doğrulaması
2. Route seviyesinde yetki kontrolü
3. CSRF doğrulaması
4. Feature flag kapısı
5. Alan whitelist kontrolü
6. Sunucu tarafı validasyon
7. Transaction sınırı
8. Audit ve güvenlik izi
9. Güvenli hata yönetimi

## Operasyon Güvenlik Profilleri

Aşağıdaki operasyonlar için güvenlik profili hazırlanmıştır:

- `category_create`
- `physical_location_create`
- `retention_policy_create`

Her operasyon için:

- authentication zorunludur.
- route permission zorunludur.
- CSRF zorunludur.
- field whitelist zorunludur.
- payload validation zorunludur.
- audit zorunludur.
- transaction zorunludur.
- feature flag guard zorunludur.

## Entegrasyon Adayları

DA-9A ve DA-9B keşiflerinden aşağıdaki adaylar değerlendirilmiştir:

- login / authentication örnekleri
- permission / yetki örnekleri
- CSRF örnekleri
- audit örnekleri
- transaction örnekleri
- hata yönetimi örnekleri

## Güvenli Durum

- `DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED = False`
- `DIGITAL_ARCHIVE_WRITE_ENABLED = False`
- POST route açılmamıştır.
- DB yazma yapılmamıştır.
- Canlı ortamda işlem yapılmamıştır.

## Sonuç

OK: Dijital Arşiv güvenlik entegrasyon sözleşmesi hazırlanmıştır.

Mevcut aşama hâlâ güvenlidir:

- POST yoktur.
- DB yazma yoktur.
- Canlıya işlem yapılmamıştır.
