# BYS360 Teknik Borç Temizliği SAFE V2 Planı

## Amaç
SAFE V1 temizlik sonrası kalan teknik borcu modül ve dosya bazında sıralamak.

## Sıralama mantığı
1. P0: `.env`, yerel DB, secret benzeri ifadeler, syntax/bare except.
2. P1: sessiz broad exception, uygulama içi print, teknik UI dili.
3. P2: script print, large file, TODO ve genel broad exception.

## V3 için önerilen hedef
Hotspot raporundaki ilk 20 uygulama dosyasında:
- print -> logger dönüşümü,
- sessiz broad except -> loglu ve özgül hata yönetimi,
- teknik UI ifadeleri -> kurumsal Türkçe mesaj sözlüğü.

## Güvenlik notu
SAFE V2 yalnızca rapor ve yardımcı dosya üretir. Çalışan iş kuralı, route, template ve DB şemasında değişiklik yapmaz.
