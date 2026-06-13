# BYS360 Teknik Borç Temizliği SAFE V3 Planı

## Hedef

V2 raporunda uygulama kodunda kalan az sayıdaki `print()` kullanımını güvenli logger kullanımına dönüştürmek; daha büyük risk taşıyan sessiz `except Exception` blokları için ise net hotspot raporu üretmek.

## Uygulama sırası

1. Audit raporu üret.
2. Uygulama kodundaki tek satırlık `print(...)` çağrılarını tespit et.
3. Sadece güvenli dönüştürülebilen satırları patch et.
4. Patch öncesi dosya yedeği al.
5. Sessiz `except Exception` hotspot raporu üret.
6. Compile çalıştır.
7. Varsa Quality 9 gate çalıştır.

## Başarı kriterleri

- `compile_ok=true` olmalı.
- Quality 9 gate dönüş kodu 0 olmalı.
- Uygulama kodundaki `print()` sayısı azalmalı veya sıfırlanmalı.
- Sessiz except blokları otomatik değişmemeli, sadece raporlanmalı.
