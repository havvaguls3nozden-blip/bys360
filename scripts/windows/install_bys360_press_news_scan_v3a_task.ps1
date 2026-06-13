param(
  [string]$ProjectRoot = "C:\bys360\project",
  [string]$TaskName = "BYS360 Portal Press News Scan V3A",
  [switch]$Create,
  [switch]$RunNow
)

$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\portal\run_bys360_press_news_scan_v3a.py"

if (!(Test-Path $Python)) { throw "Python bulunamadi: $Python" }
if (!(Test-Path $Script)) { throw "Tarama scripti bulunamadi: $Script" }

if ($Create) {
  $Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" --project-root `"$ProjectRoot`"" -WorkingDirectory $ProjectRoot
  $T1 = New-ScheduledTaskTrigger -Daily -At 8:30am
  $T2 = New-ScheduledTaskTrigger -Daily -At 12:30pm
  $T3 = New-ScheduledTaskTrigger -Daily -At 5:30pm
  $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger @($T1,$T2,$T3) -Settings $Settings -Force | Out-Null
  Write-Host "BYS360_PRESS_NEWS_SCAN_V3A_TASK_CREATED" -ForegroundColor Green
}

if ($RunNow) {
  & $Python $Script --project-root $ProjectRoot --manual
}
