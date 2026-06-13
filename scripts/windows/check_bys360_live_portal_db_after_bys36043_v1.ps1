
param(
    [string]$ProjectRoot = "C:\bys360\project"
)
$ErrorActionPreference = "Stop"
$Version = "BYS360_LIVE_PORTAL_DB_FIX_AFTER_BYS36043_V1"
if (!(Test-Path -LiteralPath $ProjectRoot)) { throw "ProjectRoot bulunamadı: $ProjectRoot" }
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $Python)) { $Python = "python" }
$FixPy = Join-Path $ProjectRoot "scripts\windows\repair_bys360_live_portal_db_after_bys36043_v1.py"
& $Python $FixPy --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "$Version gate başarısız oldu." }
Write-Host "$Version`_GATE_OK" -ForegroundColor Green
