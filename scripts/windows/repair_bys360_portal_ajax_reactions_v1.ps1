param(
    [string]$ProjectRoot = "C:\bys360\project",
    [ValidateSet("all", "repair", "audit")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"
Write-Host "BYS360 Portal AJAX Reactions V1 başlıyor..." -ForegroundColor Cyan
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

if (!(Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot bulunamadı: $ProjectRoot"
}

$LocalPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $LocalPython) {
    $Python = $LocalPython
} else {
    $Python = "python"
}
Write-Host "Python=$Python"

$Repair = Join-Path $ProjectRoot "scripts\quality\repair_bys360_portal_ajax_reactions_v1.py"
$Check = Join-Path $ProjectRoot "scripts\quality\check_bys360_portal_ajax_reactions_v1.py"

if (!(Test-Path -LiteralPath $Repair)) { throw "Repair script bulunamadı: $Repair" }
if (!(Test-Path -LiteralPath $Check)) { throw "Check script bulunamadı: $Check" }

if ($Mode -eq "all" -or $Mode -eq "repair") {
    & $Python $Repair --project-root $ProjectRoot --mode repair
    if ($LASTEXITCODE -ne 0) { throw "Repair başarısız oldu." }
}

if ($Mode -eq "all" -or $Mode -eq "audit") {
    & $Python $Check --project-root $ProjectRoot
    if ($LASTEXITCODE -ne 0) { throw "Audit başarısız oldu." }
}

Write-Host "BYS360 Portal AJAX Reactions V1 tamamlandı." -ForegroundColor Green
