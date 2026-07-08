# BYS360 Quality 10/10 P11-E1 — Effective Menu Dependency / Candidate Analizi

Bu paket kod değiştirmez. `app/services/settings/effective_menu.py` için güvenli taşıma adaylarını ve bağımlılıkları çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_E1_EFFECTIVE_MENU_DEPENDENCY_CANDIDATES_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_e1_effective_menu_dependency_candidates.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_e1_effective_menu_dependency_candidates_v1.json
reports/quality/bys360_quality_10_10_p11_e1_effective_menu_dependency_candidates_v1.md
```

## Neden?

`effective_menu.py` menü görünürlüğünü, rol matrisini ve kişi bazlı yetkiyi etkiler. Yanlış refactor menülerin yanlış görünmesine veya beyaz sayfaya neden olabilir. Bu yüzden ilk gerçek taşıma öncesi dependency/candidate analizi yapılır.
