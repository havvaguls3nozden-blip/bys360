# BYS360 Teknik Borç Faz 2B — Scripts Envanteri Runbook

Amaç: `scripts/` klasöründeki aktif, legacy, tek seferlik, güvenlik, kalite ve canlı müdahale scriptlerini sınıflandırmak.

Bu faz sadece okuma/audit yapar. Dosya taşımaz, silmez, değiştirmez.

Önerilen kullanım:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2b_scripts.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode audit `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2b"
```

Beklenen çıktılar:

- `BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.md`
- `BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.json`
- `BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.csv`

Sınıflandırmalar:

- `keep_active`: Güncel bakım, kalite kapısı, güvenlik veya teknik borç aracı olarak tutulması önerilen script.
- `review`: Canlı, güvenlik, migration veya kritik modül etkisi nedeniyle manuel bakılması gereken script.
- `archive_candidate`: Tek seferlik hotfix/repair/overlay/diff kanıtı gibi dış arşive taşınmaya aday script.
- `tooling_keep`: PowerShell wrapper, faz araçları ve kalite araçları gibi repo içinde kalabilecek yardımcı script.

Apply yapılmaz. Uygulama/taşıma için ayrı Faz 2B-apply paketi hazırlanmalıdır.
