# BYS360 DA-21H4 Local Preview Enable Helper

## Amaç

Dijital Arşiv GET ekranlarının local önizleme env değerleriyle disabled.html ekranına düşmeden açılması sağlanmıştır.

## Desteklenen Env Değerleri

- DIGITAL_ARCHIVE_ENABLED=1
- BYS360_DIGITAL_ARCHIVE_ENABLED=1
- BYS360_DIGITAL_ARCHIVE_LOCAL_UI_PREVIEW=1

## Güvenlik Notu

Bu helper yalnızca GET ekranlarının görünürlüğünü etkiler. DB yazma kapısı ayrıca local write env ve route guard koşullarıyla kontrol edilmektedir.

## Sonuç

- Python syntax kontrolü geçmiştir.
- Local preview page check geçmiştir.
- Sayfalar disabled ekrandan çıkmıştır.
