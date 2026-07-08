param(
    [string]$ProjectRoot = "C:\bys360\project",
    [Parameter(Mandatory=$true)][string]$BackupRoot
)
$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) { $python = "python" }
$script = Join-Path $ProjectRoot "scripts\live\repair_bys360_live_full_overlay_v2_17_60.py"
if (!(Test-Path $script)) { throw "Repair script bulunamadi: $script" }
& $python $script --project-root $ProjectRoot --mode rollback --backup-root $BackupRoot
if ($LASTEXITCODE -ne 0) { throw "Rollback basarisiz. ExitCode=$LASTEXITCODE" }
Write-Host "BYS360_LIVE_FULL_OVERLAY_V2_17_60_ROLLBACK_OK" -ForegroundColor Green
