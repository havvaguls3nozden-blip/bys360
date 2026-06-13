# BYS360 Quality 10/10 P11-F1 — Settings Style Partial

Bu paket `app/templates/settings.html` içindeki güvenli `<style>...</style>` bloğunu ayrı partial dosyaya taşır.

## Ne yapar?

- `settings.html` içindeki tek inline style bloğunu bulur.
- Bloğu `app/templates/partials/settings/_settings_styles.html` dosyasına taşır.
- Eski yerde sadece şu include satırını bırakır:

```jinja
{% include 'partials/settings/_settings_styles.html' %}
```

## Neye dokunmaz?

- Rol matrisi kaydetme mantığına
- Kişi bazlı menü görünürlüğüne
- Form başlangıç/bitişine
- Input `name/id` değerlerine
- CSRF alanına
- Script/fetch davranışına

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_F1_SETTINGS_STYLE_PARTIAL_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_f1_settings_style_partial.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_f1_settings_style_partial.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 120
```

Beklenen:

- P0 sıfır kalır.
- `settings.html` büyük dosya listesinden çıkar.
- P1 yaklaşık 52 → 51 düşer.
