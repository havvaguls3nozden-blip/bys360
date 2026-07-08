# BYS360 Quality 10/10 P13-E — Analysis Script P0 Fix

Bu paket uygulama kodunu değiştirmez. Sadece kalite analiz yardımcı scriptlerinde kalan 2 adet `except ... pass` P0 bulgusunu düzeltir.

## Düzeltilen dosyalar

```text
scripts/quality/analyze_p12_b_technical_ui_term_decision_v1.py
scripts/quality/analyze_p13_a_effective_p1_closure_map_v1.py
```

## Ne değişir?

Sessiz `except ... pass` yerine uyarı basan güvenli hata yakalama kullanılır.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_E_ANALYSIS_SCRIPT_P0_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_e_analysis_script_p0_fix.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p13_e_analysis_script_p0_fix.ps1 -ProjectRoot "C:\bys360\project"
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
