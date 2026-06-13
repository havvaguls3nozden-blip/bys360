# BYS360 Quality 10/10 P11-B1A — Mobile Routes Decorator Fix + Split Candidate Analizi

P11-B1 ilk denemede route fonksiyonlarını göremediyse sebep büyük ihtimalle `.get(...)`, `.post(...)`, `.put(...)`, `.patch(...)`, `.delete(...)` decorator kısayollarının yakalanmamasıdır.

Bu paket kod değiştirmez. Sadece analiz scriptini geliştirir.

## Desteklenen decorator tipleri

- `@...route(...)`
- `@...get(...)`
- `@...post(...)`
- `@...put(...)`
- `@...patch(...)`
- `@...delete(...)`

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_B1A_MOBILE_ROUTES_DECORATOR_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_b1a_mobile_routes_split_candidates.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_b1a_mobile_routes_split_candidates_v1.json
reports/quality/bys360_quality_10_10_p11_b1a_mobile_routes_split_candidates_v1.md
```
