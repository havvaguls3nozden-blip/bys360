# BYS360 P14F2 — Mobile API Route Registrar Adapter

Bu paket, mobil API route parçalama sonrası kalan imza uyumsuzluğunu düzeltir.

## Hata

```text
TypeError: register_mobile_performance_read_routes_v1() takes 1 positional argument but 2 were given
_register_mobile_performance_read_routes_v1(mobile_bp, globals())
```

## Ne yapar?

- `routes.py` içine güvenli route registrar adapter ekler.
- `register_mobile_performance_read_routes_v1` çağrısını adapter üzerinden yapar.
- Adapter önce `(bp, globals())`, olmazsa `(bp)` ile çağırır.
- Böylece hem 1 parametre hem 2 parametre bekleyen route kayıt fonksiyonları desteklenir.
- Yedek alır, silme yapmaz.

## Kullanım

Önce çalışan Waitress ekranında `Ctrl + C` ile durdur.

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MOBILE_API_ROUTE_REGISTRAR_ADAPTER_P14F2_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_p14f2_mobile_api_route_registrar_adapter.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_p14f2_mobile_api_route_registrar_adapter.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_p14f2_mobile_api_route_registrar_adapter.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts
```

Sonra uygulamayı tekrar başlat:

```powershell
python -m waitress --listen=0.0.0.0:8000 --threads=12 --no-log-socket-errors wsgi:app
```

Beklenen: `Mobile real API routes` optional startup hatası görünmemeli. Eğer yeni bir route registrar adı çıkarsa aynı adapter kapsamına alınır.
