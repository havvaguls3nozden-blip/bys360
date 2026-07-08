# BYS360 CI Hardening SAFE V1

Bu paket Aşama 1 ve Aşama 2 sonunda temizlenen risklerin CI içinde tekrar oluşmasını engellemek için hazırlanmıştır.

Eklenen/garanti edilen kapılar:

- `python -m ruff check app --select F821`
- `python -m compileall -q app config.py wsgi.py run.py scripts`
- `python scripts/quality/bys360_secret_repo_gate.py --root .`
- `python scripts/release/build_bys360_safe_release.py --root . --output reports/quality/BYS360_SAFE_RELEASE_CI_AUDIT.zip --audit-only`
- `python scripts/quality/bys360_quality9_ci_gate.py --root .`
- `pip-audit` için bağımlılık kurulumu

Windows uygulama komutu:

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_CI_HARDENING_SAFE_V1_OVERLAY.zip" `
  -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ci_hardening_safe_v1.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode all `
  -RunChecks
```

Başarılı sonuçta `reports\quality\BYS360_CI_HARDENING_SAFE_V1_REPORT.json` içinde tüm kontroller `true` görünmelidir.
