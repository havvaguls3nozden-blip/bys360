# BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 7 Kullanım Kılavuzu

Versiyon: `BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE`

## Amaç
Bu kılavuz, Kurumsal Bilgilendirme Merkezi'nin canlı kullanımında görev seçimi, alıcı kontrolü, şablon düzenleme, kuru çalışma, gerçek gönderim ve log izleme adımlarını standartlaştırır.

## Canlı kullanım sırası
1. Sistem Sağlığı ekranında SMTP, gönderici adresi, CSRF, oturum ve log durumunu kontrol edin.
2. Alıcılar ekranında pilot grup ve görev kapsamını kontrol edin.
3. Şablonlar ekranında konu, metin, değişken ve teknik ifade kontrolü yapın.
4. Test Merkezi ekranında önce kuru çalışma yapın.
5. Kuru çalışma sonucu doğruysa gerçek gönderim onay kapısından pilot gruba gönderin.
6. Loglar ekranından başarılı / başarısız / atlandı sonuçlarını kontrol edin.
7. Pilot sonuç temizse daha geniş alıcı grubuna geçin.

## Temel güvenlik ilkesi
İlk canlı kullanımda toplu gerçek gönderim yapılmamalıdır. Önce pilot alıcı grubu ile doğrulama yapılmalıdır.
