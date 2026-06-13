# İletişim ve Anket Yönetimi | Faz 9 Canlıya Geçiş Runbook

## Amaç
Bu faz; iletişim, bildirim, duyuru, yardım merkezi ve nabız/anket alanlarının kontrollü şekilde canlıya açılması için son karar yüzeyini sağlar.

## 9A — Yayın öncesi teknik kilit
- Kod freeze uygulanır.
- `.env`, cookie ve proxy ayarları son kez doğrulanır.
- Yeni migration ya da veri taşıma işi varsa karara bağlanır.
- Release etiketi ve rollback sorumluları netleştirilir.

## 9B — Veri ve güvenlik geçişi
- Veritabanı yedeği alınır.
- Log üretimi ve klasör izinleri kontrol edilir.
- KVKK açısından sicil bazlı görünürlük ve export alanları tekrar test edilir.
- Rollback planı yazılı olarak hazır tutulur.

## 9C — Pilot canlı açılış
- Pilot kullanıcı listesi sabitlenir.
- Tek destek kanalı tanımlanır.
- Faz 8 ve Faz 9 karar kayıtları sistem içine bırakılır.
- İlk açılış kontrollü kullanıcı grubuyla yapılır.

## 9D — İlk 72 saat stabilizasyon
- Operasyon sağlığı ekranı düzenli yenilenir.
- Atanmamış ve duran destek talepleri aynı gün kapatılır.
- CSRF, redirect ve export hataları öncelikli takip edilir.
- Gerekirse daraltılmış rollback veya hotfix penceresi kullanılır.
