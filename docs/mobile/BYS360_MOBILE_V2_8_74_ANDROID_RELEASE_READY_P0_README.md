# BYS360 Mobile V2.8.74 Android Release Ready P0 Overlay

Bu overlay, Android mobil uygulamanın Play Store / kurumsal dağıtım öncesi en kritik P0 eksiğini kapatır.

## Kapsam

- Release APK icin debug signing kullanimi kaldirilir.
- `android/key.properties` tabanli release signing yapisi eklenir.
- `google-services.json` varsa Google Services plugin kosullu uygulanir.
- FCM kapaliyken uygulama stabil kalir.
- FCM acikken token alindiktan sonra login sonrasi backend'e kayit denemesi yapilir.
- Keystore ve `key.properties` dosyalari git/release hijyen kurallarina eklenir.
- V2.8.74 gate ve Flutter test dosyasi eklenir.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MOBILE_V2_8_74_ANDROID_RELEASE_READY_P0_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_mobile_v2_8_74_android_release_ready_p0.ps1 -ProjectRoot "C:\bys360\project"
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_mobile_v2_8_74_android_release_ready_p0.ps1 -ProjectRoot "C:\bys360\project"
```

## Release keystore olusturma

Gercek sifreleri ChatGPT'ye veya zip dosyasina koymayin.

```powershell
cd C:\bys360\project\mobile_flutter\bys360_mobile_native
New-Item -ItemType Directory -Force .\keystores | Out-Null
keytool -genkey -v -keystore .\keystores\bys360-release.jks -alias bys360 -keyalg RSA -keysize 2048 -validity 10000
Copy-Item .\android\key.properties.example .\android\key.properties
notepad .\android\key.properties
```

`android/key.properties` icine yerel sifreleri yazin. Bu dosya ve `.jks` dosyasi kesinlikle zip/repo icine alinmamalidir.

## Release preflight

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_mobile_v2_8_74_android_release_ready_p0.ps1 -ProjectRoot "C:\bys360\project" -ReleasePreflight
```

## APK build

FCM kapali release:

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\build_bys360_mobile_v2_8_74_release_apk.ps1 -ProjectRoot "C:\bys360\project" -EnableFcm:$false
```

FCM acik release icin once Firebase Console'dan `google-services.json` alinip `mobile_flutter/bys360_mobile_native/android/app/google-services.json` altina konulmalidir:

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\build_bys360_mobile_v2_8_74_release_apk.ps1 -ProjectRoot "C:\bys360\project" -EnableFcm:$true
```
