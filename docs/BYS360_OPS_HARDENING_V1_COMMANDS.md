# BYS360 Ops V1 Komutları

## Overlay uygula

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_OPS_HARDENING_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_ops_hardening_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Sadece audit

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_bys360_ops_audit_v1.ps1 -ProjectRoot "C:\bys360\project"
```

## Docker doğrulama

```powershell
Copy-Item .env.docker.example .env.docker.local -Force
notepad .env.docker.local

docker compose config
docker compose build
docker compose up -d
curl http://127.0.0.1:8000/health
```

## CI tarafı

GitHub reposuna push edildiğinde `.github/workflows/bys360-ci.yml` otomatik çalışır. İlk gate compile + ops audit + ruff kritik syntax/import kontrolüdür.
