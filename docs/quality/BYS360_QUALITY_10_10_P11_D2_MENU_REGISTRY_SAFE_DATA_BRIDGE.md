# BYS360 Quality 10/10 P11-D2 — Menu Registry Safe Data Bridge

Bu paket `app/menu_registry.py` içindeki D1 analizinde güvenli bulunan büyük veri/sabit bloklarını ayrı data modüllerine taşır.

## Taşınan güvenli bloklar

- `ROLE_MENU_DEFAULTS`
- `_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_DISALLOWED_KEYS`
- `_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY`
- `_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS`

## Özellikle taşınmayan blok

- `MENU_SECTIONS`

Çünkü D1 analizinde `MENU_SECTIONS` içinde `sorted` çağrısı ve `ANNOUNCEMENT_TOOL_ROLES` bağımlılığı görülmüştür. Bu blok P11-D3 analizine bırakılmıştır.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_D2_MENU_REGISTRY_SAFE_DATA_BRIDGE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## Dry-run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_d2_menu_registry_safe_data_bridge.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## Uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p11_d2_menu_registry_safe_data_bridge.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

## Beklenen

- P0 sıfır kalır.
- `menu_registry.py` satır sayısı ciddi azalır ama `MENU_SECTIONS` durduğu için `LARGE_FILE_HARD` tamamen düşmeyebilir.
- Menü anahtarları ve public değişken adları korunur.
