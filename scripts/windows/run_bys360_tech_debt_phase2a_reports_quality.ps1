param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [Parameter(Mandatory=$true)][ValidateSet("dry-run","apply")][string]$Mode,
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [string]$ArchiveRoot = "C:\bys360\archive"
)

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $ProjectRoot "scripts\local\bys360_phase2a_reports_quality_archive.py"
if (-not (Test-Path $ScriptPath)) {
    throw "Phase2A local script not found: $ScriptPath"
}

python $ScriptPath --project-root $ProjectRoot --output-root $OutputRoot --archive-root $ArchiveRoot --mode $Mode
if ($LASTEXITCODE -ne 0) {
    throw "Phase2A reports/quality command failed."
}

Write-Host "OK: BYS360 Teknik Borç Faz 2A reports/quality $Mode tamamlandı."
Write-Host "Rapor klasörü: $OutputRoot"
