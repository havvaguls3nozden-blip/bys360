# BYS360 Teknik Borç Faz 2 Runbook

## Amaç

Faz 2, Faz 1'de temiz kaynak ayrımı yapıldıktan sonra kalan teknik borç alanlarını sınıflandırır.
Bu faz kod davranışını değiştirmez; yalnızca audit raporu üretir.

## Ölçülen ana alanlar

- `reports/quality` kalabalığı
- `scripts` klasörü büyüklüğü
- büyük dosya / god-object adayları
- route hotspot dosyaları
- kullanıcıya görünebilecek teknik dil sinyalleri
- `print` kullanımları
- broad/bare `except` kullanımları
- hardcoded localhost / yerel IP sinyalleri
- secret benzeri metin sinyalleri

## Çalıştırma

```powershell
cd C:\bys360\project

powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_tech_debt_phase2.ps1 `
  -ProjectRoot "C:\bys360\project" `
  -Mode audit `
  -OutputRoot "C:\bys360\reports\tech_debt_phase2"
```

## Beklenen çıktılar

- `C:\bys360\reports\tech_debt_phase2\BYS360_TECH_DEBT_PHASE2_REPORT.md`
- `C:\bys360\reports\tech_debt_phase2\BYS360_TECH_DEBT_PHASE2_AUDIT.json`
- `C:\bys360\reports\tech_debt_phase2\BYS360_TECH_DEBT_PHASE2_FILE_CANDIDATES.csv`

## Güvenlik

Bu script canlı sisteme, veritabanına, migration dosyalarına veya uygulama davranışına dokunmaz.
Sadece dosya okur ve rapor üretir.
