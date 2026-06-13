param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$Mode = "all"
)
$ErrorActionPreference = "Stop"
Write-Host "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V5_DIRECT_STABLE uygulanıyor..."
Write-Host "ProjectRoot=$ProjectRoot"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
& $python (Join-Path $ProjectRoot "scripts\live_release\apply_bys360_cic_v3_0_live_final_release_resume_v5_direct_stable.py") $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V5_DIRECT_STABLE başarısız. ExitCode=$LASTEXITCODE" }
