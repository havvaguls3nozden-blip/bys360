# BYS360 Quality 10/10 P11-H1 — CSS Wrapper Split

Bu paket `app/static/css/performance_phase3.css` dosyasını güvenli wrapper/import yapısına alır.

## Mantık

- HTML tarafındaki CSS referansı değişmez.
- `performance_phase3.css` küçük bir wrapper dosyasına dönüşür.
- Orijinal CSS içeriği `app/static/css/performance_phase3_parts/` altında sırası korunarak parçalara ayrılır.
- CSS blokları top-level kapanış noktalarında bölünür; blok ortasından kesilmez.
- Uygulama öncesi orijinal dosya `.quality_backup` altına yedeklenir.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_H1_CSS_WRAPPER_SPLIT_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Önce dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_h1_css_wrapper_split.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_h1_css_wrapper_split.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 120
```

Beklenen:

- P0 sıfır kalır.
- `app/static/css/performance_phase3.css` artık `LARGE_FILE_HARD` listesinden çıkar.
- Eğer kalite aracı parça CSS dosyalarını da tarıyorsa her parça 450 satır civarında olduğu için yeni büyük dosya uyarısı üretmemelidir.
