# BYS360 DA-5E Dijital Arşiv Yazma Güvenliği Sözleşmesi

## Amaç

Bu sözleşme, Dijital Arşiv ve Belge Yönetimi modülünde veri yazma işlemleri açılmadan önce uyulması gereken zorunlu güvenlik şartlarını tanımlar.

DA-5E aşamasında veri yazma açılmaz.

## Mevcut Durum

- Liste ekranları salt-okunur çalışmaktadır.
- Taslak form ekranları GET-only çalışmaktadır.
- POST route yoktur.
- DB yazma yoktur.
- Form alanları disabled durumdadır.
- Kayıt, silme veya güncelleme düğmesi yoktur.
- Canlı ortamda işlem yapılmamıştır.

## POST Açılmadan Önce Zorunlu Şartlar

### 1. Yetki Kontrolü

Kayıt oluşturma, güncelleme, pasifleştirme ve silme işlemleri yalnızca açıkça yetkilendirilmiş rol veya gruplar tarafından yapılmalıdır.

Yetki kontrolü sadece menü görünürlüğüne bırakılmamalıdır. Route seviyesinde de kontrol edilmelidir.

### 2. CSRF Koruması

POST ile veri yazma açılmadan önce CSRF token doğrulaması zorunludur.

CSRF doğrulaması olmayan hiçbir form yazma işlemine izin verilmemelidir.

### 3. Sunucu Tarafı Validasyon

Her form alanı sunucu tarafında doğrulanmalıdır.

Kontrol edilmesi gereken başlıklar:

- Zorunlu alan
- Maksimum uzunluk
- Veri tipi
- Benzersizlik
- Boşluk/trim kontrolü
- Güvenli karakter kontrolü
- Aktif/pasif durum kontrolü

### 4. Whitelist Alan Yazımı

Formdan gelen bütün alanlar doğrudan modele basılmamalıdır.

Yazılabilecek alanlar tablo bazında whitelist olarak tanımlanmalıdır.

### 5. Audit Event

Her veri yazma işleminde audit kaydı oluşturulmalıdır.

Audit kaydı en az şu bilgileri içermelidir:

- İşlemi yapan kullanıcı
- İşlem zamanı
- İşlem türü
- Hedef tablo
- Hedef kayıt
- Değişen alanlar
- IP / oturum bilgisi mümkünse

### 6. Transaction Güvenliği

Her yazma işlemi transaction içinde yapılmalıdır.

Hata oluşursa rollback zorunludur.

### 7. Soft Delete / Pasifleştirme Politikası

Silme işlemi doğrudan fiziksel delete olarak açılmamalıdır.

Öncelik pasifleştirme veya soft-delete yaklaşımı olmalıdır.

### 8. Canlıya Geçiş Öncesi Kontroller

Canlıya geçmeden önce ayrı deployment planı hazırlanmalıdır.

Zorunlu kontroller:

- Veritabanı yedeği
- `flask db current`
- `flask db heads`
- Migration uyumu
- Route smoke
- Yetki smoke
- Audit smoke
- Geri dönüş planı

## DA-5E Sonucu

OK: Dijital Arşiv yazma güvenliği sözleşmesi tanımlanmıştır.

Bu aşama hâlâ GET-only ve DB yazmasızdır.
