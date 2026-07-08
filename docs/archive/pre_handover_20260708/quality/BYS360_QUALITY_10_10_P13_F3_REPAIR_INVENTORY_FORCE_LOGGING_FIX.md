# BYS360 Quality 10/10 P13-F3 — Repair Inventory Force Logging Fix

F2 sonrasında kalite kuralı hâlâ `EXCEPT_WITHOUT_LOG` görürse bu paket kullanılır.

## Hedef

```text
scripts/quality/analyze_p13_b_repair_script_inventory_v1.py
```

## Ne yapar?

- `import logging` yoksa ekler.
- Log/raise bulunmayan `except` bloklarına doğrudan `logging.warning(...)` ekler.
- `continue` davranışı varsa korur.
- Uygulama koduna dokunmaz.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_F3_REPAIR_INVENTORY_FORCE_LOGGING_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_f3_repair_inventory_force_logging_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_f3_repair_inventory_force_logging_fix.ps1 -ProjectRoot "C:\bys360\project"
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
