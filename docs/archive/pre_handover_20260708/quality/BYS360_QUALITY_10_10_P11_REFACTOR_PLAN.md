# BYS360 Quality 10/10 P11 — Büyük Dosya Refactor Planı

Bu paket kod değiştirmez. P10.2 ile aktif P1 kalmadığı doğrulandıktan sonra kalan planlı P1 maddeleri için refactor ve süreç planı üretir.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_REFACTOR_PLAN_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_refactor_plan.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_refactor_plan_v1.json
reports/quality/bys360_quality_10_10_p11_refactor_plan_v1.md
```

## Amaç

- `LARGE_FILE_HARD` kayıtlarını doğrudan parçalamadan önce güvenli sıraya koymak.
- Her dosya için risk, strateji ve smoke test belirlemek.
- `MANY_REPAIR_SCRIPTS` uyarısını CI/arşiv planına taşımak.
