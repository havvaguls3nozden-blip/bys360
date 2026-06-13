# AI Karar Destek / Analiz Merkezi Faz 7 — Excel Önizleme

Bu faz, Analiz Merkezi için gerçek içe aktarım yapmadan güvenli dosya doğrulama ve veri önizleme katmanı ekler.

## Kapsam

- `.xlsx` ve `.csv` dosya doğrulama
- dosya adı, uzantı, boyut ve içerik türü kontrolü
- `.xlsx` iç paket güvenliği: makro, dış bağlantı, gömülü nesne ve zip şişmesi sinyali
- sütun başlığı normalizasyonu
- tekrarlı ve boş başlık tespiti
- örnek satır önizleme
- formül hücrelerinin çalıştırılmadan gizlenmesi
- KVKK hassasiyet sınıflandırması
- TC kimlik, e-posta, telefon, sicil, ad-soyad, IBAN ve benzeri alanlarda maskeleme

## Bilinçli sınır

Bu fazda gerçek içe aktarım yoktur. Dosya sunucuya kalıcı olarak kaydedilmez, veritabanına yazım yapılmaz, personel/performans/anket/destek kayıtları üretilmez.

## Ekran

- Ana endpoint: `/admin/analysis-center/excel-preview`
- Kısa alias: `/admin/ai-excel-preview`
- Yetki: `login_required`, `admin_required`, `menu_key_required('ai_center')`

## Kalite kapısı

```powershell
python -S scripts\check_ai_decision_analytics_faz7_gate.py
python -S scripts\refactor\bys360_ai_decision_analytics_faz7_audit.py
```

Kapı statik çalışır; Flask veya veritabanı import etmez.
