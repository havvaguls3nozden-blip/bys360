# BYS360 Portal V3B8C — Portal Menü/Sekme Geri Yükleme

Bu hotfix V3B8 sonrasında kaybolan Kurumsal Portal sol şerit menüsünü ve portal üst sekmelerini geri getirir.

## Geri Gelenler

- Kurumsal Portal sol şerit bölümü
- Yayın Akışı
- Profilim / Portal Profilim
- Personel Duvarları
- Gruplar / Portal Grupları
- Basında Tarihi Alan
- Portal Yönetimi

## Geri Getirilmeyen

- Sosyal Medya Gönderisi Ekle
- `/portal/social-import` menü/sekmesi

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V3B8C_RESTORE_PORTAL_MENU_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v3b8c_restore_portal_menu.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```
