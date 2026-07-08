param()

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\bys360\project"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\executive\send_daily_executive_summary.py"

if (!(Test-Path $Python)) {
    throw "Python bulunamadı: $Python"
}

if (!(Test-Path $Script)) {
    throw "Executive summary script bulunamadı: $Script"
}

Set-Location $ProjectRoot
& $Python $Script --type night

if ($LASTEXITCODE -ne 0) {
    throw "Executive Summary 0001 başarısız. ExitCode=$LASTEXITCODE"
}
