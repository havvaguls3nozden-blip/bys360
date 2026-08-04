param()

# BYS360 Daily Weather Personnel Mail launcher
# install_bys360_daily_weather_mail_task.ps1 / install_bys360_daily_mail_tasks_v1_4.ps1
# icindeki Install-BysTask fonksiyonu, kurulum sirasinda bu dosyanin icerigini
# kendi minimal (ErrorActionPreference=Continue) golgesiyle YENIDEN YAZAR
# (Set-Content -Path $Launcher). Bu nedenle bu repodaki surum, kaynak kontrollu
# referans/dogrulanabilir surumdur; canliya kurulum calistirildiginda
# installer'in urettigi surumle degistirilir (bkz. rapor: "kalan riskler").
#
# Runner: scripts\communication\send_daily_weather_personnel_mail.py
# Log: C:\bys360\logs\daily_weather_personnel_mail.log (Install-BysTask -LogPath ile birebir eslesir)

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\bys360\project"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\communication\send_daily_weather_personnel_mail.py"
$LogDir = "C:\bys360\logs"
$LogPath = Join-Path $LogDir "daily_weather_personnel_mail.log"

if (!(Test-Path $Python)) {
    throw "Python bulunamadi: $Python"
}

if (!(Test-Path $Script)) {
    throw "Weather mail scripti bulunamadi: $Script"
}

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

Set-Location $ProjectRoot
& $Python $Script >> $LogPath 2>&1

if ($LASTEXITCODE -ne 0) {
    throw "Daily Weather Personnel Mail basarisiz. ExitCode=$LASTEXITCODE"
}
