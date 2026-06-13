param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"
$Version = "BYS360_LIVE_RESTORE_FROM_BYS36043_V1"
Write-Host "$Version gate kontrolü..." -ForegroundColor Cyan
Write-Host "ProjectRoot=$ProjectRoot"

if (!(Test-Path -LiteralPath $ProjectRoot)) { throw "ProjectRoot bulunamadı: $ProjectRoot" }
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $Python)) { $Python = "python" }

$gatePy = Join-Path $ProjectRoot "scripts\windows\check_bys36043_restore_v1.py"
& $Python $gatePy --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "$Version gate başarısız oldu." }

Write-Host "$Version`_GATE_OK" -ForegroundColor Green
