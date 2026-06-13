# Faz 9B | Veri ve Güvenlik Geçişi Runbook

Bu fazın amacı, iletişim + anket + nabız alanının canlıya geçişinde veri omurgası, migration görünürlüğü, güvenlik kapıları ve rol/görünürlük doğrulamasını yazılı bir kontrol akışına bağlamaktır.

## Ana kontrol başlıkları

1. Sicil / kurum ID omurgası doğrulansın.
2. Eksik veya çakışan sicil kayıtları kapatılsın.
3. Migration klasörü, SQL hotfix dosyaları ve uygulanacak sıra netleştirilsin.
4. Son yedek ve rollback akışı fiziksel olarak doğrulansın.
5. Cookie, CSRF, CAPTCHA ve kişi bazlı görünürlük tekrar test edilsin.
6. Faz 9B karar kaydı bırakılmadan Faz 9C geçilmesin.

## Minimum kapanış kanıtı

- En az bir güncel yedek dosyası
- En az bir güncel uygulama ve operasyon logu
- Faz 9B kapı kaydı
- Faz 9B karar kaydı
- Sicil eksik/çakışma kontrol notu
- Migration / SQL sırası notu
