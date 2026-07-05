# BYS360 Teknik Borç Faz 2C — Secret Sinyali Sınıflandırma Runbook

Bu faz kod davranışını değiştirmez.

Amaç:
- `secret_like_text` sayısını panik üretmeden sınıflandırmak.
- Gerçek literal secret adaylarını `needs_review` olarak ayırmak.
- Güvenlik terimi, test, audit, placeholder ve environment/config okuma kaynaklı false-positive sinyalleri ayırmak.

Çalıştırma:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2c_secret_signals.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode audit `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2c"
```

Üretilen çıktılar:
- `BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.md`
- `BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.json`
- `BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.csv`

Not:
- Rapor bağlamları redakte eder.
- Değerleri açık şekilde rapora yazmaz.
- `.git`, `.venv`, `archive`, `backups`, `logs`, `instance` ve teknik borç rapor klasörlerini tarama dışında bırakır.