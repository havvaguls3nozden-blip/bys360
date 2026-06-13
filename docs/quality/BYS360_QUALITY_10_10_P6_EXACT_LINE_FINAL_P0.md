# BYS360 Quality 10/10 P6 — Son P0 Satır Bazlı Temizlik

P5 basit AST kalıbını yakalamadığı halde audit raporunda `SILENT_EXCEPT_PASS` kalan son kayıtlar için hazırlanmıştır.

## Listele

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\list_bys360_quality_10_10_p6_remaining_p0.ps1 -ProjectRoot "C:\bys360\project"
```

## İlk kalan P0 için deneme

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p6_remaining_p0.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## İlk kalan P0 için uygulama

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p6_remaining_p0.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```
