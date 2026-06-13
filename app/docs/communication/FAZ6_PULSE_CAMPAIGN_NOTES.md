# Faz 6 — Nabız Ölçme ve Kampanya Entegrasyonu

Bu fazda canlı omurgayı kırmadan, migration gerektirmeden nabız ve kampanya akışları aynı yüzeyde bağlandı.

## Eklenenler
- Kişisel nabız geçmişi ekranı
- Yönetici için nabız analitiği ekranı
- Kampanya sonuç ekranına kampanya dönemi nabız görünümü
- `survey_with_pulse` ve `training_feedback_with_pulse` kampanya türleri
- Kampanya yanıtı ile aynı formda günlük nabız kaydı
- Dashboard ve yönetici ekranlarında nabız özetleri

## Teknik yaklaşım
- Veritabanında yeni kolon eklenmedi.
- Birleşik akış kampanya türü üzerinden yönetildi.
- Günlük nabız kaydı mevcut `FeedbackPulseEntry` tablosuna yazılmaya devam eder.
- Kullanıcı aynı gün daha önce nabız girdiyse kayıt güncellenir.

## Dikkat
- Bu faz migration gerektirmez.
- Yönetici analitiği gizlilik eşiği ile sınırlıdır.
- CSV export içine kampanya nabız özeti de eklendi.
