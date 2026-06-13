# BYS360 Performans Yönetimi V2.1.3 — Personel Kartı Kategori ve Atama Merkezi

## Amaç

V2.1.3, V2.1.2 ile kurulan personel grup/kategori altyapısını personel ekranlarına bağlar. Böylece yetkili kullanıcılar personelin performans kategorisini görüntüleyebilir, tekil veya toplu atama yapabilir ve kategori değişikliklerini denetlenebilir şekilde izleyebilir.

## Kapsam

| Başlık | Açıklama |
|---|---|
| Personel kategori merkezi | Personel listesini kategori bilgisiyle gösterir. |
| Tekil kategori atama | Kullanıcı ID üzerinden kategori ataması yapar. |
| Toplu kategori atama | Virgül, boşluk veya satır bazlı kullanıcı ID listesine kategori atar. |
| Kategori filtresi | Personel listesi kategoriye göre süzülebilir. |
| Personel kartı paneli | Profil/düzenleme ekranına performans kategorisi paneli eklenir. |
| Audit kayıt | Kategori değişiklikleri ayrı audit tablosunda tutulur. |
| Gate kontrol | Tablolar, servisler ve ekran yardımcıları doğrulanır. |

## Veri yaklaşımı

V2.1.3 mevcut `users` tablosunu değiştirmez. Aktif kategori ilişkisi V2.1.2 tablosunda tutulur:

- `performance_personnel_categories`
- `performance_personnel_category_assignments`

V2.1.3 ayrıca kategori değişikliklerini izlemek için şu tabloyu kurar:

- `performance_personnel_category_audit_logs`

## Yetki yaklaşımı

Kategori atama ekranı Admin/Sistem Yöneticisi yetkisine bağlıdır. Personel kartı paneli yalnızca mevcut profil/düzenleme ekranında bilgilendirici panel ve yönetim ekranına bağlantı sunar.

## Canlı kontrol

1. `python -m compileall app scripts` hatasız çalışmalı.
2. V2.1.2 tabloları mevcut olmalı.
3. `performance_personnel_category_audit_logs` tablosu oluşmalı.
4. `/performance/v2-1-3-personnel-category-card` ekranı açılmalı.
5. Personel listesi kategori bilgileriyle gelmeli.
6. Tekil kategori ataması yapılabilmeli.
7. Toplu kategori ataması yapılabilmeli.
8. Kategori değişikliği audit tablosuna düşmeli.
9. Personel profil/düzenleme ekranında V2.1.3 paneli görünmeli.
10. Yetkisiz kullanıcı kategori atama ekranına erişememeli.

## Rollback

- `app/performance/__init__.py` dosyası `.bak_v2_1_3_*` yedeğinden geri alınabilir.
- `personnel_profile.html` ve `personnel_edit.html` dosyaları `.bak_v2_1_3_*` yedeğinden geri alınabilir.
- `performance_personnel_category_audit_logs` tablosu yedek sonrası kaldırılabilir.
- V2.1.2 kategori tabloları bu paket için temel olduğundan ayrıca kaldırılması önerilmez.

## Sonraki faz bağlantısı

V2.1.4 ile kategori bazlı dönem kapsamı ve kategoriye göre görev üretimi bu altyapının üzerine bağlanacaktır.
