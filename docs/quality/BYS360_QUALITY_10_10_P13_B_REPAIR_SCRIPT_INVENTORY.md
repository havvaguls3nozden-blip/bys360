# BYS360 Quality 10/10 P13-B — Repair/Check Script Inventory

Bu paket kod değiştirmez ve script silmez. P13-A sonrası kalan `MANY_REPAIR_SCRIPTS` gerçek aksiyonu için script envanteri çıkarır.

## Ne yapar?

- `scripts/windows`, `scripts/quality`, `scripts/security`, `app/scripts/windows`, `app/scripts/quality` klasörlerini tarar.
- Scriptleri türlerine göre ayırır:
  - analysis/report
  - check/gate
  - repair/fix
  - build/release
  - security
  - split/packaging
- Arşiv adayı, tutulacak aktif zincir ve destructive manuel inceleme listesi üretir.
- Hiçbir dosyayı taşımaz veya silmez.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_B_REPAIR_SCRIPT_INVENTORY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p13_b_repair_script_inventory.ps1 -ProjectRoot "C:\bys360\project" -Limit 240
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p13_b_repair_script_inventory_v1.json
reports/quality/bys360_quality_10_10_p13_b_repair_script_inventory_v1.md
```

## Güvenlik

Bu aşamada arşivleme bile yapılmaz. P13-C hazırlanırsa yalnızca dry-run move listesi üretilecek; dosya silme olmayacaktır.
