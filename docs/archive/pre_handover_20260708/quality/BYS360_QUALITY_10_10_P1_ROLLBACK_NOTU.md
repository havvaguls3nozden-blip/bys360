# BYS360 Quality 10/10 P1 Rollback

Bu paket, `BYS360_QUALITY_10_10_P1_SILENT_EXCEPT_LOGGING_OVERLAY` sonrasında oluşan Python syntax/girinti bozulmalarını geri almak için hazırlanmıştır.

## Neden gerekli?

P1 silent-except repair scripti çok geniş kapsamda 49 dosyaya müdahale etmiş, 162 bloğu patchlemiş ve bazı dosyalarda `try/except` yapısını bozmuştur. Bu yüzden önce backup klasöründen geri dönülmelidir.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P1_ROLLBACK_SAFE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\rollback_bys360_quality_10_10_p1_silent_except_logging.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\rollback_bys360_quality_10_10_p1_silent_except_logging.ps1 -ProjectRoot "C:\bys360\project"

powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_bys360_quality_10_10_p1_rollback.ps1 -ProjectRoot "C:\bys360\project"
```

## Beklenen sonuç

- `python -m compileall app scripts` yeniden temiz geçmeli.
- P0 sayısı P1 bozulmasından önceki seviyeye dönmeli.
- `.quality_backup/silent_except_logging_v1_*` klasörü yedek olarak kalır.
