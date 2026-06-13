# BYS360 Quality 10/10 P13-F2 — Repair Inventory Logger Fix

P13-F `print()` eklediği için kalite kuralı hâlâ `EXCEPT_WITHOUT_LOG` uyarısını verdi. Bu paket `print()` yerine gerçek logger kullanır.

## Hedef

```text
scripts/quality/analyze_p13_b_repair_script_inventory_v1.py
```

## Ne yapar?

- `import logging` ekler.
- `LOGGER = logging.getLogger(__name__)` ekler.
- Sessiz/print tabanlı `except` bloğunu `LOGGER.warning(...)` ile düzeltir.
- Uygulama koduna dokunmaz.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_F2_REPAIR_INVENTORY_LOGGER_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_f2_repair_inventory_logger_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_f2_repair_inventory_logger_fix.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

## Beklenen

```text
P0: 0
P1: 50
EXCEPT_WITHOUT_LOG görünmemeli
```
