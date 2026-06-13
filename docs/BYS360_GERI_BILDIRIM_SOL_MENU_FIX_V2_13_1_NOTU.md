# BYS360 Geri Bildirim Sol Menü Fix V2.13.1

## Amaç

Kullanıcının ekran hatası, eksik, öneri, tebrik ve teşekkür bildireceği sayfanın sol menüde görünmesini sağlar.

## Yapılan Düzeltmeler

- `base.html` içinde **Genel > Geri Bildirim Gönder** bağlantısı eklendi.
- Kısa yol varsayılan olarak görünür hale getirildi: `feedback_quick`.
- `/feedback/gonder` ekranında Genel menünün açık kalması sağlandı.
- `bys360_feedback_new` ve başarı ekranı, yalnızca `feedback_dashboard` menü yetkisine bağlı olmaktan çıkarıldı.
- Mevcut destek/geri bildirim kayıt altyapısı korunur; ayrı veri adası oluşturulmaz.

## Kontrol Adresi

- `/feedback/gonder`
