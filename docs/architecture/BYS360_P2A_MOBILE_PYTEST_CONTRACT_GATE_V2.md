# BYS360 P2A Mobile Pytest Contract Gate V2

P1 mobil domain split zincirini pytest/contract gate ile korur.

V2 düzeltmeleri:
- Pytest sonucu ayrıntılı raporlanır.
- Pytest kurulu değilse veya ortam kaynaklı çalışmazsa aynı sözleşme kontrolleri iç runner ile yapılır.
- Mobil route sözleşmesi, domain dosyaları, duplicate route ve facade boyutu korunur.
- Kod değişikliği route dosyalarına dokunmaz; sadece test/gate dosyası üretir.
