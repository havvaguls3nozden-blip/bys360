# BYS360 TCKN Alan Bazlı Şifreleme Kararı — V1A

## Problem

SCORE 100 kalite kapısı, `TCKN_ENCRYPTION_KEY` değerinin config/audit tarafında beklendiğini; ancak alan bazlı gerçek `encrypt/decrypt` kullanımının görünmediğini raporladı.

## Karar

BYS360 için iki doğru yoldan biri seçilmelidir:

### Seçenek A — TCKN tutulacaksa

- TCKN açık metin tutulmaz.
- Model/service katmanındaki yazma işlemi `encrypt_tckn()` ile yapılır.
- Okuma/gösterim yalnızca yetkili kullanıcıya ve mümkünse maskeli yapılır.
- Arama ihtiyacı varsa ayrıca hash/index alanı tasarlanır.
- Mevcut veriler için ayrı migration ve geri dönüş planı hazırlanır.

### Seçenek B — TCKN tutulmayacaksa

- TCKN alanı iş akışından çıkarılır.
- `TCKN_ENCRYPTION_KEY` zorunluluğu config/audit tarafında kaldırılır.
- Gerekçe güvenlik dokümanına yazılır.
