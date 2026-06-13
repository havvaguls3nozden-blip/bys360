# BYS360 Repo Bloat Cleanup P1

Bu overlay, BYS360 kaynak klasörünü devredilebilir hale getirmek için dosya şişmesini temizler veya temiz teslim kopyası üretir.

## Öncelik

İlk önerilen yöntem aktif projeyi bozmadan temiz kaynak kopyası üretmektir.

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_REPO_BLOAT_CLEANUP_P1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_bloat_cleanup_p1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_bloat_cleanup_p1.ps1 -ProjectRoot "C:\bys360\project" -Mode clean-copy -OutputRoot "C:\bys360\releases\BYS360_CLEAN_HANDOVER_SOURCE_P1"
```

## Modlar

| Mod | Etki |
|---|---|
| `audit` | Kod değiştirmez. Dosya şişmesi raporu üretir. |
| `clean-copy` | Aktif projeye dokunmadan temiz teslim kopyası üretir. |
| `write-gitignore` | `.gitignore` içine bloat/secret koruma bloğu ekler. |
| `quarantine-bloat` | Backup, archive, reports, cache, `.bak` gibi yerel kalıntıları arşive taşır. `.venv` yerinde bırakılır. |
| `all` | Güvenli mod: `.gitignore` yazar ve temiz kopya üretir; aktif dosya taşımaz/silmez. |

## Temiz kopyadan çıkarılanlar

- `.venv`, `venv`, cache klasörleri
- `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`
- `reports`, `backups`, `archive`, `overlay_payload`, `payload`
- `.bak`, `.bak_*`, `.old`, `.orig`, `.log`, `.tmp`
- gerçek `.env`, özel anahtar, sertifika, service account dosyaları
- üst dizindeki geçici `local_`, `debug_`, `probe_`, `inspect_` scriptleri

## Temiz kopyada kalanlar

- `app`, `scripts`, `migrations`, `tests`, `docs`, `sql`, `mobile_flutter`
- `requirements.txt`, `pyproject.toml`, `pytest.ini`, `README.md`
- güvenli `.env.example` dosyaları
- kaynak kod, şablon, migration ve test dosyaları

## Önemli güvenlik notu

Gerçek `.env` hiçbir temiz teslim paketine dahil edilmez. Daha önce gerçek `.env` içeren bir zip paylaşıldıysa parola/secret değerleri değiştirilmelidir.
