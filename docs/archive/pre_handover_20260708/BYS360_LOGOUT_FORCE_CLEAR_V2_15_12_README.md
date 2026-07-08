# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_OVERLAY

Bu overlay, BYS360 güvenli çıkış akışını güçlendirir.

## Çözdüğü durumlar

- Sol menüdeki Güvenli Çıkış bağlantısına basınca oturumun kapanmaması
- CSRF süresi dolduğu için çıkışın hata sayfasına düşmesi
- PWA / iOS / tarayıcı geri tuşunda eski sayfanın cache üzerinden görünmesi
- Bozuk veya yarım oturumda `/logout` adresinin login ekranına yönlendirmeyip içeride kalmış gibi davranması

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_logout_force_clear_v2_15_12.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol

```powershell
C:\bys360\project\.venv\Scripts\python.exe scripts\security\check_bys360_logout_force_clear_v2_15_12.py C:\bys360\project
```

## Son test

1. Uygulamayı yeniden başlatın.
2. Giriş yapın.
3. Sol menüden **Kullanıcı > Güvenli Çıkış** seçin.
4. Login ekranına dönmelidir.
5. Tarayıcı geri tuşuna basınca eski sayfa işlem yapabilir şekilde açılmamalıdır.
6. Direkt `/logout` adresine gidilse bile oturum temizlenip login ekranına dönmelidir.
