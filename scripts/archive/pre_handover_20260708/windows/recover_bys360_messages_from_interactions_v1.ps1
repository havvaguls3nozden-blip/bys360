param(
    [string]$ProjectRoot = "C:\bys360\project",
    [switch]$RestartWaitress,
    [string]$TaskName = "BYS360 Live Waitress 80"
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 Messages Recovery V1 basliyor..."
Write-Host "ProjectRoot=$ProjectRoot"

if (!(Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot bulunamadi: $ProjectRoot"
}

Set-Location $ProjectRoot

$BackupRoot = Join-Path $ProjectRoot "backups"
if (!(Test-Path -LiteralPath $BackupRoot)) {
    throw "backups klasoru bulunamadi: $BackupRoot"
}

$backup = Get-ChildItem -LiteralPath $BackupRoot -Directory |
    Where-Object { $_.Name -like "message_interactions_v1_*" } |
    Sort-Object Name -Descending |
    Select-Object -First 1

if (-not $backup) {
    throw "message_interactions_v1_* yedegi bulunamadi. Once manuel kontrol gerekli."
}

Write-Host "Kullanilacak yedek: $($backup.FullName)"

$files = @(
    "app\models\communication_models.py",
    "app\models\__init__.py",
    "app\schema_guard_core_maintenances.py",
    "app\services\messages\constants.py",
    "app\services\messages\serialization.py",
    "app\services\messages\__init__.py",
    "app\communication\messages_routes.py",
    "app\templates\messages_inbox.html",
    "app\templates\messages_thread.html",
    "app\static\js\messages_messenger_mobile.js",
    "app\static\css\messages_messenger_mobile.css"
)

$rollbackStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$beforeRollback = Join-Path $BackupRoot "messages_before_recovery_v1_$rollbackStamp"
New-Item -ItemType Directory -Force -Path $beforeRollback | Out-Null

foreach ($rel in $files) {
    $src = Join-Path $backup.FullName $rel
    $dst = Join-Path $ProjectRoot $rel
    if (!(Test-Path -LiteralPath $src)) {
        Write-Warning "Yedekte yok, atlaniyor: $rel"
        continue
    }
    if (Test-Path -LiteralPath $dst) {
        $pre = Join-Path $beforeRollback $rel
        New-Item -ItemType Directory -Force -Path (Split-Path $pre -Parent) | Out-Null
        Copy-Item -LiteralPath $dst -Destination $pre -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    Write-Host "Geri alindi: $rel"
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $Python)) { $Python = "python" }
Write-Host "Python=$Python"

& $Python -m py_compile `
    app\models\communication_models.py `
    app\models\__init__.py `
    app\services\messages\constants.py `
    app\services\messages\serialization.py `
    app\services\messages\__init__.py `
    app\communication\messages_routes.py

if ($LASTEXITCODE -ne 0) { throw "py_compile hata verdi." }

Write-Host "OK: Mesaj ekranlari Message Interactions V1 oncesi calisan hale geri alindi."
Write-Host "Not: message_comments tablosu veritabaninda kalabilir; kullanilmadigi icin sorun degildir."

if ($RestartWaitress) {
    Write-Host "Waitress yeniden baslatiliyor: $TaskName"
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 8
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1/messages" -UseBasicParsing | Select-Object StatusCode, StatusDescription
    } catch {
        Write-Warning "Lokal /messages kontrolu hata verdi: $($_.Exception.Message)"
    }
}
