param(
    [Parameter(Mandatory=$true)][string]$ProjectRoot,
    [ValidateSet("dry-run", "apply")][string]$Mode = "dry-run",
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [string]$ArchiveRoot = "C:\bys360\archive"
)

$ErrorActionPreference = "Stop"
$Script = Join-Path $ProjectRoot "scripts\local\bys360_phase2b_scripts_archive_candidates.py"
if (-not (Test-Path $Script)) {
    throw "Phase2B archive script bulunamadı: $Script"
}

python $Script --project-root $ProjectRoot --mode $Mode --output-root $OutputRoot --archive-root $ArchiveRoot
if ($LASTEXITCODE -ne 0) {
    throw "Phase2B archive candidates çalışması başarısız oldu."
}

Write-Host "OK: BYS360 Teknik Borç Faz 2B script archive-candidates $Mode tamamlandı."
Write-Host "Rapor klasörü: $OutputRoot"
