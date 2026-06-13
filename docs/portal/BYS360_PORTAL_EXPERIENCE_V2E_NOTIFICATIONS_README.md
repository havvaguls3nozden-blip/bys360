# BYS360 Portal Deneyimi V2E — Bildirim Alışkanlığı

Bu paket portal bildirimlerini kullanıcı alışkanlığına bağlar. Yeni tablo açmaz, veritabanına dokunmaz.

## Özellikler

- Portal sağ alanına **Bildirimlerim** kartı eklenir.
- Okunmamış, portal ve öncelikli bildirim sayıları gösterilir.
- Son okunmamış bildirimler portal içinden hızlı erişilir hale gelir.
- Mevcut portal yorum, tepki, etiket ve paylaşım bildirimleri görünür portal alışkanlığına bağlanır.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V2E_NOTIFICATIONS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v2e_notifications.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```
