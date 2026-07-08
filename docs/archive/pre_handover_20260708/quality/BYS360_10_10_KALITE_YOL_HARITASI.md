# BYS360 10/10 Kalite Yol Haritası

## Hedef

BYS360 zaten production seviyesinde güçlü bir kurumsal sistemdir. 10/10 hedefi için ana amaç yeni modül eklemek değil; bakım, test, gözlemlenebilirlik, CI/CD ve kod ayrışmasını kurumsal seviyeye çıkarmaktır.

## Faz 0 — Güvenli Başlangıç ve Tanılama

- Sessiz `except/pass` blokları kaldırılır.
- Opsiyonel başlangıç bileşenleri hata aldığında uygulama açılmaya devam eder ama hata loglanır.
- Kalite audit raporu üretilir.

Başarı kriteri: Gizli başlangıç arızası kalmaz.

## Faz 1 — Tanrı Dosyaları Parçalama

Öncelik sırası:

1. `app/api/mobile/routes.py`
2. `app/api/mobile/performance_routes.py`
3. `app/menu_registry.py`
4. `app/admin/routes.py`
5. `app/admin/ops_routes.py`

Parçalama kuralı:

- Auth/session ayrı
- Dashboard ayrı
- Personel ayrı
- Performans ayrı
- Destek/anket ayrı
- Ortak response/pagination/error helper ayrı

Başarı kriteri: Her yeni dosya tercihen 600 satır altında, zorunlu durumlarda 900 satır altında kalır.

## Faz 2 — Testleri Gerçek Güvenceye Çevirme

- Static gate testleri kalır ama tek başına kalite sayılmaz.
- En az 10 gerçek senaryo testi eklenir.
- Login, yetki, personel, performans dönem, 70 altı onay, mobil API ve destek talebi akışları test edilir.

Başarı kriteri: Test kapsamı sadece import/smoke değil, gerçek kullanıcı akışlarını da korur.

## Faz 3 — CI/CD Disiplini

- Ruff, black, isort, mypy, pytest, compileall tek komutta çalışır.
- Repair scriptleri üretim kökünde birikmez; arşivlenir veya CI job'a taşınır.
- Release paketi manifest, checksum ve kalite raporuyla çıkar.

Başarı kriteri: Canlıya çıkmadan önce tek komutla kalite kapısı çalışır.

## Faz 4 — Teknik Dil ve UI Temizliği

- Kullanıcı ekranlarında `workflow`, `phase`, `sync`, `debug`, `endpoint`, `exception`, `raw error` gibi ifadeler kalmaz.
- Tüm hata/boş/yetkisiz durumları kurumsal Türkçe bileşenlerden döner.

Başarı kriteri: BYS360 tek ürün gibi görünür; teknik borç kullanıcı yüzüne yansımaz.

## Faz 5 — Mobil State ve API Olgunlaştırma

- Flutter Provider yapısı büyüyen ekranlar için Riverpod/BLoC kararına bağlanır.
- Mobile API route'ları domain bazlı ayrılır.
- Mobil hata, offline, token refresh ve FCM senaryoları testlenir.

Başarı kriteri: Mobil taraf sadece çalışan değil, sürdürülebilir native uygulama seviyesine çıkar.
