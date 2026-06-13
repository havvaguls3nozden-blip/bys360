param(
  [string]$ProjectRoot = "C:\bys360\project",
  [string]$TaskName = "BYS360 CIC Auto Mail Scheduler"
)
$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $ProjectRoot "scripts\windows\run_cic_auto_mail_scheduler.ps1"
if (!(Test-Path $ScriptPath)) { throw "Zamanlayici scripti bulunamadi: $ScriptPath" }
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
# Görev 5 dakikada bir yoklama yapar. Servis tarafında ayrıca hafta sonu kilidi vardır.
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(5) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description "BYS360 Kurumsal Bilgilendirme otomatik mail yoklama gorevi. BYS360 icindeki hafta ici kurali nedeniyle cumartesi-pazar otomatik mail gonderilmez." -Force | Out-Null
Write-Host "BYS360_CIC_AUTO_MAIL_SCHEDULER_TASK_INSTALLED_WEEKDAY_SAFE"
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State,TaskPath
Get-ScheduledTaskInfo -TaskName $TaskName
