param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360_QUALITY_10_10_P1_ROLLBACK_VERIFY_START"
Push-Location $ProjectRoot
try {
    python -m compileall app scripts
    if ($LASTEXITCODE -ne 0) {
        throw "compileall başarısız oldu."
    }

    powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p0.ps1 -ProjectRoot $ProjectRoot -FailOn never

    Write-Host "BYS360_QUALITY_10_10_P1_ROLLBACK_VERIFY_OK"
}
finally {
    Pop-Location
}
