# BYS360 Script Devir Teslim Notu

Bu projede çok sayıda bakım ve gate scripti bulunabilir. Bunlar geliştirme sürecindeki onarım, güvenlik kontrolü ve geçiş doğrulama adımları için kaynak projede tutulur.

## Devir/release paketinde ne yapılır?

Güvenli release üretimi sırasında `scripts/security/check_bys360_secure_release_secret_clean_*`, `scripts/security/repair_bys360_secure_release_secret_clean_*`, `scripts/security/build_bys360_secure_release_*` ve `scripts/windows/build_bys360_secure_release_*` dosyaları release dışına alınır.

Böylece devredilen paket; çalıştırılabilir kaynak kod, gerekli statik dosyalar, migrationlar ve sade dokümantasyon içerir. Geçmiş bakım scriptleri yeni geliştiriciyi gereksiz yere yormaz.

## Güncel kaynak içi bakım komutu

Kaynak projede güvenli release üretmek için güncel komut:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\build_bys360_secure_release_v1_5.ps1 -ProjectRoot "C:\bys360\project"
```
