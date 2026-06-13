# BYS360 Quality 9 Future Docstring Syntax HOTFIX V7

Bu paket V6 sonrası `compileall scripts` adımında kalan eski V5 onarım scripti hatasını kapatır.

## Kapsam

- `scripts/quality/repair_bys360_quality9_future_docstring_syntax_hotfix_v5.py` geçerli, emekliye alınmış wrapper haline getirilir.
- `from __future__ import annotations` sırası tekrar kontrol edilir.
- `logging.getLogger` kullanıp `import logging` eksik olan app dosyaları onarılır.
- `compileall`, Quality 9 gate, operasyon audit ve isteğe bağlı `ci_safe` pytest çalıştırılır.

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY9_FUTURE_DOCSTRING_SYNTAX_HOTFIX_V7_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_future_docstring_syntax_hotfix_v7.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests
```
