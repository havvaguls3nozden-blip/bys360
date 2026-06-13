param([string]$ProjectRoot = "C:\bys360\project")
$ErrorActionPreference = "Stop"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\communication\run_executive_mail_center_v2.py"
$LogDir = "C:\bys360\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$tasks = @(
 @{Name="BYS360 Mail Center Manager Morning"; Hour=8; Minute=0; TaskKey="manager_morning"},
 @{Name="BYS360 Mail Center Manager Evening"; Hour=17; Minute=30; TaskKey="manager_evening"},
 @{Name="BYS360 Mail Center Staff Morning"; Hour=8; Minute=15; TaskKey="staff_morning"},
 @{Name="BYS360 Mail Center Staff Midday"; Hour=13; Minute=0; TaskKey="staff_midday"},
 @{Name="BYS360 Mail Center Staff Evening"; Hour=17; Minute=15; TaskKey="staff_evening"}
)
foreach ($t in $tasks) {
    $log = Join-Path $LogDir (($t.Name -replace '[^A-Za-z0-9]+','_') + ".log")
    $cmd = "& '$Python' '$Script' --task $($t.TaskKey) *> '$log'"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"$cmd`"" -WorkingDirectory $ProjectRoot
    $trigger = New-ScheduledTaskTrigger -Daily -At ([datetime]::Today.AddHours($t.Hour).AddMinutes($t.Minute))
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "OK: $($t.Name) $($t.Hour):$($t.Minute.ToString('00')) -> $log"
}
Write-Host "BYS360_EXECUTIVE_MAIL_CENTER_V2_0_TASKS_OK"
