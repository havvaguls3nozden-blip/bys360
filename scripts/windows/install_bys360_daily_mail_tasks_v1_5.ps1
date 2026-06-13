param(
  [string]$ProjectRoot = "C:\bys360\project"
)
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LogDir = "C:\bys360\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
function Register-BysTask($Name, $Script, $Hour, $Minute) {
  $Arg = "`"$Script`" --force >> `"$LogDir\$($Name -replace ' ','_').log`" 2>&1"
  $Action = New-ScheduledTaskAction -Execute $Python -Argument $Arg -WorkingDirectory $ProjectRoot
  $Trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute))
  Register-ScheduledTask -TaskName $Name -Action $Action -Trigger $Trigger -Description "BYS360 otomatik mail görevi" -Force | Out-Null
  Write-Host "OK: $Name $Hour:$Minute"
}
Register-BysTask "BYS360 Daily Weather Personnel Mail" "scripts\communication\send_daily_weather_personnel_mail.py" 8 15
Register-BysTask "BYS360 Daily Pulse Check Mail" "scripts\communication\send_daily_pulse_check_mail.py" 13 0
Register-BysTask "BYS360 Daily Evening Tomorrow Mail" "scripts\communication\send_daily_evening_tomorrow_mail.py" 17 0
Write-Host "BYS360_EXECUTIVE_MAIL_CENTER_V1_5_TASKS_OK"
