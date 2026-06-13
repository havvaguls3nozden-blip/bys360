# BYS360 Geri Bildirim Kampanya Formu V2.13.2 Notu

Bu güncelleme, yeni geri bildirim kampanyası oluşturma ekranını BYS360'ın güncel gelişmiş yapısına uygun hale getirir.

## Ürün kararı

Kampanya ekranı, yalnızca klasik anket oluşturma ekranı gibi kalmamalıdır. BYS360'da artık şu amaçlarla kullanılmalıdır:

- Ekran hataları ve eksikler için toplu görüş toplama
- Yeni eklenen özelliklerin kullanıcı deneyimini ölçme
- Mobil / APK deneyimini düzenli izleme
- Tebrik ve teşekkürleri kurumsal hafızaya alma
- Nabız ve memnuniyet eğilimlerini raporlanabilir hale getirme

## Teknik yaklaşım

Veri modeli ve servis alanları değiştirilmedi. Mevcut `create_campaign_from_form` akışı korunmuştur. Bu nedenle güncelleme düşük risklidir ve temel olarak şablon / kullanıcı deneyimi iyileştirmesidir.

## Yetki notu

`/feedback/admin/campaigns/new` sayfası yönetim ekranıdır. Tüm personel tarafından değil; Admin, yetkili yönetici veya geri bildirim kampanyası yönetim yetkisi verilen kullanıcılar tarafından görülmelidir.
