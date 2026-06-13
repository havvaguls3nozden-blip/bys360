# BYS360 Portal V3A — Basında Tarihi Alan Haber Takip ve Onaylı Paylaşım

Bu paket ana sayfa hero alanına ve portal sol alanına **Basında Tarihi Alan** vitrini ekler.

## Güvenli yayın kuralı

- Sistem haber adayını bulur.
- Haber otomatik portalda yayınlanmaz.
- Yetkili kullanıcı `/portal/press-news` ekranında inceleyip onaylarsa portal gönderisi oluşur.
- Haber metni ve görseli kopyalanmaz; kısa bilgi ve kaynak bağlantısı kullanılır.

## Manuel tarama

```powershell
cd C:\bys360\project
C:\bys360\project\.venv\Scripts\python.exe .\scripts\portal\run_bys360_press_news_scan_v3a.py --project-root "C:\bys360\project" --manual
```

## Zamanlanmış görev

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_bys360_press_news_scan_v3a_task.ps1 -ProjectRoot "C:\bys360\project" -Create
```

Varsayılan saatler: 08:30, 12:30, 17:30.

## Aday havuzu

Adaylar yeni tablo açmadan `instance/portal/press_news_candidates_v3a.json` dosyasında saklanır.
