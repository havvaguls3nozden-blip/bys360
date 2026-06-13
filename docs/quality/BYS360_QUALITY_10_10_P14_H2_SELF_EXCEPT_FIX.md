# BYS360 Quality 10/10 P14-H2 — Self Except Fix

P14-H başarıyla çalıştıktan sonra kendi scriptinde kalan tek `EXCEPT_WITHOUT_LOG` bulgusunu kapatır.

## Kalan bulgu

```text
scripts/quality/apply_p14_h_p1_cleanup_v1.py line=197
rule=EXCEPT_WITHOUT_LOG
```

## Ne yapar?

- Sadece `scripts/quality/apply_p14_h_p1_cleanup_v1.py` dosyasına dokunur.
- Loglanmamış `except` bloğuna `LOGGER.warning(...)` ekler.
- Gerekirse `import logging` ve `LOGGER = logging.getLogger(__name__)` ekler.
- Asistan, base.html, performans, mobil API ve çalışan kaynak dosyalara dokunmaz.
- Yedek alır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_H2_SELF_EXCEPT_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_h2_self_except_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_h2_self_except_fix.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p14_h2_self_except_fix.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 240
```

## Beklenen

```text
P0=0
P1=50
45 | TECHNICAL_UI_TERM
4  | LARGE_FILE_HARD
1  | MANY_REPAIR_SCRIPTS
```
