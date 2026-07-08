param([string]$ProjectRoot = "C:\bys360\project")
$ErrorActionPreference = "Stop"
Write-Host "BYS360 Yönetici Özeti zamanlanmış görevleri kuruluyor..."
Write-Host "ProjectRoot=$ProjectRoot"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if(!(Test-Path $Python)){ throw "Python bulunamadı: $Python" }
$Script = Join-Path $ProjectRoot "scripts\executive\send_daily_executive_summary.py"
if(!(Test-Path $Script)){ throw "Gönderim scripti bulunamadı: $Script" }
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$NightCmd = "cd `"$ProjectRoot`"; & `"$Python`" `"$Script`" --type night >> `"$LogDir\executive_summary_0001.log`" 2>&1"
$MorningCmd = "cd `"$ProjectRoot`"; & `"$Python`" `"$Script`" --type morning >> `"$LogDir\executive_summary_0830.log`" 2>&1"

$NightAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command $NightCmd" -WorkingDirectory $ProjectRoot
$MorningAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command $MorningCmd" -WorkingDirectory $ProjectRoot
$NightTrigger = New-ScheduledTaskTrigger -Daily -At 00:01
$MorningTrigger = New-ScheduledTaskTrigger -Daily -At 08:30
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "BYS360 Executive Summary 0001" -Action $NightAction -Trigger $NightTrigger -Settings $Settings -Description "BYS360 00:01 Gece Sistem Kontrolü ve Tarihi Alan Durum Raporu" -Force | Out-Null
Register-ScheduledTask -TaskName "BYS360 Executive Summary 0830" -Action $MorningAction -Trigger $MorningTrigger -Settings $Settings -Description "BYS360 08:30 Günaydın Yeni Gün Yönetici Özeti" -Force | Out-Null

Write-Host "BYS360_EXECUTIVE_SUMMARY_TASKS_V2_14_1_REGISTER_OK"
Get-ScheduledTask -TaskName "BYS360 Executive Summary 0001","BYS360 Executive Summary 0830" | Select-Object TaskName, State
