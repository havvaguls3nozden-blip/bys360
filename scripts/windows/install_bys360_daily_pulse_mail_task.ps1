param(
    [string]$ProjectRoot = "C:\bys360\project",
    [int]$Hour = 13,
    [int]$Minute = 0
)
$ErrorActionPreference = "Stop"
$TaskName = "BYS360 Daily Pulse Check Mail"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\communication\send_daily_pulse_check_mail.py"
# BYS360 DEFECT AA: the previous Action passed shell-redirection syntax
# (">>", "2>&1") as LITERAL argv to python.exe. Windows Task Scheduler
# never invokes a shell to interpret those tokens, so python.exe received
# them as unrecognized positional arguments -- argparse rejected the
# invocation and exited non-zero before any mail logic ever ran. Fixed by
# delegating to the canonical PowerShell launcher (same architecture as
# run_daily_weather_personnel_mail.ps1 / Install-BysTask's Pulse sub-task):
# a real powershell.exe process owns ">>"/"2>&1" as its own operators, not
# argv, and the launcher itself performs the same Python/script pre-flight
# checks this installer used to do directly.
$Launcher = Join-Path $ProjectRoot "scripts\communication\run_daily_pulse_check_mail.ps1"
$LogDir = "C:\bys360\logs"
$Log = Join-Path $LogDir "daily_pulse_check_mail.log"
if (!(Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
if (!(Test-Path $Python)) { throw "Python bulunamadi: $Python" }
if (!(Test-Path $Script)) { throw "Script bulunamadi: $Script" }
if (!(Test-Path $Launcher)) { throw "Launcher bulunamadi (installer bunu URETMEZ; repoda onceden var olmasi gerekir): $Launcher" }
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`"" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($Hour).AddMinutes($Minute))
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
# BYS360 DEFECT Y: explicit unattended-service principal -- without this,
# Register-ScheduledTask/Set-ScheduledTask default to the current
# interactive caller's identity/logon type, which this daily mail task
# cannot depend on.
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Set-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
    Write-Host "Mevcut gorev guncellendi: $TaskName"
} else {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "BYS360 gun ortasi pilot yoklama maili" | Out-Null
    Write-Host "Yeni gorev kuruldu: $TaskName"
}
Write-Host "BYS360_DAILY_PULSE_MAIL_TASK_OK"
Write-Host "Calisma saati: $($Hour.ToString('00')):$($Minute.ToString('00'))"
Write-Host "Log: $Log"
