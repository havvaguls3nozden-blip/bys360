<#
BYS360 SCORE 100 QUALITY GATE V1

Kullanım:
  cd C:\bys360\project
  powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit

Modlar:
  audit    : Sadece ölçer, dosya değiştirmez.
  fix-safe : Düşük riskli düzeltmeleri yapar; örn. key.properties.example parola alanlarını placeholder yapar ve .gitignore secret kurallarını ekler.
  gate     : CI/kalite kapısıdır. FAIL varsa non-zero exit verir.
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = ".",
    [ValidateSet("audit", "fix-safe", "gate")]
    [string]$Mode = "audit",
    [string]$OutputRoot = "",
    [switch]$RunPipAudit,
    [switch]$RunRuff,
    [switch]$RunAppFactoryDuplicateCheck,
    [switch]$Strict,
    [string]$Allowlist = ""
)

$ErrorActionPreference = "Stop"

function Resolve-BysPython {
    param([string]$Root)

    $candidates = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        (Join-Path $Root "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { return $pythonCmd.Source }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { return $pyCmd.Source }

    throw "Python bulunamadı. .venv oluşturun veya Python'u PATH'e ekleyin."
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$ScriptPath = Join-Path $ProjectRoot "scripts\quality\bys360_score100_quality_gate_v1.py"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Gate script bulunamadı: $ScriptPath. Overlay doğru klasöre açılmamış olabilir."
}

$Python = Resolve-BysPython -Root $ProjectRoot

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $ProjectRoot "reports\quality\score100_quality_gate_v1"
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

Write-Host "BYS360 SCORE 100 QUALITY GATE V1 başlıyor..." -ForegroundColor Cyan
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"
Write-Host "Python=$Python"
Write-Host "OutputRoot=$OutputRoot"

$argsList = @(
    $ScriptPath,
    "--project-root", $ProjectRoot,
    "--mode", $Mode,
    "--output-dir", $OutputRoot
)

if ($RunPipAudit) { $argsList += "--run-pip-audit" }
if ($RunRuff) { $argsList += "--run-ruff" }
if ($RunAppFactoryDuplicateCheck) { $argsList += "--run-app-factory-duplicate-check" }
if ($Strict) { $argsList += "--strict" }
if (-not [string]::IsNullOrWhiteSpace($Allowlist)) { $argsList += @("--allowlist", $Allowlist) }

& $Python @argsList
$exit = $LASTEXITCODE

$ReportMd = Join-Path $OutputRoot "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.md"
$ReportJson = Join-Path $OutputRoot "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json"

Write-Host ""
Write-Host "Raporlar:" -ForegroundColor Yellow
Write-Host "- $ReportMd"
Write-Host "- $ReportJson"

if ($exit -ne 0) {
    Write-Host "BYS360 SCORE 100 QUALITY GATE V1 başarısız. Raporu inceleyin." -ForegroundColor Red
    exit $exit
}

Write-Host "BYS360 SCORE 100 QUALITY GATE V1 tamamlandı." -ForegroundColor Green
exit 0
