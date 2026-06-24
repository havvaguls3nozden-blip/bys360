<#
BYS360 Handover Docs Gate V1

Kullanım:
  powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_handover_docs_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode gate
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = ".",
    [ValidateSet("audit", "gate")]
    [string]$Mode = "audit",
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
$ScriptPath = Join-Path $ProjectRoot "scripts\quality\bys360_handover_docs_gate_v1.py"
if (-not (Test-Path -LiteralPath $ScriptPath)) { throw "Handover docs gate bulunamadı: $ScriptPath" }

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $ProjectRoot "reports\handover\handover_docs_gate_v1"
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

Write-Host "BYS360 handover docs gate başlıyor..." -ForegroundColor Cyan
& $Python $ScriptPath --project-root $ProjectRoot --output-dir $OutputRoot
$exit = $LASTEXITCODE
if ($Mode -eq "gate" -and $exit -ne 0) { exit $exit }
exit $exit
