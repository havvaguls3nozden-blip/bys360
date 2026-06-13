param(
    [string]$ProjectRoot = "C:\bys360\project",
    [int]$Hour = 13,
    [int]$Minute = 0
)
$ErrorActionPreference = "Stop"
$TaskName = "BYS360 Daily Pulse Check Mail"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\communication\send_daily_pulse_check_mail.py"
$LogDir = "C:\bys360\logs"
$Log = Join-Path $LogDir "daily_pulse_check_mail.log"
if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
if (!(Test-Path $Python)) { throw "Python bulunamadi: $Python" }
if (!(Test-Path $Script)) { throw "Script bulunamadi: $Script" }
$action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" >> `"$Log`" 2>&1" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute))
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings | Out-Null
    Write-Host "Mevcut gorev guncellendi: $TaskName"
} else {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "BYS360 gun ortasi pilot yoklama maili" | Out-Null
    Write-Host "Yeni gorev kuruldu: $TaskName"
}
Write-Host "BYS360_DAILY_PULSE_MAIL_TASK_OK"
Write-Host "Calisma saati: $($Hour.ToString('00')):$($Minute.ToString('00'))"
Write-Host "Log: $Log"
