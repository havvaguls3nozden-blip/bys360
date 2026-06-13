# BYS360 Quality 10/10 P3 — Clean Audit / Backup Hariç Rapor

P2 tek dosya düzeltmeleri başarılı olmasına rağmen P0 sayısı artmış görünebilir. Bunun sebebi denetim aracının `.quality_backup` ve `versions_BACKUP...` gibi yedek klasörleri de taramasıdır.

Bu paket, mevcut audit raporunu üretir; ardından yedek klasörlerden gelen bulguları temizleyip ayrı bir temiz rapor oluşturur.

## Komut

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P3_CLEAN_AUDIT_EXCLUDE_BACKUPS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

## Çıktı

Temiz rapor:

```text
reports\quality\bys360_quality_10_10_audit_v1_clean.json
```

Bu aşamada strict kapı için `-FailOn P0` kullanmayın; önce gerçek P0 sayısını görüp küçük dosya hedefleriyle devam edeceğiz.
