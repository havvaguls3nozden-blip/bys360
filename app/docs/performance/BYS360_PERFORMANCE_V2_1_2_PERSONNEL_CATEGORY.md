# BYS360 Performans Yönetimi V2.1.2 — Personel Grup/Kategori Altyapısı

## Amaç

V2.1.2, performans sonuçlarının yalnızca kişi ve birim düzeyinde değil; Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel ve Diğer gibi kategori/grup düzeyinde yönetilebilmesi için temel veri omurgasını kurar.

## Kurulan veri yapıları

| Tablo | Amaç |
|---|---|
| `performance_personnel_categories` | Varsayılan ve ileride eklenecek performans kategorilerini tutar. |
| `performance_personnel_category_assignments` | Personel ile kategori arasındaki aktif/geçmiş ilişkiyi tutar. |

## Varsayılan kategoriler

| Anahtar | Görünen ad |
|---|---|
| `guvenlik` | Güvenlik |
| `temizlik` | Temizlik |
| `idari_personel` | İdari Personel |
| `teknik_personel` | Teknik Personel |
| `deneme_sureli_personel` | Deneme Süreli Personel |
| `diger` | Diğer |

## Canlıya geçiş kontrolü

1. `python -m compileall app scripts` hatasız çalışmalı.
2. `performance_personnel_categories` tablosu oluşmalı.
3. `performance_personnel_category_assignments` tablosu oluşmalı.
4. Varsayılan 6 kategori seed edilmeli.
5. `/performance/v2-1-2-categories` ekranı Admin/Sistem Yöneticisiyle açılmalı.
6. Test amaçlı bir kullanıcı ID'si ile kategori ataması yapılabilmeli.
7. Kategori ataması personel detayına zorla yazılmadığı için mevcut personel kaydı bozulmamalı.

## Sonraki faz bağlantısı

V2.1.2 tamamlandıktan sonra şu fazlar bunun üzerine bağlanacaktır:

- Performans döneminde kategori kapsamı seçimi.
- Kategori bazlı görev üretimi.
- Kategori ortalaması ve kişi detayı gizleme.
- Personel kartında kategori seçimi.
- Excel/import dosyasında kategori sütunu.
- Yetki sınırına göre kategori görünürlüğü.

## Rollback

Bu paket mevcut `users` veya performans çekirdek tablolarını değiştirmez. Geri almak için:

- Route dosyası opsiyonel import listesinden çıkarılabilir.
- `performance_personnel_categories` ve `performance_personnel_category_assignments` tabloları yedek sonrası kaldırılabilir.
- Scriptin oluşturduğu `.bak_v2_1_2_*` yedeklerinden `app/performance/__init__.py` geri döndürülebilir.
