# BYS360_HOME_PRESTIGE_SAFE_V1A

Bu paket, Claude prestij anasayfa tasarımını BYS360 son anasayfa omurgasına güvenli şekilde uygular.

## V1A düzeltmesi
Önceki V1 paketi `home.html` içinde `portal/_press_news_home_hero_v3a.html` include satırını zorunlu arıyordu. Son projede bu hero V4 hotfix ile anasayfadan kaldırılmış olabildiği için kurulum duruyordu. V1A bu markerı zorunlu tutmaz.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_HOME_PRESTIGE_SAFE_V1A_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_home_prestige_safe_v1a.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunCompile
```

Başarılı çıktı:

```text
BYS360_HOME_PRESTIGE_SAFE_V1A_CHECK_OK
```

## Korunanlar
- Mevcut home.html akışı
- Portal feed include yapısı
- Hava durumu kartı
- Görevler / operasyon kartları
- AI karar destek kartı
- Duyuru popup runtime
- Basın hero dosyası varsa güvenli haber filtresi

