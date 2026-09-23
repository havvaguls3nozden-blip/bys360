param(
  [string]$ProjectRoot = "C:\bys360\project"
)
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\communication\run_corporate_information_task.py"
$Tasks = @(
  @{Name="BYS360 Corporate Info Staff Morning"; Key="staff_morning"; Time="08:00"},
  @{Name="BYS360 Corporate Info Staff Noon"; Key="staff_noon"; Time="12:30"},
  @{Name="BYS360 Corporate Info Staff Evening"; Key="staff_evening"; Time="17:30"},
  @{Name="BYS360 Corporate Info Manager Morning"; Key="manager_morning"; Time="07:45"},
  @{Name="BYS360 Corporate Info Manager Evening"; Key="manager_evening"; Time="17:45"}
)
# BYS360 DEFECT Y: explicit unattended-service principal (SYSTEM,
# ServiceAccount, Highest) -- without this, Register-ScheduledTask defaults
# to the current interactive caller's identity/logon type, which these
# early-morning/unattended daily mail tasks cannot depend on.
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
foreach($t in $Tasks){
  $Action = New-ScheduledTaskAction -Execute $Python -Argument "`"$Script`" --task $($t.Key)" -WorkingDirectory $ProjectRoot
  $Trigger = New-ScheduledTaskTrigger -Daily -At $t.Time
  $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
  Register-ScheduledTask -TaskName $t.Name -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
  Write-Host "Kuruldu/Güncellendi: $($t.Name) $($t.Time)"
}
Write-Host "BYS360_CORPORATE_INFORMATION_TASKS_V3_0_INSTALL_OK"
