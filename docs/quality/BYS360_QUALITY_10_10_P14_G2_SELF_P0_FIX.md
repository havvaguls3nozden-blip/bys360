# BYS360 Quality 10/10 P14-G2 — Self P0 Fix

P14-G ana P0 bulgularını kapattıktan sonra kendi scriptinde kalan tek P0’u düzeltir.

## Kalan P0

```text
scripts/quality/apply_p14_g_p0_silent_except_fix_v1.py line=206
rule=SILENT_EXCEPT_PASS
```

## Ne yapar?

- Sadece `scripts/quality/apply_p14_g_p0_silent_except_fix_v1.py` dosyasına dokunur.
- Sessiz `except/pass` bloğunu `LOGGER.warning(...)` ile değiştirir.
- Gerekirse `import logging` ve `LOGGER = logging.getLogger(__name__)` ekler.
- Asistan, base.html, performans ve mobil dosyalarına dokunmaz.
- Yedek alır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_G2_SELF_P0_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_g2_self_p0_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_g2_self_p0_fix.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p14_g2_self_p0_fix.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\list_bys360_quality_10_10_p6_remaining_p0.ps1 -ProjectRoot "C:\bys360\project"

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

## Beklenen

```text
remaining_silent_p0_found=0
P0=0
```
