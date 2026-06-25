param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

Write-Host "BYS360 güvenli release üretimi başlıyor..."
& $PythonExe "scripts\security\build_bys360_secure_release_v1_5.py" --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "Güvenli release üretimi başarısız." }

$LatestZip = Get-ChildItem -Path (Join-Path $ProjectRoot "dist_secure") -Filter "BYS360_SECURE_RELEASE_V1_5_*.zip" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $LatestZip) { throw "dist_secure altında release zip bulunamadı." }

Write-Host "Preflight çalışıyor: $($LatestZip.FullName)"
& $PythonExe "scripts\security\bys360_release_zip_preflight_v1.py" --zip $LatestZip.FullName --output-dir "reports\security\release_zip_preflight_v1"
if ($LASTEXITCODE -ne 0) { throw "Preflight FAIL verdi. Zip paylaşılmamalı." }

Write-Host "BYS360_SECURE_RELEASE_AND_PREFLIGHT_OK"
Write-Host "Zip: $($LatestZip.FullName)"
Write-Host "Rapor: reports\security\release_zip_preflight_v1"
