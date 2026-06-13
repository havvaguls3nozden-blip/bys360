# BYS360 Quality 10/10 P13-E2 — P12-B Last P0 Fix

Bu paket uygulama kodunu değiştirmez. Sadece kalan tek P0 bulgusunu hedefler:

```text
scripts/quality/analyze_p12_b_technical_ui_term_decision_v1.py
```

## Neden gerekli?

P13-E iki bulgudan birini düzeltti. Kalan P12-B bloğunda boşluk/format farkı olduğu için ilk kalıp eşleşmedi. P13-E2 satır bazlı daha esnek çalışır.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_E2_P12B_LAST_P0_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_e2_p12b_last_p0_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_e2_p12b_last_p0_fix.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\list_bys360_quality_10_10_p6_remaining_p0.ps1 -ProjectRoot "C:\bys360\project"
```

## Beklenen

```text
P0: 0
remaining_silent_p0_found=0
```
