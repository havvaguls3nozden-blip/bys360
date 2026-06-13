# BYS360 Performans V2.1.3B — Personel Kategori Atama Sol Şerit Görünürlük Onarımı

Bu hotfix, V2.1.3A sonrası ekran çalıştığı halde sol şeritte görünmeyen **Personel Kategori Atama** sekmesini gerçek kullanıcı/rol görünürlüğüne bağlar.

## Yapılanlar

- Menü anahtarı dosya registry tarafında tekrar emniyete alınır.
- Runtime menü guard birden fazla menü dosyasına eklenir.
- `role_menu_defaults` içinde Admin/Sistem Yöneticisi için görünürlük zorlanır.
- `user_menu_permissions` içinde mevcut Admin/Sistem Yöneticisi kullanıcılarına kişi bazlı görünürlük verilir.
- Gate çıktısında rol ve kullanıcı bazlı izin sayıları raporlanır.

## Menü

- Ana modül: Performans Yönetimi
- Sekme: Personel Kategori Atama
- URL: `/performance/v2-1-3-personnel-category-card`
- Menü anahtarı: `performance_personnel_category_card`

## Not

Kurulum sonrası çalışan Waitress/Flask süreci yeniden başlatılmalı, kullanıcı çıkış-giriş yapmalı ve tarayıcı yenilenmelidir. Mevcut oturum menü izinlerini cache’lemiş olabilir.
