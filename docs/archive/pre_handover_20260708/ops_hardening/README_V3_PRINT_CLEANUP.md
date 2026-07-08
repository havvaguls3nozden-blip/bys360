# BYS360 Operasyonel Sağlamlaştırma V3 — Print Temizliği

Bu paket, canlı aday Python kodundaki `print()` çağrılarını güvenli şekilde `logging` kullanımına dönüştürür.

## Kapsam

Taranan canlı aday alanlar:

- `app/`
- `config.py`
- `wsgi.py`
- `run.py`
- `asgi.py`
- `manage.py`

Şunlar kapsam dışıdır:

- `.venv`, `venv`
- `scripts` dışındaki eski repair/overlay araçları
- `reports`, `backups`, `archive`
- `__pycache__`

## Güvenlik Mantığı

Script yalnızca tek satırlık ve güvenli dönüştürülebilen `print(...)` çağrılarını otomatik çevirir.
`file=`, `flush=`, çok satırlı veya karmaşık kullanım varsa otomatik değiştirmez; rapora “manuel incelenecek” olarak yazar.

Değişiklikten önce her dosya yedeklenir:

```text
backups/ops_hardening_v3_print_cleanup/<timestamp>/...
```

## Komut

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_OPS_HARDENING_V3_PRINT_CLEANUP_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ops_hardening_v3_print_cleanup.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Rapor

```text
reports/quality/BYS360_OPS_HARDENING_V3_PRINT_CLEANUP_REPORT.md
reports/quality/BYS360_OPS_HARDENING_V3_PRINT_CLEANUP_REPORT.json
```

## Sonraki Faz

V3 tamamlandıktan sonra V4 geniş `except Exception` bloklarını önem sırasına göre sınıflandıracaktır.
