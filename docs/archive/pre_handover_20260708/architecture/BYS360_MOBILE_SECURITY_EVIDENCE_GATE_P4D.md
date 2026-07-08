# BYS360 P4D Mobile Security Evidence Gate

Bu paket P4A ve P4B V3 güvenlik kapılarını birleştiren P4C V2 raporunu devir/CI kanıtı olarak doğrular.

## Kontroller

- P4C V2 security suite raporu `ok=true` olmalı.
- P4A auth guard ve P4B V3 role boundary raporları bulunmalı ve başarılı olmalı.
- Toplam probe sayısı en az 97 olmalı.
- Beklenen mobil güvenlik feature kapsamı eksiksiz olmalı.
- Secret finding sayısı 0 olmalı.
- Mobil route facade sözleşmesi korunmalı: `routes.py <= 300`, toplam 24 route decorator.

Canlı veriye yazmaz; yalnızca rapor ve kalite kapılarını doğrular.
