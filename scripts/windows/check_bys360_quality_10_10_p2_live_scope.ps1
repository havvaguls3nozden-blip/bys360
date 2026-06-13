param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360_QUALITY_10_10_P2_LIVE_SCOPE_CHECK_START"
Push-Location $ProjectRoot
try {
    python -m py_compile .\app\live_scope.py
    if ($LASTEXITCODE -ne 0) {
        throw "app/live_scope.py py_compile başarısız."
    }

    python -m compileall app scripts
    if ($LASTEXITCODE -ne 0) {
        throw "compileall başarısız."
    }

    powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p0.ps1 -ProjectRoot $ProjectRoot -FailOn never

    Write-Host "BYS360_QUALITY_10_10_P2_LIVE_SCOPE_CHECK_OK"
}
finally {
    Pop-Location
}
