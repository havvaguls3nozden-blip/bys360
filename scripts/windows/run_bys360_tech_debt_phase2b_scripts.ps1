param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectRoot,

    [Parameter(Mandatory=$false)]
    [ValidateSet("audit", "dry-run")]
    [string]$Mode = "audit",

    [Parameter(Mandatory=$true)]
    [string]$OutputRoot
)

$ErrorActionPreference = "Stop"

$ScriptPath = Join-Path $ProjectRoot "scripts\local\bys360_phase2b_scripts_inventory.py"

if (-not (Test-Path $ScriptPath)) {
    throw "Phase 2B Python audit script bulunamadı: $ScriptPath"
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

python $ScriptPath --project-root $ProjectRoot --mode $Mode --output-root $OutputRoot

if ($LASTEXITCODE -ne 0) {
    throw "Phase 2B scripts inventory başarısız oldu."
}

Write-Host "OK: BYS360 Teknik Borç Faz 2B scripts inventory tamamlandı."
Write-Host "Rapor klasörü: $OutputRoot"
