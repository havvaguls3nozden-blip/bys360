# BYS360 Mimari Genel Bakış

BYS360; kimlik, yetki, organizasyon, ayarlar, bildirim, loglama, raporlama ve karar destek servislerini merkezi omurgada toplayan modüler bir Flask/PostgreSQL kurumsal yönetim platformudur.

## Ana katmanlar

1. **Sunum katmanı:** Flask template ekranları, mobil/PWA yüzleri ve Flutter native uygulama.
2. **HTTP route katmanı:** Blueprint temelli endpoint bağlama katmanı. Bu katman iş mantığını taşımamalı, servisleri çağırmalıdır.
3. **Servis katmanı:** Performans, personel, iletişim, AI karar destek, yetki ve bildirim iş kurallarını yürütür.
4. **Veri katmanı:** SQLAlchemy modelleri, Alembic migrasyonları ve PostgreSQL veri omurgası.
5. **Güvenlik/uyum katmanı:** Rol bazlı erişim, menü görünürlüğü, CSRF, CSP nonce, rate limit, audit log ve upload doğrulama.
6. **Operasyon katmanı:** CI/CD, kalite gate, loglama, healthcheck, rollback ve devir teslim raporları.

## Mimari iyileştirme kuralı

- Route dosyası sadece HTTP binding yapmalıdır.
- 600 satırı aşan route dosyaları domain bazlı parçalanmalıdır.
- `phase*` isimli dosyalar kalıcı ürün mimarisinde anlamlı domain adlarına dönüştürülmelidir.
- Kritik iş kuralları servis katmanında ve test edilebilir fonksiyonlarda yaşamalıdır.
