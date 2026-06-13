# BYS360 STATUS


<!-- PHASE2C6_STATUS_20260613 -->

## 2026-06-13 - Faz 2C6 Wildcard Import Durum Kararı

### Durum

Faz 2C5 sonunda düşük riskli wildcard import temizliği kontrollü şekilde uygulanmıştır.

- C5 aday sayısı: 5
- Kalıcı tutulan değişiklik: 4
- Güvenli geri alınan değişiklik: 1
- App AST wildcard sayısı: 62 -> 58
- Final test sonucu: 746 passed, 2 skipped, 34 deselected, 0 failed, 0 errors, 0 warnings
- Rollback all performed: False

### Kalıcı Temizlenen Dosyalar

- app/institutional/hr_form_helpers.py
- app/institutional/hr_reports_routes.py
- app/institutional/routes.py - app.institutional.hr_common importu
- app/institutional/routes.py - app.institutional.hr_personnel_operations_routes importu

### Güvenli Geri Alınan Dosya

- app/institutional/hr_scope_helpers.py

Gerekçe: açık import denemesi uygulama başlangıcında _safe_import bağımlılığı üzerinden test kırılımı oluşturduğu için dosya güvenli şekilde eski haline döndürülmüştür.

### Karar

Faz 2C6 kapsamında kalan wildcard importlar artık otomatik toplu temizlik konusu değildir. Kalanlar şu şekilde ele alınacaktır:

1. Güvenli ve küçük olanlar ileride mevcut modül düzenlemesi sırasında temizlenecek.
2. Facade/aggregator dosyaları bilinçli istisna olarak tutulacak.
3. Riskli dosyalar ayrı refactor konusu yapılacak.
4. Yeni script, yeni README, yeni manifest üretme alışkanlığı bırakılacaktır.
5. Bundan sonraki değişiklikler mevcut modül, mevcut test ve mevcut doküman üzerinden ilerleyecektir.

### Sonraki Adım

Faz 2Z final kapanış: compileall, route contract, auth guard, quality smoke, default pytest ve doküman kararlarının birlikte doğrulanması.

