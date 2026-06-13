# BYS360 Clean Handover Source P1 Report

Generated at: `2026-06-08T12:16:34`
Project root: `C:\bys360\releases\BYS360_CLEAN_HANDOVER_SOURCE_P1`

## Summary

| Metric | Value |
|---|---:|
| All files | 3488 |
| All size MB | 30.94 |
| Clean handover candidate files | 3488 |
| Clean handover candidate size MB | 30.94 |
| Excluded files | 0 |
| Excluded size MB | 0.0 |

## Exclusion reasons

| Reason | Files | Size MB |
|---|---:|---:|

## Largest top-level areas by size

| Path | Size MB |
|---|---:|
| `app` | 22.34 |
| `scripts` | 5.78 |
| `mobile_flutter` | 1.12 |
| `CLEAN_PACKAGE_MANIFEST.json` | 0.67 |
| `migrations` | 0.43 |
| `tests` | 0.3 |
| `docs` | 0.18 |
| `sql` | 0.05 |
| `config` | 0.03 |
| `BYS360_REPO_BLOAT_CLEANUP_P1_OVERLAY` | 0.02 |
| `config.py` | 0.02 |
| `.env.example` | 0.0 |
| `.gitignore` | 0.0 |
| `pyproject.toml` | 0.0 |
| `.env.production.example` | 0.0 |
| `pytest.ini` | 0.0 |
| `run_server.py` | 0.0 |
| `README_BYS360_REPO_BLOAT_CLEANUP_P1.md` | 0.0 |
| `SECURITY_HANDOVER_NOTE.md` | 0.0 |
| `release_manifest.json` | 0.0 |

## Next action

Recommended first run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_bloat_cleanup_p1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_bloat_cleanup_p1.ps1 -ProjectRoot "C:\bys360\project" -Mode clean-copy -OutputRoot "C:\bys360\releases\BYS360_CLEAN_HANDOVER_SOURCE_P1"
```
