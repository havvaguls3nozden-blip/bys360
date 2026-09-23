param()

# BYS360 Daily Pulse Check Mail launcher
# BYS360 DEFECT AA/AG: canonical launcher, created to close two related
# defects at once:
#   AA (install_bys360_daily_pulse_mail_task.ps1): the standalone Pulse
#      installer built a Scheduled Task Action that passed shell-
#      redirection syntax (">>", "2>&1") as LITERAL argv to python.exe
#      directly. Task Scheduler never invokes a shell to interpret those
#      tokens -- python.exe received them as unrecognized positional
#      arguments, so argparse rejected the invocation and exited non-zero
#      BEFORE any mail logic ever ran. This launcher lets a real
#      PowerShell process own the redirection instead (">>"/"2>&1" are
#      genuine PowerShell operators here, not argv), matching the exact,
#      already-canonical pattern established by the sibling
#      run_daily_weather_personnel_mail.ps1 launcher.
#   AG (install_bys360_daily_mail_tasks_v1_4.ps1): this file's own path
#      was already referenced by that installer's Install-BysTask helper
#      as the required launcher for the Pulse sub-task, but the file did
#      not exist on disk -- Install-BysTask's own pre-flight Test-Path
#      guard threw before any Scheduled Task mutation was attempted, so
#      that sub-task could never install at all.
# One canonical launcher closes both: install_bys360_daily_pulse_mail_
# task.ps1 and install_bys360_daily_mail_tasks_v1_4.ps1 both invoke this
# same file rather than maintaining two competing Pulse launch mechanisms.
#
# Runner: scripts\communication\send_daily_pulse_check_mail.py
# Log: C:\bys360\logs\daily_pulse_check_mail.log

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\bys360\project"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\communication\send_daily_pulse_check_mail.py"
$LogDir = "C:\bys360\logs"
$LogPath = Join-Path $LogDir "daily_pulse_check_mail.log"

if (!(Test-Path $Python)) {
    throw "Python bulunamadi: $Python"
}

if (!(Test-Path $Script)) {
    throw "Pulse mail scripti bulunamadi: $Script"
}

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

Set-Location $ProjectRoot
& $Python $Script >> $LogPath 2>&1

if ($LASTEXITCODE -ne 0) {
    throw "Daily Pulse Check Mail basarisiz. ExitCode=$LASTEXITCODE"
}
