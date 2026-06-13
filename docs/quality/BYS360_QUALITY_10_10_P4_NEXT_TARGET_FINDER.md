# BYS360 Quality 10/10 P4 — Sıradaki Hedef Bulucu

Bu paket, tek tek yanlış dosya denemeyi azaltmak için hazırlanmıştır.

## Komutlar

Sıradaki basit `except/pass` hedeflerini listele:

```powershell
cd C:\bys360\project

powershell -ExecutionPolicy Bypass -File .\scripts\windows\find_bys360_quality_10_10_p4_next_targets.ps1 -ProjectRoot "C:\bys360\project" -Limit 20
```

En güvenli sıradaki tek hedefi deneme:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p4_next_target.ps1 -ProjectRoot "C:\bys360\project" -DryRun
```

En güvenli sıradaki tek hedefi uygula:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p4_next_target.ps1 -ProjectRoot "C:\bys360\project"
```

Son kontrol:

```powershell
python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never
```

## Not

Bu paket sadece AST olarak okunabilen dosyalarda basit `except ...: pass` yapılarını hedefler. Büyük ve riskli dosyalar düşük öncelikli tutulur.
