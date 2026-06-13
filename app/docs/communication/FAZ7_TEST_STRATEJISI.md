# Faz 7 Test Stratejisi

Bu faz yeni özellik eklemekten çok, iletişim + anket + nabız alanlarının canlı öncesi güvence katmanını kurmak için hazırlanmıştır.

## Amaç
- Kırık route veya eksik template riskini erkenden görmek
- Export, menü anahtarları ve çekirdek ekran sözleşmelerini doğrulamak
- Canlı öncesi kullanıcı kabul testlerini standartlaştırmak
- Son aşamada hotfix ihtiyacını azaltmak

## Eklenen bileşenler
- `pytest.ini`
- `tests/conftest.py`
- `tests/communication/test_communication_route_contracts.py`
- `tests/communication/test_communication_template_presence.py`
- `tests/communication/test_feedback_contracts.py`
- `scripts/communication_preflight.py`
- Faz 7 kabul ve canlı hazır kontrol listeleri

## Test katmanları
### 1) Kaynak sözleşme testleri
Bu testler uygulamayı ayağa kaldırmadan şunları doğrular:
- beklenen route tanımları mevcut mu
- kritik template dosyaları yerinde mi
- communication ve service alanında `query.get()` gibi eski kullanım kaldı mı
- CSV export `utf-8-sig` ile üretiliyor mu
- feedback tarafındaki çekirdek handler ve servis fonksiyonları mevcut mu

### 2) Kullanıcı kabul testleri
Ayrı kontrol listesinde tanımlıdır. Özellikle:
- anket taslağı → yayın → cevap → sonuç
- nabız kaydı
- destek kuyruğu ve SLA görünümü
- yönetici raporları ve export
- kişi bazlı görünürlük ve yetki kontrolleri

### 3) Canlı öncesi preflight
`communication_preflight.py` scripti hızlı statik kontrol üretir.

## Çalıştırma
### Pytest
```bash
pytest tests/communication -q
```

### Preflight script
```bash
python scripts/communication_preflight.py
```

## Beklenen başarı ölçütü
- pytest iletişim testleri temiz geçmeli
- preflight çıktısında eksik dosya ve eksik route olmamalı
- UAT maddeleri kritik hata olmadan tamamlanmalı

## Faz 7 sınırı
Bu faz bilinçli olarak migration açmaz.
Amaç güvence katmanı kurmak ve mevcut çalışan akışları doğrulamaktır.
