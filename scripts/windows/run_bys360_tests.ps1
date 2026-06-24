param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string[]]$PytestArgs = @()
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (!(Test-Path $Python)) {
    throw "BYS360 venv Python bulunamadi: $Python"
}

& $Python -m pytest @PytestArgs
exit $LASTEXITCODE
