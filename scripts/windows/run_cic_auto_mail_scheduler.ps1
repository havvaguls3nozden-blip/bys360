param()

# BYS360 CIC Auto Mail Scheduler launcher
# install_bys360_cic_auto_mail_scheduler_task.ps1 tarafindan 5 dakikada bir
# tetiklenen Scheduled Task, bu scripti calistirir. Bu script sirasiyla
# scripts\scheduled\run_cic_auto_scheduler.py dosyasini cagirir (bkz.
# scripts/archive/quality/phase2y-wave1/check_bys360_cic_v3_0_system_auto_mail_scheduler_v1.py
# gate sozlesmesi: bu dosyada "cic_auto_mail_scheduler.log" ifadesi bulunmalidir).

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\bys360\project"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\scheduled\run_cic_auto_scheduler.py"
$LogDir = "C:\bys360\logs"
$LogPath = Join-Path $LogDir "cic_auto_mail_scheduler.log"
$LockPath = Join-Path $LogDir "cic_auto_mail_scheduler.lock"
$StaleLockMinutes = 15

if (!(Test-Path $Python)) {
    throw "Python bulunamadi: $Python"
}

if (!(Test-Path $Script)) {
    throw "CIC auto scheduler scripti bulunamadi: $Script"
}

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

# Gorev 5 dakikada bir tetiklenir. Bir onceki calisma hala suruyorsa
# (uzun suren mail gonderimi gibi) ust uste binmeyi engellemek icin basit
# bir dosya kilidi kullanilir. Kilit dosyasi StaleLockMinutes'tan eskiyse
# (ornegin onceki calisma cokup kilidi temizleyemediyse) otomatik temizlenir.
if (Test-Path $LockPath) {
    $lockAge = (Get-Date) - (Get-Item $LockPath).LastWriteTime
    if ($lockAge.TotalMinutes -lt $StaleLockMinutes) {
        Add-Content -Path $LogPath -Value "$(Get-Date -Format o) SKIP: onceki calisma suruyor (kilit yasi $([int]$lockAge.TotalSeconds) sn), bu tetikleme atlandi."
        exit 0
    }
    Add-Content -Path $LogPath -Value "$(Get-Date -Format o) WARN: bayat kilit dosyasi temizleniyor (yas $([int]$lockAge.TotalMinutes) dk)."
    Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType File -Path $LockPath -Force | Out-Null

try {
    Set-Location $ProjectRoot
    Add-Content -Path $LogPath -Value "$(Get-Date -Format o) START"
    & $Python $Script >> $LogPath 2>&1
    $ExitCode = $LASTEXITCODE
    Add-Content -Path $LogPath -Value "$(Get-Date -Format o) END ExitCode=$ExitCode"

    if ($ExitCode -ne 0) {
        throw "CIC Auto Mail Scheduler basarisiz. ExitCode=$ExitCode"
    }
}
finally {
    Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue
}
