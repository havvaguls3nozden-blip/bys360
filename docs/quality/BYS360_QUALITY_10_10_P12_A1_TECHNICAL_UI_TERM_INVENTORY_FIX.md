# BYS360 Quality 10/10 P12-A1 — Technical UI Term Inventory Fix

P12-A ilk çalışmada `technical_ui_term_count=0` döndürürse bu paket kullanılmalıdır. Bu sürüm yalnızca clean audit raporunu değil, P7 analizinin ürettiği `bys360_quality_10_10_p1_analysis_v1.json` raporunu da okur.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P12_A1_TECHNICAL_UI_TERM_INVENTORY_FIX_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p12_a1_technical_ui_term_inventory_fix.ps1 -ProjectRoot "C:\bys360\project" -Limit 200
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p12_a1_technical_ui_term_inventory_fix_v1.json
reports/quality/bys360_quality_10_10_p12_a1_technical_ui_term_inventory_fix_v1.md
```

## Güvenlik

Bu paket kod değiştirmez. Sadece teknik UI terimlerini doğru kaynak rapordan okur ve P12-B için güvenli adayları sınıflandırır.
