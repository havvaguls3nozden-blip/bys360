param(
  [string]$ProjectRoot = "C:\bys360\project",
  [ValidateSet("audit", "rollback", "check", "all")]
  [string]$Mode = "all",
  [switch]$RunCompile,
  [switch]$DeleteStatic
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 Anasayfa Prestij SAFE V1A geri alma basliyor..." -ForegroundColor Cyan
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
  $Python = "python"
}
Write-Host "Python=$Python"

$Script = Join-Path $ProjectRoot "scripts\portal\rollback_bys360_home_prestige_safe_v1a.py"
if (!(Test-Path $Script)) {
  throw "Rollback script bulunamadi: $Script"
}

$argsList = @($Script, "--project-root", $ProjectRoot, "--mode", $Mode)
if ($RunCompile) { $argsList += "--compile" }
if ($DeleteStatic) { $argsList += "--delete-static" }

& $Python @argsList
if ($LASTEXITCODE -ne 0) {
  throw "BYS360 Anasayfa Prestij SAFE V1A rollback kontrolu basarisiz. Cikis kodu: $LASTEXITCODE"
}

if ($RunCompile) {
  Write-Host "Python compileall calisiyor..." -ForegroundColor Yellow
  & $Python -m compileall app config.py scripts
  if ($LASTEXITCODE -ne 0) {
    throw "compileall basarisiz. Cikis kodu: $LASTEXITCODE"
  }
}

Write-Host "BYS360_HOME_PRESTIGE_SAFE_V1A_ROLLBACK_OK" -ForegroundColor Green
