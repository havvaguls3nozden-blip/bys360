param([string]$ProjectRoot = "C:\bys360\project")
$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) { $python = "python" }
$script = Join-Path $ProjectRoot "scripts\quality\check_bys360_live_full_overlay_v2_17_60.py"
if (!(Test-Path $script)) { throw "Check script bulunamadi: $script" }
& $python $script --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "BYS360 LIVE FULL OVERLAY V2.17.60 check basarisiz. ExitCode=$LASTEXITCODE" }
Write-Host "BYS360_LIVE_FULL_OVERLAY_V2_17_60_CHECK_OK" -ForegroundColor Green
