# BYS360 Quality 10/10 P13-A — Effective P1 Closure Map

Bu paket kod değiştirmez. P12-B karar raporundan sonra ham P1 ile etkili P1 ayrımını çıkarır.

## Ne yapar?

- Ham P1 değerini okur.
- Teknik UI false positive kararlarını düşerek etkili P1 değerini hesaplar.
- Kalan gerçek P1 aksiyonlarını ayırır:
  - LARGE_FILE_HARD
  - MANY_REPAIR_SCRIPTS
- Sıradaki güvenli fazı önerir.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_A_EFFECTIVE_P1_CLOSURE_MAP_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p13_a_effective_p1_closure_map.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p13_a_effective_p1_closure_map_v1.json
reports/quality/bys360_quality_10_10_p13_a_effective_p1_closure_map_v1.md
```

## Güvenlik

Bu aşamada dosya silinmez, kod taşınmaz. Büyük dosya ve script envanteri için karar haritası üretilir.
