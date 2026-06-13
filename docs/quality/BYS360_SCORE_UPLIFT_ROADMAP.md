# BYS360 90+ Kalite Puanı Yol Haritası

Bu yol haritası, 360° değerlendirmede görülen puan kırılımlarını sistemli şekilde 90+ seviyesine taşımak için hazırlanmıştır.

## P0 — Güvenlik ve repo hijyeni

Hedef: Güvenlik 90+, teknik borç 65+, kod kalitesi 70+.

- Gerçek `.env` ve local secret dosyaları repodan çıkarılır.
- Tüm secret değerler rotate edilir.
- `pip-audit` CI içinde build kıran kapı haline gelir.
- `.venv`, `backups`, `.bak`, `.orig`, `payload` gibi dosyalar kaynak kod ağacından çıkarılır.
- Bağımlılıklar tam sürüme pinlenir.
- `bys360_secret_repo_gate.py` CI'a bağlanır.

## P1 — Mimari konsolidasyon

Hedef: Mimari 80+, teknik borç 75+.

- `app/api/mobile/routes.py` domain bazlı route dosyalarına ayrılır.
- `communication/phase*` dosyaları anlamlı modül adlarına konsolide edilir.
- `admin/ai_phase*` dosyaları `ai_decision` domain yapısına alınır.
- Route dosyalarında iş mantığı azaltılır, servis katmanı güçlendirilir.

## P2 — Test olgunlaştırma

Hedef: Test 80+.

- Gerçek unit test sayısı artırılır.
- DB fixture stratejisi standartlaştırılır.
- Performans, yetki, yayın ve CSRF akışları integration test kapsamına alınır.
- CI'da sadece statik/contract test değil, kritik domain testleri de çalışır.

## P3 — Dokümantasyon ve devir teslim

Hedef: Dokümantasyon 80+.

- `CONTRIBUTING.md` ve onboarding rehberi eklenir.
- Genel mimari dokümanı ve modül sınırları yazılır.
- Mobil API için OpenAPI başlangıç dokümanı oluşturulur.
- Devir teslim manifesti ve temiz kaynak paket üretim süreci standartlaştırılır.

## P4 — Mobil/API profesyonelleştirme

Hedef: Mimari, test ve dokümantasyon puanlarını birlikte yükseltmek.

- Mobil API route dosyaları sadeleştirilir.
- Flutter native ekranlar ortak tasarım sistemine bağlanır.
- API response/error sözleşmesi standartlaştırılır.
- OpenAPI dokümanı mobil app ile birlikte güncellenir.
