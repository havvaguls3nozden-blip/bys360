# BYS360 Score100 Handover + Security V1 Overlay

Bu overlay, 100/100 hedefinde ilk somut adımı kapatır:

- kök `DEPLOYMENT.md`, `BACKUP_RUNBOOK.md`, `SECURITY.md`
- gerçek devir/handover doküman seti
- release zip preflight kontrolü
- handover doküman kalite gate’i
- static test sözleşmesi

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_SCORE100_HANDOVER_SECURITY_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Kontrol

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_handover_docs_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode gate
pytest tests\test_score100_handover_docs_contract_v1.py
```

## Temiz release

```powershell
python scripts\security\build_bys360_secure_release_v1_5.py --project-root "C:\bys360\project"
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_release_zip_preflight_v1.ps1 -ProjectRoot "C:\bys360\project" -ZipPath "C:\bys360\project\dist_secure\BYS360_SECURE_RELEASE_V1_5_*.zip"
```
