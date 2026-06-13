# BYS360 S0F2 Pip-Audit Wave1 Runtime Verify

Tarih: 2026-06-13T10:14:11

## Sonuç

- OK: True
- Karar: S0F2_GREEN_RUNTIME_FIXED
- Vulnerability count after: 1
- Wave1 vulnerability count after: 0
- Deferred vulnerability count after: 1
- Other vulnerability count after: 0
- Compileall returncode: 0
- Pytest quality smoke returncode: 0
- Pytest full returncode: 0
- Pytest default returncode: 0

## Package Versions

```json
{
  "cryptography": "49.0.0",
  "flask": "3.1.3",
  "pillow": "12.2.0",
  "pytest": "8.4.2",
  "python-dotenv": "1.2.2",
  "waitress": "3.0.2"
}
```

## By Package After

```json
{
  "pytest": 1
}
```

## Remaining Findings

```json
[
  {
    "package": "pytest",
    "installed_version": "8.4.2",
    "vulnerability_id": "GHSA-6w46-j5rx-g56g",
    "aliases": [
      "CVE-2025-71176"
    ],
    "fix_versions": [
      "9.0.3"
    ],
    "description_present": true
  }
]
```

## S0A Rerun

```json
{
  "returncode": 0,
  "ok": true,
  "red_flag_count": 2,
  "pip_audit_available": true,
  "pip_audit_vulnerability_count": 1,
  "old_venv_total_mb": 197.11
}
```

## Pytest Full Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Pytest Default Summary

```json
{
  "passed": 744,
  "skipped": 2,
  "deselected": 34,
  "failed": 0,
  "errors": 0,
  "warnings": 0
}
```

## Sonraki Adım

S0F3 pytest zafiyeti için ayrı test-altyapısı dalgası değerlendirilebilir; riskli bulunursa S0G eski venv temizliğine geçilebilir.