# BYS360 Local SQLite Schema Bootstrap V2

Bu hotfix, local geliştirme ortamında `DATABASE_URL` boş veya `sqlite:///:memory:` olduğunda oluşan `no such table: users` / `no such table: audit_logs` beyaz ekranını düzeltir.

## Kullanım

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_LOCAL_SQLITE_SCHEMA_BOOTSTRAP_V2_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_local_sqlite_schema_bootstrap_v2.ps1 -ProjectRoot "C:\bys360\project" -Mode all -LocalAdminEmail "bys360@ktb.gov.tr" -LocalAdminPassword "GECICI_GUCLU_SIFRE" -ResetLocalAdminPassword
```

Başarılı çıktı:

```text
BYS360_LOCAL_SQLITE_SCHEMA_BOOTSTRAP_V2_OK
```

Sonra uygulamayı yeniden başlatın.
