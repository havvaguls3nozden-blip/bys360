param(
  [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"
Write-Host "BYS360 Live Full Overlay V2.13.0 geri alma işlemi başlıyor..."
Write-Host "ProjectRoot=$ProjectRoot"

if (!(Test-Path $ProjectRoot)) { throw "ProjectRoot bulunamadı: $ProjectRoot" }

$OverlayRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Helper = Join-Path $OverlayRoot "scripts\overlay\bys360_live_full_overlay_v2_13_0.py"
if (!(Test-Path $Helper)) { throw "Overlay helper bulunamadı: $Helper" }

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) { $Python = $VenvPython } else { $Python = "python" }

& $Python $Helper --project-root $ProjectRoot --mode rollback
if ($LASTEXITCODE -ne 0) { throw "Rollback başarısız oldu." }

Write-Host "BYS360_LIVE_FULL_OVERLAY_V2_13_0_ROLLBACK_OK"
