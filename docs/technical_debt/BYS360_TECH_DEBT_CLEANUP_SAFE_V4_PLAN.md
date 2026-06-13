# BYS360 Teknik Borç Temizliği SAFE V4 Planı

SAFE V4, V3 sonrası kalan ana borç olan sessiz `except Exception` bloklarına odaklanır.

## Güvenli sınır

- Sadece uygulama Python dosyaları hedeflenir.
- Sadece basit ve davranışı değişmeyecek sessiz handler bloklarına log eklenir.
- `return`, `pass`, `continue`, `break`, basit atama gibi akışlar korunur.
- Karmaşık handler blokları sadece raporlanır.
- Her dosya değişmeden önce `C:ys360ackups` altına yedek alınır.
- Compile ve mevcut Quality 9 gate çalıştırılır.

## Varsayılan yama limiti

`-MaxPatches 120` olarak sınırlıdır. Böylece büyük ve riskli toplu refactor yerine kontrollü temizlik yapılır.
