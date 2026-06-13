# BYS360 OPS HARDENING V6A — Kritik Exception Temizliği

Bu overlay, canlı aday kodda kritik kimlik/yetki/güvenlik hatlarında yer alan sessiz veya zayıf `except Exception` bloklarına güvenli `logger.exception(...)` görünürlüğü ekler.

## Hedef kapsam

- `app/**/auth/**`
- `app/**/security/**`
- `app/**/session/**`
- `app/**/permission/**`
- `app/**/access/**`
- `app/**/rbac/**`
- `config.py`, `wsgi.py`, `run.py`

## Bilerek yapmadıkları

- Tüm 2104 exception bloğunu otomatik değiştirmez.
- İş akışını bozabilecek toplu `raise` eklemez.
- Performans, mail, bildirim ve API exception temizliklerini bu fazda genişletmez.

## Komut

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_OPS_HARDENING_V6A_CRITICAL_EXCEPTION_CLEANUP_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ops_hardening_v6a_critical_exception_cleanup.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Rapor

`reports\quality\BYS360_OPS_HARDENING_V6A_CRITICAL_EXCEPTION_CLEANUP_REPORT.md`
