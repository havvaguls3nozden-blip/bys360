# BYS360 P14F1 — Mobile API Blueprint Name Fix

Bu paket `app/api/mobile/routes.py` içinde kalan eski `mobile_bp` değişken adını güvenli resolver ile düzeltir.

## Hata

Startup sırasında şu hata görülebilir:

```text
NameError: name 'mobile_bp' is not defined
_register_mobile_utility_routes_v1(mobile_bp, globals())
```

## Ne yapar?

- Utility route registration için gerçek Flask Blueprint nesnesini güvenli şekilde bulur.
- Eski doğrudan `mobile_bp` çağrısını `_bys360_mobile_utility_bp_v1` ile değiştirir.
- Kod davranışını değiştirmez; sadece route kayıt nesnesini doğru değişkenden alır.
- Yedek alır.
- `py_compile` kontrolü yapar.

## Kullanım

Önce çalışan Waitress ekranında `Ctrl + C` ile durdur.

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MOBILE_API_BLUEPRINT_NAME_FIX_P14F1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_p14f1_mobile_api_blueprint_name_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_p14f1_mobile_api_blueprint_name_fix.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_p14f1_mobile_api_blueprint_name_fix.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts
```

Sonra uygulamayı tekrar başlat:

```powershell
python -m waitress --listen=0.0.0.0:8000 --threads=12 --no-log-socket-errors wsgi:app
```

Beklenen: `Mobile real API routes` optional startup hatası artık görünmemeli.
