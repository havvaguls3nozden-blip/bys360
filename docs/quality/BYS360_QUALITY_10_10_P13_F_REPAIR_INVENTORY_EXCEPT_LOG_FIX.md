# BYS360 Quality 10/10 P13-F — Repair Inventory Except Log Fix

Bu paket uygulama kodunu değiştirmez. Yalnızca kalite yardımcı scriptindeki 1 adet P1 bulgusunu düzeltir:

```text
scripts/quality/analyze_p13_b_repair_script_inventory_v1.py
rule=EXCEPT_WITHOUT_LOG
```

## Ne değişir?

Sessiz `except ... continue/pass` bloğuna uyarı mesajı eklenir. Böylece hata yutulmaz; fakat scriptin güvenli tarama davranışı korunur.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_F_REPAIR_INVENTORY_EXCEPT_LOG_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_f_repair_inventory_except_log_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_f_repair_inventory_except_log_fix.ps1 -ProjectRoot "C:\bys360\project"
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
EXCEPT_WITHOUT_LOG artık görünmemeli
```
