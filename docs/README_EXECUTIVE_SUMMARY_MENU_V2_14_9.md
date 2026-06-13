# BYS360 Yönetici Özeti Menü Düzeltme Overlay V2.14.9

Bu overlay yalnızca sol menü hiyerarşisini düzeltir.

## Yaptıkları

- `Yönetici Özeti` bağlantısını AI Karar Destek altından çıkarır.
- `Yönetici Özeti`ni bağımsız ana menü/akordeon grubu olarak ekler.
- Kendi ikonunu kullanır: `fa-chart-line`.
- Alt menüleri ekler:
  - Yönetici Paneli
  - Otomatik E-Postalar
  - Mail Logları
  - Zamanlanmış İşler
  - Test Gönderimi
- Her değişiklikten önce yedek alır.
- Veri silmez.
- DB migration çalıştırmaz.

## Bağlantılar

Alt menüler mevcut çalışan sayfaya ve sayfa içi anchor bağlantılarına gider:

- `/dashboard/yonetici-ozeti`
- `/dashboard/yonetici-ozeti#otomatik-epostalar`
- `/dashboard/yonetici-ozeti#mail-loglari`
- `/dashboard/yonetici-ozeti#zamanlanmis-isler`
- `/dashboard/yonetici-ozeti#test-gonderimi`

## Yetki Kodları

Referans yetkiler:

- `executive_summary.view`
- `executive_summary.dashboard`
- `executive_summary.emails`
- `executive_summary.logs`
- `executive_summary.jobs`
- `executive_summary.test`
- `executive_summary.admin`

Canlı rol matrisi mevcut BYS360 Ayarlar / Yetki ekranından yönetilmelidir.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_EXECUTIVE_SUMMARY_MENU_V2_14_9_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_executive_summary_menu_v2_14_9.ps1 -ProjectRoot "C:\bys360\project"

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_executive_summary_menu_v2_14_9.ps1 -ProjectRoot "C:\bys360\project"

Stop-ScheduledTask -TaskName "BYS360 Live Waitress 80"
Start-ScheduledTask -TaskName "BYS360 Live Waitress 80"
```

Tarayıcıda `Ctrl + F5` yapın.
