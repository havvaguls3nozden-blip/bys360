# BYS360 Quality 10/10 P5 — Büyük Dosyalar İçin Tek Blok Patch

P4 aracı hedef dosyadaki tüm basit `except ...: pass` bloklarını tek seferde temizliyordu. Bu küçük dosyalarda güvenliydi; ancak `menu_registry.py`, mobil route dosyaları ve ayar/yetki dosyaları gibi büyük dosyalarda daha kontrollü ilerlemek gerekir.

Bu P5 paketi sadece seçilen dosyada, seçilen tek bloğu temizler.

## Blokları listele

```powershell
cd C:\bys360\project

powershell -ExecutionPolicy Bypass -File .\scripts\windows\list_bys360_quality_10_10_p5_single_blocks.ps1 -ProjectRoot "C:\bys360\project" -Target "app/api/mobile/performance_routes.py"
```

## İlk bloğu deneme

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p5_single_block.ps1 -ProjectRoot "C:\bys360\project" -Target "app/api/mobile/performance_routes.py" -BlockIndex 1 -DryRun
```

## İlk bloğu uygula

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p5_single_block.ps1 -ProjectRoot "C:\bys360\project" -Target "app/api/mobile/performance_routes.py" -BlockIndex 1
```

## Kontrol

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

Beklenen: P0 birer birer düşer. Büyük dosyalarda amaç hız değil, güvenli ilerlemedir.
