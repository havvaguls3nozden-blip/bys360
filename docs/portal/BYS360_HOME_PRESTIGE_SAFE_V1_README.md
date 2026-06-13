# BYS360 Anasayfa Prestij SAFE V1 Overlay

Bu paket, Claude tarafından hazırlanan prestij anasayfa görsel dilini BYS360 mevcut anasayfasına güvenli şekilde uygular.

## Ne yapar?

- Mevcut `home.html` omurgasını korur.
- Portal, hava durumu, görevler, günlük operasyon, AI karar destek ve duyuru popup include yapılarını silmez.
- Prestij görünüm için yalnızca ek CSS/JS bağlar.
- Basında Tarihi Alan hero kartına ek koruma getirir: Tarihi Alan/Gelibolu/Çanakkale Savaşları ile ilgisiz haber hero alanında gösterilmez.
- Değişiklikten önce hedef dosyaların `.bak_...` yedeğini alır.
- Tekrar çalıştırıldığında marker çoğaltmaz.

## Uygulama

```powershell
cd C:ys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_HOME_PRESTIGE_SAFE_V1_OVERLAY.zip" -DestinationPath "C:ys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windowsepair_bys360_home_prestige_safe_v1.ps1 -ProjectRoot "C:ys360\project" -Mode all -RunCompile
```

## Önce sadece kontrol etmek istersen

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windowsepair_bys360_home_prestige_safe_v1.ps1 -ProjectRoot "C:ys360\project" -Mode audit
```

## Başarı çıktısı

`check.ok` değeri `true` olmalıdır.

## Değişen dosyalar

- `app/templates/home.html` içine marker'lı CSS/JS linkleri eklenir.
- `app/templates/portal/_press_news_home_hero_v3a.html` güvenli haber filtresiyle güncellenir.
- `app/static/css/bys360_home_prestige_safe_v1.css` eklenir.
- `app/static/js/bys360_home_prestige_safe_v1.js` eklenir.

## Canlıya almadan önce bakılacaklar

1. `/` veya anasayfa açılıyor mu?
2. Portal sekmeleri duruyor mu?
3. Basında Tarihi Alan alanında ilgisiz haber görünmüyor mu?
4. Hava durumu kartı ve hızlı kartlar mobilde taşmıyor mu?
5. Tarayıcı konsolunda JS hatası yok mu?
