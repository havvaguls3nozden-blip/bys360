param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"
Write-Host "BYS360 ACIL GERI DONUS - Yonetici Ozeti V1.0.8 rollback basliyor..."
Write-Host "ProjectRoot=$ProjectRoot"

if (!(Test-Path $ProjectRoot)) { throw "ProjectRoot bulunamadi: $ProjectRoot" }
Set-Location $ProjectRoot

$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { $py = "python" }

$script = Join-Path $ProjectRoot "scripts\dashboard\emergency_rollback_executive_summary_v1_0_8.py"
if (!(Test-Path $script)) { throw "Rollback script bulunamadi: $script" }

& $py $script --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "Yonetici Ozeti V1.0.8 acil geri donus basarisiz." }

Write-Host "BYS360_EXECUTIVE_SUMMARY_V1_0_9_EMERGENCY_ROLLBACK_OK"
Write-Host "Simdi canli Waitress gorevini durdurup baslatabilirsin."
