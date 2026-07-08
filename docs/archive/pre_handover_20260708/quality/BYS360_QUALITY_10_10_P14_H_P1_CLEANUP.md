# BYS360 Quality 10/10 P14-H — P1 Cleanup

Bu paket P0 temizlendikten sonra kalan P1 artışlarını toparlar.

## Hedefler

P7 güncel çıktısına göre:

```text
3 | EXCEPT_WITHOUT_LOG
2 | reports/quality/...preview.js kaynaklı LARGE_FILE_HARD
```

## Ne yapar?

- Şu dosyalardaki `EXCEPT_WITHOUT_LOG` bloklarına `LOGGER.warning(...)` ekler:
  - `app/services/performance/period_delete_service.py`
  - `app/services/performance/scoring_window_policy.py`
  - `scripts/quality/apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py`
- Şu büyük preview JS raporlarını `.quality_backup` altına taşır:
  - `reports/quality/bys360_quality_10_10_p14_e2_assistant_module_applied_preview.js`
  - `reports/quality/bys360_quality_10_10_p14_e2_assistant_module_dryrun_preview.js`
- Asistanın çalışan `app/static/js/bys360_assistant_module.js` dosyasına dokunmaz.
- `base.html` dosyasına dokunmaz.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_H_P1_CLEANUP_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

Önce dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_h_p1_cleanup.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

Sonra uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p14_h_p1_cleanup.ps1 -ProjectRoot "C:\bys360\project"
```

Kontrol:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p14_h_p1_cleanup.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 240
```

## Beklenen

```text
P0=0
P1 yaklaşık 50
EXCEPT_WITHOUT_LOG görünmemeli
LARGE_FILE_HARD 4'e inmeli
```
