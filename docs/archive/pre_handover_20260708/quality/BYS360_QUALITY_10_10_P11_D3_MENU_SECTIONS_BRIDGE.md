# BYS360 Quality 10/10 P11-D3 — Menu Sections Bridge

Bu paket `app/menu_registry.py` içindeki `MENU_SECTIONS` bloğunu ve bağlı olduğu `ANNOUNCEMENT_TOOL_ROLES` sabitini ayrı data modülüne taşır.

## Güvenlik şartı

Script yalnızca şu koşullar sağlanırsa çalışır:

- `MENU_SECTIONS` içinde izin verilmeyen call/çağrı bulunmamalı.
- `MENU_SECTIONS` için beklenen yerel bağımlılık yalnızca `ANNOUNCEMENT_TOOL_ROLES` olmalı.
- Public değişken adları `menu_registry.py` içinde import bridge ile korunmalı.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_D3_MENU_SECTIONS_BRIDGE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_d3_menu_sections_bridge.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_d3_menu_sections_bridge.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

## Beklenen

- P0 sıfır kalır.
- `menu_registry.py` yaklaşık 1300 satır seviyesine iner.
- `menu_registry.py` büyük dosya listesinden çıkabilir.
- Menü anahtarları ve public değişken adları korunur.
