# BYS360 Portal Deneyimi V2 Overlay

Bu paket BYS360 kurumsal portalını daha canlı ve kullanıcıyı tekrar çağıran bir deneyime taşır.

## Eklenenler

- Kurumsal profil vitrini ve profil tamamlanma göstergesi
- Teşekkür / takdir ve iyi uygulama öne çıkanları
- Kurumsal duyuru / etkinlik vitrini
- Son 30 gün portal nabız istatistikleri
- Hızlı paylaşım kartları
- Mobil uyumlu Portal V2 görünüm katmanı
- Yeni tablo açmadan mevcut portal omurgası üzerinde güvenli servis

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V2_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v2.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Başarılı çıktı:

```text
BYS360_PORTAL_EXPERIENCE_V2_OK
```

Rapor:

- `reports\portal\BYS360_PORTAL_EXPERIENCE_V2_REPORT.md`
- `reports\portal\BYS360_PORTAL_EXPERIENCE_V2_REPORT.json`
