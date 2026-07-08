param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"
Write-Host "BYS360 LIVE FULL OVERLAY V2.17.62 CHECKFIX kontrolu basliyor..." -ForegroundColor Cyan
$scriptPath = Join-Path $ProjectRoot "scripts\quality\check_bys360_live_full_overlay_v2_17_62.py"
if (!(Test-Path $scriptPath)) {
    throw "Python check script bulunamadi: $scriptPath"
}
& python $scriptPath --project-root $ProjectRoot
$exit = $LASTEXITCODE
if ($exit -ne 0) { throw "BYS360 LIVE FULL OVERLAY V2.17.62 CHECKFIX check basarisiz. ExitCode=$exit" }
Write-Host "BYS360_LIVE_FULL_OVERLAY_V2_17_62_CHECK_OK" -ForegroundColor Green
