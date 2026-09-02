param(
  [string]$ProjectRoot = "C:\bys360\project"
)
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) { throw "Python bulunamadı: $Python" }
$Runner = Join-Path $ProjectRoot "scripts\communication\run_corporate_information_center_task_v3_0_phase2.py"
if (!(Test-Path $Runner)) { throw "Runner bulunamadı: $Runner" }
$LogDir = "C:\bys360\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$tasks = @(
  @{Name="BYS360 CIC Personel Sabah"; Key="PERSONEL_MORNING"; Hour=8; Minute=0},
  @{Name="BYS360 CIC Personel Oglen"; Key="PERSONEL_NOON"; Hour=12; Minute=30},
  @{Name="BYS360 CIC Personel Aksam"; Key="PERSONEL_EVENING"; Hour=17; Minute=30},
  @{Name="BYS360 CIC Yonetici Sabah"; Key="MANAGER_MORNING"; Hour=7; Minute=45},
  @{Name="BYS360 CIC Yonetici Aksam"; Key="MANAGER_EVENING"; Hour=17; Minute=45}
)
# BYS360 DEFECT Y: explicit unattended-service principal -- without this,
# Register-ScheduledTask/Set-ScheduledTask default to the current
# interactive caller's identity/logon type, which these daily mail tasks
# cannot depend on.
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
foreach ($t in $tasks) {
  $log = Join-Path $LogDir ($t.Key.ToLower() + ".log")
  $arg = "-NoProfile -ExecutionPolicy Bypass -Command `"cd '$ProjectRoot'; & '$Python' '$Runner' --task-key $($t.Key) --log-file '$log'`""
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg
  $trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($t.Hour).AddMinutes($t.Minute))
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
  $existing = Get-ScheduledTask -TaskName $t.Name -ErrorAction SilentlyContinue
  if ($existing) {
    Set-ScheduledTask -TaskName $t.Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
    Write-Host "Güncellendi: $($t.Name) => $($t.Hour):$($t.Minute.ToString('00'))"
  } else {
    Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "BYS360 Kurumsal Bilgilendirme Merkezi otomatik mail görevi" | Out-Null
    Write-Host "Kuruldu: $($t.Name) => $($t.Hour):$($t.Minute.ToString('00'))"
  }
}
Write-Host "BYS360_CORPORATE_INFORMATION_CENTER_TASKS_V3_0_PHASE2_OK"
