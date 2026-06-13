param(
    [string]$ProjectRoot = "C:\bys360\project",
    [int]$MorningHour = 8,
    [int]$MorningMinute = 15,
    [int]$PulseHour = 13,
    [int]$PulseMinute = 0,
    [int]$EveningHour = 17,
    [int]$EveningMinute = 0
)
$ErrorActionPreference = "Stop"
$py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $py)) { throw "Python sanal ortamı bulunamadı: $py" }
$logDir = "C:\bys360\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Register-BysTask($Name, $Script, $Hour, $Minute, $LogName) {
    $taskScript = Join-Path $ProjectRoot $Script
    $arg = "-NoProfile -ExecutionPolicy Bypass -Command `"cd '$ProjectRoot'; & '$py' '$taskScript' --force *> '$logDir\$LogName'`""
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
    $trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute))
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "OK: $Name -> $($Hour.ToString('00')):$($Minute.ToString('00')) | $logDir\$LogName"
}
Register-BysTask "BYS360 Daily Weather Personnel Mail" "scripts\communication\send_daily_weather_personnel_mail.py" $MorningHour $MorningMinute "daily_weather_personnel_mail.log"
Register-BysTask "BYS360 Daily Pulse Check Mail" "scripts\communication\send_daily_pulse_check_mail.py" $PulseHour $PulseMinute "daily_pulse_check_mail.log"
Register-BysTask "BYS360 Daily Evening Tomorrow Mail" "scripts\communication\send_daily_evening_tomorrow_mail.py" $EveningHour $EveningMinute "daily_evening_tomorrow_mail.log"
Write-Host "BYS360_DAILY_MAIL_TASKS_V1_6_INSTALL_OK"
