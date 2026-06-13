# Faz 2 – Güvenlik ve Doğruluk Sertleştirmesi

Bu overlay canlı öncesi iletişim ve anket modüllerinin ikinci sertleştirme turunu içerir.

## Uygulanan başlıklar

- Bildirim yönlendirmelerinde güvenli fallback eklendi.
- `/portal/notifications` alias endpoint'i tanımlandı; kırık redirect riski kapatıldı.
- Aynı host üzerindeki mutlak URL'ler güvenli şekilde iç yönlendirmeye çevriliyor.
- Faz 4 rapor export akışına basit hız sınırlaması eklendi.
- Feedback sonuç export akışına da hız sınırlaması eklendi.
- CSV çıktıları Excel uyumu için `utf-8-sig` olarak sertleştirildi.
- Mesaj ek dosyası indirme akışı güvenli dosya yolu çözümleyicisine bağlandı.
- İletişim servislerinde kalan `query.get()` çağrıları `db.session.get()` ile güncellendi.
- Bildirim `_impl` fonksiyonlarına kısa davranış açıklamaları eklendi.
- Nabız formunda `mood_value` 1–5 aralığına sıkıştırıldı.

## Değişen dosyalar

- `app/communication/shared.py`
- `app/communication/notifications_routes.py`
- `app/communication/phase4_routes.py`
- `app/communication/feedback_routes.py`
- `app/communication/messages_routes.py`
- `app/services/feedback_report_service.py`
- `app/services/communication_phase1_service.py`
- `app/services/communication_phase2_service.py`
- `app/services/communication_phase4_service.py`
- `app/services/communication_service.py`

## Not

Bu faz veri şemasını değiştirmez. Migration gerekmez.
