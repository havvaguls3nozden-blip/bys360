param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [string]$Mode = "audit"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = (Resolve-Path $ProjectRoot).Path
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$ScriptPath = Join-Path $ProjectRoot "scripts\local\bys360_tech_debt_phase2_audit.py"
if (-not (Test-Path $ScriptPath)) {
    throw "Faz 2 audit scripti bulunamadı: $ScriptPath"
}

python $ScriptPath --project-root $ProjectRoot --output-root $OutputRoot --mode $Mode
if ($LASTEXITCODE -ne 0) {
    throw "Faz 2 audit başarısız oldu."
}

Write-Host "OK: BYS360 Teknik Borç Faz 2 audit tamamlandı."
Write-Host "Rapor klasörü: $OutputRoot"
