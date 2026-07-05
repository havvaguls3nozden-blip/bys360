param(
  [string]$ProjectRoot = "C:\bys360\project",
  [ValidateSet("audit")]
  [string]$Mode = "audit",
  [string]$OutputRoot = "C:\bys360\reports\tech_debt_phase2c"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ProjectRoot)) {
  throw "ProjectRoot bulunamadı: $ProjectRoot"
}

$ScriptPath = Join-Path $ProjectRoot "scripts\local\bys360_phase2c_secret_signal_audit.py"

if (-not (Test-Path $ScriptPath)) {
  throw "Phase2C Python audit script bulunamadı: $ScriptPath"
}

New-Item -ItemType Directory -Force $OutputRoot | Out-Null

python $ScriptPath --project-root $ProjectRoot --output-root $OutputRoot

if ($LASTEXITCODE -ne 0) {
  throw "Phase2C secret signal audit başarısız oldu."
}

Write-Host "OK: BYS360 Teknik Borç Faz 2C secret signal audit tamamlandı."
Write-Host "Rapor klasörü: $OutputRoot"