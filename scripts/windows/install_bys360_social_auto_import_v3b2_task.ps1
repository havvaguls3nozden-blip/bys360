param(
  [Parameter(Mandatory=$true)][string]$ProjectRoot,
  [switch]$Create,
  [switch]$Delete
)
$ErrorActionPreference = "Stop"
$TaskName = "BYS360 Portal Social Auto Import V3B2"
if ($Delete) {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
  Write-Host "BYS360_PORTAL_SOCIAL_AUTO_IMPORT_V3B2_TASK_DELETED"
  exit 0
}
if ($Create) {
  $python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
  $script = Join-Path $ProjectRoot "scripts\portal\run_bys360_social_media_embed_scan_v3b.py"
  $action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" --project-root `"$ProjectRoot`" --auto-discover"
  $t1 = New-ScheduledTaskTrigger -Daily -At 09:00
  $t2 = New-ScheduledTaskTrigger -Daily -At 13:00
  $t3 = New-ScheduledTaskTrigger -Daily -At 17:00
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
  # BYS360 DEFECT Y: explicit unattended-service principal -- without this,
  # Register-ScheduledTask defaults to the current interactive caller's
  # identity/logon type, which this daily import task cannot depend on.
  $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($t1,$t2,$t3) -Settings $settings -Principal $principal -Description "BYS360 kurumsal sosyal medya paylaşımlarını portal akışına normal gönderi olarak aktarır." | Out-Null
  Write-Host "BYS360_PORTAL_SOCIAL_AUTO_IMPORT_V3B2_TASK_CREATED"
  exit 0
}
Write-Host "-Create veya -Delete parametresi kullanın."
