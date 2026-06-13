# BYS360 Quality 9 Future Docstring Syntax HOTFIX V8

Bu paket V7 sonrası görülen Quality 9 gate komut uyumsuzluğunu giderir.

## Düzeltilenler

- Windows repair script artık `bys360_quality9_ci_gate.py` dosyasını `--root` ile çağırır.
- Quality gate geriye dönük uyumluluk için `--project-root` ve `--max-broad-except` argümanlarını da kabul eder.
- Eski bozuk V5 hotfix scripti güvenli wrapper olarak korunur.
- Future import/docstring sırası ve eksik logging import kontrolleri tekrar yapılır.

## Çalıştırma

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY9_FUTURE_DOCSTRING_SYNTAX_HOTFIX_V8_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_future_docstring_syntax_hotfix_v8.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests
```
