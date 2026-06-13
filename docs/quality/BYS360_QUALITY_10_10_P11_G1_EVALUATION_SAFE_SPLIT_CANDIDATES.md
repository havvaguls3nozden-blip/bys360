# BYS360 Quality 10/10 P11-G1 — Evaluation Form Güvenli Split Adayları

Bu paket kod değiştirmez. `app/templates/evaluation_form.html` için güvenli partial adaylarını çıkarır.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_G1_EVALUATION_SAFE_SPLIT_CANDIDATES_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_g1_evaluation_safe_split_candidates.ps1 -ProjectRoot "C:\bys360\project" -Limit 120
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_g1_evaluation_safe_split_candidates_v1.json
reports/quality/bys360_quality_10_10_p11_g1_evaluation_safe_split_candidates_v1.md
```

## Güvenlik

Bu aşamada form, input, name/id, CSRF, puanlama kriter döngüsü ve script davranışlarına dokunulmaz. Amaç yalnızca ilk güvenli partial adayını belirlemektir.
