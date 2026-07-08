# BYS360 Portal Deneyimi V1 Overlay

Bu paket BYS360 ana sayfa ve Kurumsal Portal ekranına kişiye özel portal deneyimi ekler.

## Eklenenler

- Benim Günüm kişisel portal özeti
- Öncelikli bildirim, performans görevi, destek talebi, anket ve mesaj kartları
- Kurumsal portal canlı akış takip paneli
- Teşekkür / Takdir, İyi Uygulama ve Günlük Not paylaşım türleri
- Takdir kültürü istatistikleri
- Ana sayfa ve `/portal` ekranına mobil uyumlu deneyim paneli
- Güvenli kontrol scripti ve rapor üretimi

## Kurulum

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol

Başarılı çıktı sonunda şu ifade görünmelidir:

```text
BYS360_PORTAL_EXPERIENCE_V1_APPLY_OK
```

Raporlar:

- `reports\portal\BYS360_PORTAL_EXPERIENCE_V1_REPORT.md`
- `reports\portal\BYS360_PORTAL_EXPERIENCE_V1_REPORT.json`
