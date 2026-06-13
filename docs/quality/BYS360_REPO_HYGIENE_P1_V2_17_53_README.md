# BYS360 Repo Hijyeni P1 V2.17.53

Bu overlay uygulama iş kodunu değiştirmez. `__pycache__`, `*.pyc`, `*.bak` ve geçici backup kalıntılarını güvenli şekilde karantinaya alır, `.gitignore` kurallarını güçlendirir ve rapor üretir.

## Kullanım

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_REPO_HYGIENE_P1_V2_17_53_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p1_v2_17_53.ps1 -ProjectRoot "C:\bys360\project" -Mode audit

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p1_v2_17_53.ps1 -ProjectRoot "C:\bys360\project" -Mode all

notepad .\reports\quality\bys360_repo_hygiene_p1_v2_17_53_report.md
```

## Not

Git repo yoksa `git rm` komutları çalıştırılmaz. Eğer gerçek Git repo ayrı klasördeyse Git index/geçmiş temizliği orada yapılmalıdır.
