# BYS360 Mobile Consistency V2.17.64

Bu overlay, BYS360 mobil klasöründeki sürüm, API base URL ve WebView kalıntısı/tutarlılık kontrolünü yapar.

## Kapsam

- `pubspec.yaml` sürümünü mobil kod içindeki en güncel `V2_8_x` marker ile uyumlu hale getirir.
- `MobileApiClient` varsayılan API adresini canlı HTTPS adresiyle uyumlu yapar.
- WebView kullanımını kaldırmaz; yalnızca portal köprü kullanımıyla sınırlı olup olmadığını raporlar.
- V2.17.61 onarım scriptinde görülen küçük `SyntaxWarning: invalid escape sequence '\/'` uyarısını temizler.
- Raporları `reports/` klasörüne yazar.

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_MOBILE_CONSISTENCY_V2_17_64_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_mobile_consistency_v2_17_64.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

İsteğe bağlı Flutter analiz:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_mobile_consistency_v2_17_64.ps1 -ProjectRoot "C:\bys360\project" -Mode all -DartAnalyze
```
