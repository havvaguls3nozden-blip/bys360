# BYS360 Performans Tamamlama Faz 10 — Otomatik Hatırlatma, Aksatan Amir ve Süreç Bildirimleri

Bu faz, performans değerlendirme sürecindeki bekleyen görevlerin, yaklaşan son tarihlerin, geciken amirlerin ve süreç bildirimlerinin tek merkezden yönetilmesini sağlar.

## Sabit Kurallar

- Otomatik hatırlatma merkezi aktif olduğunda bekleyen performans görevleri merkezi karar katmanından geçer.
- Hafta sonu gönderim kuralı tüm performans hatırlatma türleri için ortak uygulanır.
- Hafta sonu atlanan bildirimler başarısız sayılmaz; "Hafta Sonu Kuralı Nedeniyle Gönderilmedi" olarak loglanır.
- Geciken görevler amir bazlı aksatan amir raporuna dönüşür.
- Hatırlatma ve süreç bildirimleri otomatik puan, ceza veya idari karar üretmez.
- Mail ve bildirim metinlerinde teknik dil kullanıcıya gösterilmez.

## Kapanış Kriteri

`BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER_APPLY_OK` çıktısı alınmalıdır.
