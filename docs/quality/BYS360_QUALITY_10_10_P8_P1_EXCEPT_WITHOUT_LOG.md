# BYS360 Quality 10/10 P8 — P1 EXCEPT_WITHOUT_LOG Temizliği

P1 dağılımında 78 adet `EXCEPT_WITHOUT_LOG` görünmektedir. Bu paket, audit raporundaki ilk P1 `EXCEPT_WITHOUT_LOG` kaydını bulur ve ilgili `except` bloğunun gövdesinin başına `logger.exception` karşılığı ekler.

## Listele

```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\list_bys360_quality_10_10_p8_p1_except_without_log.ps1 -ProjectRoot "C:\bys360\project" -Limit 120
```

## İlk P1 kaydı için deneme

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p8_p1_except_without_log.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

## İlk P1 kaydı için uygulama

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p8_p1_except_without_log.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
python -m compileall app scripts
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

Beklenen ilk düşüş: `P1: 274 → 273`.
