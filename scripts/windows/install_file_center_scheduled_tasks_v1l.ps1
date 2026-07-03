param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$PythonExe = "",
    [string]$TaskName = "BYS360 File Center Ops Tick V1L",
    [int]$Minutes = 15
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
}
if (-not (Test-Path $PythonExe)) { throw "Python bulunamadı: $PythonExe" }
$ScriptPath = Join-Path $ProjectRoot "scripts\local\file_center_ops_tick_v1l.py"
if (-not (Test-Path $ScriptPath)) { throw "Bakım scripti bulunamadı: $ScriptPath" }

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectRoot
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $Minutes) -RepetitionDuration (New-TimeSpan -Days 3650)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -StartWhenAvailable

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "BYS360 Dosya Merkezi link/istek/kota/tarama/disk bakım döngüsü" | Out-Null
Write-Host "OK: Zamanlanmış görev kuruldu: $TaskName / $Minutes dakikada bir"
