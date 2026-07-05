# BYS360 Teknik Borç Faz 2B — Script Arşiv Adayları Runbook

Bu araç, Phase 2B scripts envanterinde `archive_candidate` olarak sınıflanan tek seferlik hotfix/repair/overlay scriptlerini repo dışı arşive taşımak için kullanılır.

## Güvenlik ilkesi

- `tooling_keep` dosyalarına dokunmaz.
- `review` dosyalarına dokunmaz.
- Sadece `archive_candidate` dosyaları işler.
- Apply modunda dosyalar silinmez; `C:\bys360\archive` altında zaman damgalı klasöre taşınır.
- Canlı sistem, canlı veritabanı ve servis davranışı değiştirilmez.

## Kullanım

Önce Phase 2B inventory audit çalışmış olmalıdır:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2b_scripts.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode audit `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2b"
```

Dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2b_archive_candidates.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode dry-run `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2b"
```

Apply:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2b_archive_candidates.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode apply `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2b"
```
