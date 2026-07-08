param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) { throw "Python bulunamadı: $python" }

$logDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$morningScript = Join-Path $ProjectRoot "scripts\windows\run_executive_summary_0830.ps1"
$nightScript = Join-Path $ProjectRoot "scripts\windows\run_executive_summary_0001.ps1"

@"
Set-Location "$ProjectRoot"
& "$python" "scripts\executive\send_daily_executive_summary.py" --type morning >> "logs\executive_summary_0830.log" 2>&1
"@ | Set-Content -Path $morningScript -Encoding UTF8

@"
Set-Location "$ProjectRoot"
& "$python" "scripts\executive\send_daily_executive_summary.py" --type night >> "logs\executive_summary_0001.log" 2>&1
"@ | Set-Content -Path $nightScript -Encoding UTF8

$actionMorning = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$morningScript`"" -WorkingDirectory $ProjectRoot
$triggerMorning = New-ScheduledTaskTrigger -Daily -At 08:30
Register-ScheduledTask -TaskName "BYS360 Executive Summary 0830" -Action $actionMorning -Trigger $triggerMorning -Description "BYS360 Günaydın Yönetici Özeti otomatik mail görevi" -Force | Out-Null

$actionNight = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$nightScript`"" -WorkingDirectory $ProjectRoot
$triggerNight = New-ScheduledTaskTrigger -Daily -At 00:01
Register-ScheduledTask -TaskName "BYS360 Executive Summary 0001" -Action $actionNight -Trigger $triggerNight -Description "BYS360 Gece Sistem Kontrolü otomatik mail görevi" -Force | Out-Null

Write-Host "BYS360_EXECUTIVE_SUMMARY_TASKS_REGISTERED"
Get-ScheduledTask -TaskName "BYS360 Executive Summary 0830","BYS360 Executive Summary 0001" | Select-Object TaskName, State
