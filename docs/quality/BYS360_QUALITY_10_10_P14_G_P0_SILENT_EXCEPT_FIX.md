# BYS360 Quality 10/10 P14-G — P0 Silent Except Fix

Bu paket yalnızca kalan P0 bulgularını hedefler.

## Kalan P0

```text
app/services/performance/period_delete_service.py line=212
scripts/quality/apply_p14f1_mobile_api_blueprint_name_fix_v1.py line=82
scripts/quality/apply_p14f2_mobile_api_route_registrar_adapter_v1.py line=179
```

## Ne yapar?

- Sessiz `except: pass` / `except ...: pass` bloklarını gerçek `LOGGER.warning(...)` ile değiştirir.
- Gerekirse `import logging` ve `LOGGER = logging.getLogger(__name__)` ekler.
- Asistan JS, base.html veya mobil route davranışına dokunmaz.
- Yedek alır.
- Compile kontrolü yapar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_G_P0_SILENT_EXCEPT_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_g_p0_silent_except_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_g_p0_silent_except_fix.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p14_g_p0_silent_except_fix.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\list_bys360_quality_10_10_p6_remaining_p0.ps1 -ProjectRoot "C:\bys360\project"

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

## Beklenen

```text
remaining_silent_p0_found=0
P0=0
```
