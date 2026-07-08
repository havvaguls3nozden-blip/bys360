# BYS360 Portal Deneyimi V2F — Duyuru / İç Haber Vitrini

Bu paket duyuru ve iç haber vitrininin yayın akışında sağ tarafa yığılmasını önler. Vitrin sol alanda, profil kartının altında gösterilir.

## Özellikler

- Duyuru / iç haber vitrini sol alana alınır.
- Sağ alandaki duyuru kartı kaldırılır veya gizlenir.
- Sağ alan bildirim ve kısa özet kartları için daha hafif bırakılır.
- Mevcut `portal_v2.featured_announcements` verisi kullanılır.
- Yeni tablo açmaz, veritabanına dokunmaz.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V2F_NEWS_SHOWCASE_LEFT_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v2f_news_left.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```
