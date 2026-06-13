# BYS360 Portal V3A2 — Haber Tarama Sağlamlaştırma

Bu paket V3A Basında Tarihi Alan haber takip yapısını daha seçici ve kurumsal hale getirir.

## Eklenen güçlendirmeler

- Kaynak güven listesi ve yerel kaynak işareti
- Konu alakası puanı
- Riskli kelime etiketi
- Benzer haberleri tek aday altında birleştirme
- Elenen haber örnekleri
- Tarama sağlık raporu
- Hero ve portal paylaşımı için sadece onaylı haber mantığının korunması

## Kritik yayın kuralı

Sistem haber adayı bulur; otomatik portal gönderisi oluşturmaz. Yetkili kullanıcı onaylamadan yayın yapılmaz.

## Tarama raporları

- `reports/portal/BYS360_PRESS_NEWS_SCAN_V3A_LAST_REPORT.json`
- `reports/portal/BYS360_PRESS_NEWS_SCAN_V3A2_HEALTH_REPORT.json`

## Ortam değişkenleri

İstenirse arama sorguları ve güvenilir kaynaklar ayarlanabilir:

```text
BYS360_PRESS_NEWS_QUERIES="...|..."
BYS360_PRESS_NEWS_ALLOWED_HOSTS="aa.com.tr|trthaber.com|canakkale.gov.tr"
```
