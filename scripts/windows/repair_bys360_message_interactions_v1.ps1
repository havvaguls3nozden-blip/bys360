param(
    [string]$ProjectRoot = "C:\bys360\project",
    [ValidateSet("all", "repair", "check")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 Mesaj Etkileşimleri V1 başlıyor..." -ForegroundColor Cyan
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
Write-Host "Python=$Python"

$Repair = Join-Path $ProjectRoot "scripts\quality\repair_bys360_message_interactions_v1.py"
$Check = Join-Path $ProjectRoot "scripts\quality\check_bys360_message_interactions_v1.py"

if ($Mode -eq "all" -or $Mode -eq "repair") {
    if (-not (Test-Path -LiteralPath $Repair)) { throw "Repair script bulunamadı: $Repair" }
    & $Python $Repair --project-root $ProjectRoot --mode repair
    if ($LASTEXITCODE -ne 0) { throw "Repair script hata verdi." }
}

if ($Mode -eq "all" -or $Mode -eq "check") {
    if (-not (Test-Path -LiteralPath $Check)) { throw "Check script bulunamadı: $Check" }
    & $Python $Check --project-root $ProjectRoot
    if ($LASTEXITCODE -ne 0) { throw "Check script hata verdi." }
}

Write-Host "BYS360 Mesaj Etkileşimleri V1 tamamlandı." -ForegroundColor Green
