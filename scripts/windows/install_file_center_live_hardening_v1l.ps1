param(
    [string]$ProjectRoot = "C:\bys360\project",
    [switch]$InstallScheduledTask,
    [switch]$SecretHygiene
)

$ErrorActionPreference = "Stop"
$OverlayRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path $ProjectRoot)) { throw "Proje yolu bulunamadı: $ProjectRoot" }

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path $ProjectRoot "backups\file_center_live_hardening_v1l_$Timestamp"
New-Item -ItemType Directory -Force $BackupRoot | Out-Null

$Files = @(
    "app\__init__.py",
    "app\security\api_rate_limit.py",
    "app\file_center\routes.py",
    "app\file_center\services.py",
    "app\file_center\maintenance_service.py",
    "app\templates\file_center\security.html",
    ".env.example",
    "scripts\local\file_center_ops_tick_v1l.py",
    "scripts\local\audit_file_center_secret_hygiene_v1l.py",
    "scripts\windows\install_file_center_scheduled_tasks_v1l.ps1",
    "scripts\windows\repair_file_center_secret_hygiene_v1l.ps1",
    "deployment\file_center_cron_v1l.example",
    "tests\security\test_file_center_v1l_hardening_static.py",
    "README_FILE_CENTER_LIVE_HARDENING_V1L.md"
)

foreach ($Rel in $Files) {
    $src = Join-Path $OverlayRoot $Rel
    if (-not (Test-Path $src)) { continue }
    $dst = Join-Path $ProjectRoot $Rel
    if (Test-Path $dst) {
        $backupPath = Join-Path $BackupRoot ($Rel -replace '[\\/]', '__')
        Copy-Item -LiteralPath $dst -Destination $backupPath -Force
    }
    New-Item -ItemType Directory -Force (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
}

# Aktif olmayan eski bak dosyalarını release kaynak görünümünden temizle.
Get-ChildItem -LiteralPath (Join-Path $ProjectRoot "app\file_center") -Filter "*.bak*" -File -ErrorAction SilentlyContinue |
    ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination (Join-Path $BackupRoot $_.Name) -Force }

Write-Host "OK: BYS360 Dosya Merkezi V1L canlı sertleştirme overlay uygulandı."
Write-Host "Yedek: $BackupRoot"

if ($SecretHygiene) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\windows\repair_file_center_secret_hygiene_v1l.ps1") -ProjectRoot $ProjectRoot
}
if ($InstallScheduledTask) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\windows\install_file_center_scheduled_tasks_v1l.ps1") -ProjectRoot $ProjectRoot
}
