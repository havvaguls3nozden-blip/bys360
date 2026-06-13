# BYS360 Portal Deneyimi V1B Guard Overlay

Bu paket V1 portal deneyimini güçlendirir.

## Amaç

- Eksik tablo/model yüzünden beyaz ekran oluşmasını engellemek.
- Portal deneyimi servisindeki sorguları tablo varlığı kontrolüyle çalıştırmak.
- Ana sayfa ve `/portal` için güvenli varsayılan bağlam üretmek.
- V1 görsel katmanını küçük erişilebilirlik/mobil iyileştirmelerle güncellemek.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V1B_GUARD_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_experience_v1b.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Başarılı çıktı:

```text
BYS360_PORTAL_EXPERIENCE_V1B_GUARD_OK
```
