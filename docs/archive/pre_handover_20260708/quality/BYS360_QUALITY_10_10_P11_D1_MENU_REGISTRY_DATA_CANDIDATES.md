# BYS360 Quality 10/10 P11-D1 — Menu Registry Data Candidate Analizi

Bu paket kod değiştirmez. `app/menu_registry.py` içindeki büyük top-level sabit/veri bloklarının güvenli şekilde bridge ile başka modüle taşınıp taşınamayacağını analiz eder.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_D1_MENU_REGISTRY_DATA_CANDIDATES_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_d1_menu_registry_data_candidates.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_d1_menu_registry_data_candidates_v1.json
reports/quality/bys360_quality_10_10_p11_d1_menu_registry_data_candidates_v1.md
```

## Güvenlik

Bu analiz menü anahtarlarını değiştirmez. Sadece taşıma adaylarını ve bağımlılıkları listeler. Gerçek refactor P11-D2 içinde dry-run destekli ve yedekli yapılmalıdır.
