param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 ACIL TAM SOL SERIT RESTORE V2.14.12 kontrol basliyor..."
Write-Host "ProjectRoot=$ProjectRoot"

$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { $py = "python" }

$check = Join-Path $ProjectRoot "scripts\menu\check_full_sidebar_restore_v2_14_12.py"
if (!(Test-Path $check)) {
    throw "Check script bulunamadi: $check"
}

& $py $check --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Tam sol serit restore kontrolu basarisiz."
}

& $py -m py_compile (Join-Path $ProjectRoot "app\__init__.py")
if ($LASTEXITCODE -ne 0) {
    throw "app/__init__.py derlenemedi."
}

Write-Host "BYS360_EMERGENCY_FULL_SIDEBAR_RESTORE_V2_14_12_CHECK_OK"
