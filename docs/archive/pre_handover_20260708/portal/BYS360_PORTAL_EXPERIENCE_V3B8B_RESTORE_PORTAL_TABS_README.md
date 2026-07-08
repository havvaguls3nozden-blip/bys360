# BYS360 Portal V3B8B — Portal Sekmelerini Geri Getirme

Bu hotfix V3B8 sonrasında kaybolan portal üst sekmelerini geri getirir.

## Geri Gelen Üst Sekmeler

- Yayın Akışı
- Profilim
- Personel Duvarları
- Gruplar
- Basında Tarihi Alan
- Portal Yönetimi

## Korunan Sadeleştirme

- Sosyal Medya Gönderisi sekmesi geri getirilmez.
- `/portal/social-import` kullanıcı arayüzünde görünmez.
- Basında Tarihi Alan sayfasının tarih sıralaması korunur.

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V3B8B_RESTORE_PORTAL_TABS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v3b8b_restore_portal_tabs.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```
