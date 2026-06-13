# BYS360 Quality 10/10 P13-A2 — Effective P1 Closure Map Corrected

P13-A ham özetinde çift sayım oluşursa bu paket kullanılır. P13-A2, P1 kural özetini yalnızca P7 analiz raporundan okur ve clean report ile tekrar birleştirip bulguları şişirmez.

## Ne düzeltir?

P13-A çıktısında görülebilecek şu hatalı özetleri düzeltir:

```text
46 | TECHNICAL_UI_TERM
8  | LARGE_FILE_HARD
2  | MANY_REPAIR_SCRIPTS
```

Doğru beklenen kaynak P7 analizidir:

```text
45 | TECHNICAL_UI_TERM
4  | LARGE_FILE_HARD
1  | MANY_REPAIR_SCRIPTS
```

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_A2_EFFECTIVE_P1_CLOSURE_MAP_CORRECTED_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p13_a2_effective_p1_closure_map_corrected.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p13_a2_effective_p1_closure_map_corrected_v1.json
reports/quality/bys360_quality_10_10_p13_a2_effective_p1_closure_map_corrected_v1.md
```

## Güvenlik

Bu paket kod değiştirmez. Sadece kapanış/karar raporu üretir.
