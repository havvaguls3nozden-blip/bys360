param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 ACIL RESTORE REMOVE EXEC MENU V2.14.18 kontrol basliyor..."
Write-Host "ProjectRoot=$ProjectRoot"

$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { $py = "python" }

$check = Join-Path $ProjectRoot "scripts\menu\check_emergency_restore_remove_exec_menu_v2_14_18.py"
if (!(Test-Path $check)) {
    throw "Check script bulunamadi: $check"
}

& $py $check --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Acil restore/remove exec menu kontrolu basarisiz."
}

& $py -m py_compile (Join-Path $ProjectRoot "app\__init__.py")
if ($LASTEXITCODE -ne 0) {
    throw "app/__init__.py derlenemedi."
}

Write-Host "BYS360_EMERGENCY_RESTORE_REMOVE_EXEC_MENU_V2_14_18_CHECK_OK"
