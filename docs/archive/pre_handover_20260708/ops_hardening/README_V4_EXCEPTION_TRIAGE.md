# BYS360 OPS Hardening V4 — Exception Triage

Bu overlay kod değiştirmez. Canlı aday kod içindeki `except Exception` bloklarını risk seviyesine göre sınıflandırır.

Çalıştırma:

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ops_hardening_v4_exception_triage.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Rapor:

`reports\quality\BYS360_OPS_HARDENING_V4_EXCEPTION_TRIAGE_REPORT.md`

Riskler:

- P0: kritik canlı yol + sessiz/zayıf hata yakalama
- P1: kritik canlı yol + geniş exception
- P2: daha düşük öncelikli ama temizlenmesi gereken kayıtlar
- P3: loglanan veya tekrar yükseltilen geniş exception, refactor adayı
