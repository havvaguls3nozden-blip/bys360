# BYS360 Quality 10/10 P8.1 — P1 EXCEPT_WITHOUT_LOG Tek Satır Except Düzeltmesi

P8 aracı normal çok satırlı `except` bloklarında çalışır. Ancak `except Exception: pass` gibi tek satırlı except bloklarında log satırını yanlış yere ekleyebilir. Bu paket aynı dosya adlarıyla P8 aracını günceller.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P8_1_P1_EXCEPT_LOG_SINGLE_LINE_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts
```

## Devam

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p8_p1_except_without_log.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p8_p1_except_without_log.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

Beklenen: P0 sıfır kalır, P1 bir azalır.
