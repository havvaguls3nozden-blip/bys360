# BYS360 Portal V3B8A — Syntax Empty Block Hotfix

Bu küçük düzeltme, V3B8 sonrasında `app/menu_registry_data_performance.py` içinde oluşan `IndentationError: expected an indented block after 'for' statement` hatasını kapatır.

## Uygulama

```powershell
cd C:ys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PORTAL_EXPERIENCE_V3B8A_SYNTAX_EMPTY_BLOCK_HOTFIX_OVERLAY.zip" -DestinationPath "C:ys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windowsepair_bys360_portal_experience_v3b8a_syntax_empty_block_hotfix.ps1 -ProjectRoot "C:ys360\project" -Mode all
```

Başarılı çıktı:

```text
BYS360_PORTAL_EXPERIENCE_V3B8A_SYNTAX_EMPTY_BLOCK_HOTFIX_OK
```
