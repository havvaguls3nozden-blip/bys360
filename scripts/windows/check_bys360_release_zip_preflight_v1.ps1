<#
BYS360 Release Zip Preflight V1

Kullanım:
  powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_release_zip_preflight_v1.ps1 -ZipPath "C:\bys360\project\dist_secure\BYS360_SECURE_RELEASE_V1_5_*.zip"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ZipPath,
    [string]$ProjectRoot = ".",
    [string]$OutputRoot = ""
)

$ErrorActionPreference = "Stop"

function Resolve-BysPython {
    param([string]$Root)
    $candidates = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        (Join-Path $Root "venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { return $pythonCmd.Source }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { return $pyCmd.Source }
    throw "Python bulunamadı."
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$Python = Resolve-BysPython -Root $ProjectRoot
$ScriptPath = Join-Path $ProjectRoot "scripts\security\bys360_release_zip_preflight_v1.py"
if (-not (Test-Path -LiteralPath $ScriptPath)) { throw "Preflight script bulunamadı: $ScriptPath" }

$zipMatches = Get-ChildItem -Path $ZipPath -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if (-not $zipMatches) { throw "Zip bulunamadı: $ZipPath" }
$ResolvedZip = $zipMatches[0].FullName

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $ProjectRoot "reports\security\release_zip_preflight_v1"
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

Write-Host "BYS360 release zip preflight başlıyor..." -ForegroundColor Cyan
Write-Host "Zip=$ResolvedZip"
& $Python $ScriptPath --zip $ResolvedZip --output-dir $OutputRoot
exit $LASTEXITCODE
