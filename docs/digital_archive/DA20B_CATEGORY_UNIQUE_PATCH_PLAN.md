# BYS360 DA-20B Dijital Arşiv Category Unique Patch Plan

## Amaç

DA-20B aşamasında kategori code alanı için kalıcı unique koruma planı hazırlanmıştır.

Bu aşama POST test çalıştırmaz ve DB yazma yapmaz.

## DA-20A Kaynak Haritası Sonucu

- Sonuç: DA20A_CATEGORY_UNIQUE_SOURCE_MAP_OK
- Model code alanı var: True
- Model unique=True izi: False
- Model UniqueConstraint izi: False
- Model unique Index izi: False
- Migration real unique candidate: True
- Migration index candidate: True
- DB unique code protection: False
- Kategori kayıt sayısı: 1
- Duplicate code group count: 0
- Null/blank code count: 0

## Sorunun Anlamı

Route seviyesinde duplicate guard vardır; ancak bu tek başına yeterli değildir.

Kalıcı koruma için digital_archive_categories.code alanı hem model tarafında hem de DB tarafında unique olarak tanımlanmalıdır.

Mevcut veri temiz olduğu için local DB üzerinde unique index/constraint uygulanabilir durumdadır.

## Planlanan Patch Stratejisi

1. Model tarafında DigitalArchiveCategory.code alanı unique=True ve index=True olacak şekilde güncellenecektir.
2. Yeni Alembic migration dosyası eklenecektir.
3. SQLite uyumluluğu için unique index stratejisi tercih edilecektir.
4. Beklenen index adı: ux_digital_archive_categories_code
5. Upgrade akışı digital_archive_categories.code için unique index oluşturacaktır.
6. Downgrade akışı aynı indexi kaldıracaktır.

## Uygulama Sırası

- Model patch
- Migration dosyası ekleme
- flask db upgrade
- DB introspection ile unique index doğrulama
- Duplicate POST guard tekrar testi
- Invalid POST validation tekrar testi
- Liste GET görünürlük tekrar testi
- Clean checkpoint

## Güvenlik Notu

Bu plan DA-15B route seviyesindeki duplicate guard yerine geçmez; onu tamamlar.

Nihai hedef üç katmanlı korumadır:

- Route seviyesinde proaktif duplicate engeli
- Validation seviyesinde zorunlu alan kontrolü
- DB seviyesinde son savunma unique koruması

## Sonuç

OK: DA-20B unique patch planı hazırdır.

Bir sonraki aşama DA-20C model ve migration patch olacaktır.
