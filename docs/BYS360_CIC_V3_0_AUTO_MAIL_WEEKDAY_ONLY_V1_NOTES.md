# BYS360 CIC V3.0 Auto Mail Weekday Only V1

Bu overlay, Kurumsal Bilgilendirme Merkezi otomatik mail zamanlayıcısına hafta sonu güvenlik kilidi ekler.

- Cumartesi ve pazar günleri otomatik mail gönderilmez.
- BYS360 Sistem ekranına "Sadece hafta içi gönder" alanı eklenir.
- Görevler ekranında hafta sonu gönderim yapılmadığına dair bilgi notu görünür.
- Windows görevi çalışsa bile servis katmanı hafta sonu otomatik gönderimi engeller.
- Manuel "Şimdi çalıştır" işlemi ayrı bir kullanıcı aksiyonudur; otomatik zamanlayıcı kuralı run_due_tasks fonksiyonunda uygulanır.
