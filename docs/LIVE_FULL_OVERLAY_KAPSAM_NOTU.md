# BYS360 Canlı Full Overlay Kapsam Notu

## Canlıya alınan iyileştirme başlıkları

1. **Geri Bildirim Merkezi**
   - Ekran hatası, eksik bildirme, öneri, tebrik ve teşekkür dili kurumsallaştırıldı.
   - Kampanya oluşturma ekranı sade ve anlaşılır bir kullanıcı yönlendirme paneliyle desteklendi.

2. **Geri Bildirim Kampanyaları**
   - Kampanyanın amacı, hedef kitle, raporlanabilirlik ve takip edilebilirlik dili netleştirildi.
   - Mevcut form yapısı bozulmadan kullanıcı deneyimi güçlendirildi.

3. **Rol Matrisi / Ayarlar**
   - Rol, kişi ve birim bazlı görünürlük için açıklayıcı rehber paneli eklendi.
   - Tablolar mobilde taşmayacak şekilde responsive hale getirildi.
   - Menü görünürlüğünün yalnızca tasarım değil güvenlik kontrolü olduğu vurgulandı.

4. **Personel Bazlı Rol Matrisi**
   - Kişiye özel istisnaların audit log ile izlenmesi gerektiğini açıklayan rehber paneli eklendi.
   - Standart rol ile kişi bazlı özel görünürlük ayrımı daha anlaşılır hale getirildi.

5. **Portal / iPhone Responsive**
   - Portal kartları dar ekranda tek kolona düşürüldü.
   - Görsel ve iframe taşmaları azaltıldı.
   - Hazır olmayan Instagram/harici akış kartları ana görünümden gizlendi.

6. **Teknik Dil Temizliği**
   - Kullanıcı ekranında görülebilen bazı teknik ifadeler sade Türkçe karşılıklarla değiştirildi.
   - `unauthorized_scope`, `workflow state`, `sync`, `debug`, `endpoint`, `exception` gibi ifadeler yumuşatıldı.

## Değişiklik yaklaşımı

Bu paket canlı ortam için risk azaltılmış overlay mantığıyla hazırlanmıştır:

- Mevcut route akışları zorla değiştirilmez.
- Base template içine yalnızca overlay CSS/JS bağlantıları eklenir.
- Değiştirilen dosyalar otomatik yedeklenir.
- Rollback scripti vardır.
- Kontrol scripti vardır.

## Kontrol edilecek canlı ekranlar

- `/feedback`
- `/feedback/admin/campaigns`
- `/feedback/admin/campaigns/new`
- `/settings`
- rol matrisi ekranı
- personel detay / personel rol matrisi ekranı
- `/portal`
- iPhone Safari portal ana sayfa

## Başarı kriterleri

- Geri Bildirim sol menüde veya ilgili ana alanda erişilebilir olmalı.
- Kampanya ekranında eski/teknik görünüm yerine kurumsal açıklama paneli görünmeli.
- Portal iPhone ekranda yatay taşmamalı.
- Rol matrisi tabloları mobilde yatay kaydırılabilir olmalı.
- Kullanıcı beyaz ekran veya teknik hata metniyle karşılaşmamalı.
