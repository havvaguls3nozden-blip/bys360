# BYS360_HOME_PRESTIGE_SAFE_V1A_ROLLBACK

Bu paket Claude/Prestij SAFE V1/V1A anasayfa kaplamasını geri almak için hazırlanmıştır.

## Ne yapar?

- `app/templates/home.html` içindeki prestij CSS/JS link bloklarını kaldırır.
- Mevcut anasayfa omurgasını, portal feed, hava durumu, görevler ve AI alanlarını korur.
- İşlem öncesi `app/templates/_backup_home_prestige_safe_v1a_rollback/` altında yedek alır.
- İsteğe bağlı `-DeleteStatic` ile prestij CSS/JS dosyalarını silmez; `.disabled_by_rollback` olarak yeniden adlandırır.

## Kullanım

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_HOME_PRESTIGE_SAFE_V1A_ROLLBACK_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\rollback_bys360_home_prestige_safe_v1a.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunCompile -DeleteStatic
```

Başarılı çıktı:

```text
BYS360_HOME_PRESTIGE_SAFE_V1A_ROLLBACK_OK
```
