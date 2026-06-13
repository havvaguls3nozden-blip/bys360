# BYS360 Quality 10/10 P13-C — Repair Script Archive Dry-Run

Bu paket hiçbir dosya taşımaz veya silmez. P13-B envanterinden çıkan güvenli arşiv adayları için yalnızca dry-run taşıma planı üretir.

## Ne yapar?

- P13-B raporunu okur.
- Sadece `ARCHIVE_CANDIDATE_*` kararına sahip dosyaları plana alır.
- `REVIEW_DESTRUCTIVE_SCRIPT_BEFORE_ARCHIVE` dosyalarını özellikle bloke eder.
- `KEEP_ACTIVE_QUALITY_CHAIN` ve `KEEP_REFERENCED_TOOL` dosyalarına dokunmaz.
- Rapor üretir.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_C_REPAIR_SCRIPT_ARCHIVE_DRYRUN_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p13_c_repair_script_archive_dryrun.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p13_c_repair_script_archive_dryrun_v1.json
reports/quality/bys360_quality_10_10_p13_c_repair_script_archive_dryrun_v1.md
reports/quality/bys360_quality_10_10_p13_c_repair_script_archive_dryrun_preview.ps1
```

## Güvenlik

Bu aşama sadece plan üretir. P13-D ayrıca istenirse ve full checkpoint alındıktan sonra uygulanabilir; onda bile silme değil yalnızca arşiv klasörüne taşıma yapılmalıdır.
