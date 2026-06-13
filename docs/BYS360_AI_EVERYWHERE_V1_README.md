# BYS360 AI Everywhere V1 Overlay

Bu paket, BYS360’da sonradan geliştirilen ekranların AI Karar Destek / BYS360 Asistanı çizgisine bağlanması için hazırlanmıştır.

## Ne yapar?

- Tüm `base.html` kullanan ekranlara kurumsal **AI destekli ekran rehberi** kartı ekler.
- Performans kategori/kapsam, dönem entegrasyonu, Başkan onayları, dönem içi notlar, personel, iletişim/anket/destek, kurumsal bilgilendirme, sistem ayarları, AI karar destek, asistan, KPI ve dashboard ekranlarını tanır.
- Kullanıcının bulunduğu ekrana göre “Asistana sor” hızlı soruları üretir.
- Mevcut BYS360 Asistanı paneline soru gönderir.
- Hassas veri göstermez, idari karar üretmez, performans puanı belirlemez.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_AI_EVERYWHERE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ai_everywhere_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol

```powershell
.\.venv\Scripts\python.exe .\scripts\quality\check_bys360_ai_everywhere_v1.py "C:\bys360\project"
```

Beklenen çıktı: `ok: true` ve PowerShell sonunda `BYS360_AI_EVERYWHERE_V1_OK`.

## Dokunulan dosyalar

- `app/static/css/bys360_ai_everywhere_v1.css`
- `app/static/js/bys360_ai_everywhere_v1.js`
- `scripts/repair/repair_bys360_ai_everywhere_v1.py`
- `scripts/windows/repair_bys360_ai_everywhere_v1.ps1`
- `scripts/quality/check_bys360_ai_everywhere_v1.py`
- `app/templates/base.html` içine marker'lı CSS/JS include eklenir.

## Güvenlik sınırı

Bu katman yalnızca rehberlik ve yönlendirme sağlar. AI karar vermez; puan, amir görüşü, mesaj içeriği, anket cevabı veya hassas personel verisi göstermez.
