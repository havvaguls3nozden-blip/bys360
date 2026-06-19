param(
    [string]$ProjectRoot = "C:\bys360\project",
    [ValidateSet("apply", "check", "all")]
    [string]$Mode = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 Notification Email V1 başlıyor..."
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

$Repair = Join-Path $ProjectRoot "scripts\quality\repair_bys360_notification_email_v1.py"
$Check = Join-Path $ProjectRoot "scripts\quality\check_bys360_notification_email_v1.py"

if ($Mode -eq "apply" -or $Mode -eq "all") {
    if (-not (Test-Path -LiteralPath $Repair)) { throw "Repair script bulunamadı: $Repair" }
    & $Python $Repair --project-root $ProjectRoot --mode apply
}

if ($Mode -eq "check" -or $Mode -eq "all") {
    if (-not (Test-Path -LiteralPath $Check)) { throw "Check script bulunamadı: $Check" }
    & $Python $Check --project-root $ProjectRoot
}

Write-Host "BYS360 Notification Email V1 tamamlandı."
