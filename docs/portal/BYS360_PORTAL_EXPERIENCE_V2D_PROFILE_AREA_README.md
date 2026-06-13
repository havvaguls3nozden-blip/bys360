# BYS360 Portal Deneyimi V2D — Kurumsal Profil Alanı

Bu paket kurumsal profil görünümünü güçlendirir. Yeni tablo açmaz ve veritabanına dokunmaz.

## Özellikler

- Yayın akışı sol profil kartı daha kurumsal ve bilgilendirici hale gelir.
- Profil sayfasında büyük profil özeti, birim/görev bilgisi, görünür paylaşım sayısı ve profil tamamlanma göstergesi görünür.
- Eski küçük profil kutusu gizlenir.
- Canlı ekranda sürüm/geliştirme dili kullanılmaz.
- Mobilde profil kartı tek kolon düzenine geçer.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V2D_PROFILE_AREA_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v2d_profile_area.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Başarılı çıktı:

```text
BYS360_PORTAL_EXPERIENCE_V2D_PROFILE_AREA_OK
```
