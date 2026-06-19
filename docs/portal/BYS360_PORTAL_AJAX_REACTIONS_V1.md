# BYS360 Portal AJAX Reactions V1

Bu paket, portal paylaşım tepkilerinin sayfa yenilenmeden çalışmasını sağlar.

## Değişen davranış

- Beğeni/tepki butonuna basıldığında tam sayfa yenilenmez.
- Backend aynı route üzerinden JSON cevap döndürür.
- Tepki toplamı, seçili tepki ve tepki sayıları DOM üzerinde anlık güncellenir.
- JavaScript kapalıysa veya tarayıcı `fetch` desteklemiyorsa eski POST + redirect davranışı korunur.
- Yetki yoksa AJAX isteğinde kurumsal Türkçe hata mesajı döner.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_AJAX_REACTIONS_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_portal_ajax_reactions_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol

Portal akışında bir paylaşımda `Beğendim` veya başka bir tepkiye basın. Sayfa yukarı atlamadan veya yenilenmeden tepki sayısı değişmelidir.

Audit raporu:

```text
reports\quality\BYS360_PORTAL_AJAX_REACTIONS_V1_REPORT.json
```
