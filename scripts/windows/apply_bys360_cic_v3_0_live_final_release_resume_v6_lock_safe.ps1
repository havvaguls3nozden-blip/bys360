param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$Mode = "all"
)
Write-Host "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V6_LOCK_SAFE uygulanıyor..."
Write-Host "ProjectRoot=$ProjectRoot"
$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { $py = "python" }
& $py (Join-Path $ProjectRoot "scripts\live_release\apply_bys360_cic_v3_0_live_final_release_resume_v6_lock_safe.py") -ProjectRoot $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V6_LOCK_SAFE başarısız. ExitCode=$LASTEXITCODE" }
