# BYS360 Quality 10/10 P9.4 — Flutter Analyze Info Temizliği

P9.3 sonrası kalite denetiminde P0 sıfır kalmış, P1 59 seviyesine inmiştir. Flutter analyze tarafında hata değil, 13 adet info/lint kalmıştır.

Bu paket `dart fix` üzerinden güvenli mobil lint temizliği yapar.

## Önce checkpoint

```powershell
cd C:\bys360

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Compress-Archive -Path "C:\bys360\project" -DestinationPath "C:\bys360\BYS360_QUALITY_CHECKPOINT_P1_59_BEFORE_P9_4_$stamp.zip" -Force
```

## Paketi uygula

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P9_4_FLUTTER_ANALYZE_INFO_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_4_flutter_analyze_info_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_4_flutter_analyze_info_fix.ps1 -ProjectRoot "C:\bys360\project"
```

## Son kontrol

```powershell
cd C:\bys360\project

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 120
```

Beklenen:

- `flutter analyze` temiz veya daha az info verir.
- P0 sıfır kalır.
- P1 yaklaşık 59 seviyesinde kalabilir veya biraz düşebilir.
- Kalan P1 ana yükü `LARGE_FILE_HARD` ve `MANY_REPAIR_SCRIPTS` olacaktır.
