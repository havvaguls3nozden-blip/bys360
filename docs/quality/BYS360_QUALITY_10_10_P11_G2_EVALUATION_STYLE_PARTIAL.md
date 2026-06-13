# BYS360 Quality 10/10 P11-G2 — Evaluation Form Style Partial

Bu paket `app/templates/evaluation_form.html` içindeki güvenli `<style>...</style>` bloğunu ayrı partial dosyaya taşır.

## Ne yapar?

- `evaluation_form.html` içindeki tek inline style bloğunu bulur.
- Bloğu `app/templates/partials/evaluation_form/_evaluation_form_styles.html` dosyasına taşır.
- Eski yerde sadece şu include satırını bırakır:

```jinja
{% include 'partials/evaluation_form/_evaluation_form_styles.html' %}
```

## Neye dokunmaz?

- Form başlangıç/bitişine
- Input `name/id` değerlerine
- CSRF alanına
- Jinja kriter/puanlama döngülerine
- Submit/kaydet davranışına
- Script bloğuna

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_G2_EVALUATION_STYLE_PARTIAL_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_g2_evaluation_style_partial.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_g2_evaluation_style_partial.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 120
```

Beklenen:

- P0 sıfır kalır.
- `evaluation_form.html` büyük dosya listesinden çıkar.
- P1 yaklaşık 53 → 52 düşer.
