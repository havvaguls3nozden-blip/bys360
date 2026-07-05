param(
    [string]$ProjectRoot = "C:\bys360\project",
    [ValidateSet("audit", "clean-copy", "audit-and-clean")]
    [string]$Mode = "audit",
    [string]$OutputRoot = "C:\bys360\reports\tech_debt_phase1",
    [switch]$NoZip
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Proje kökü bulunamadı: $ProjectRoot"
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectScript = Join-Path (Split-Path -Parent $ScriptDir) "local\bys360_tech_debt_phase1_audit_clean.py"

if (-not (Test-Path -LiteralPath $ProjectScript)) {
    throw "Python audit scripti bulunamadı: $ProjectScript"
}

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    throw "Python bulunamadı. Lütfen Python 3.12 ortamını veya .venv'i aktif edin."
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$argsList = @(
    $ProjectScript,
    "--project-root", $ProjectRoot,
    "--mode", $Mode,
    "--output-root", $OutputRoot
)

if ($NoZip) {
    $argsList += "--no-zip"
}

& $PythonCmd.Source @argsList
if ($LASTEXITCODE -ne 0) {
    throw "Teknik borç Faz 1 scripti hata verdi. ExitCode=$LASTEXITCODE"
}

Write-Host "OK: BYS360 Teknik Borç Faz 1 tamamlandı." -ForegroundColor Green
Write-Host "Rapor klasörü: $OutputRoot" -ForegroundColor Cyan
