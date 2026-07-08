param(
  [ValidateSet("Plan","ValidateEnv","BackupPlan","HttpSmokePlan")]
  [string]$Mode = "Plan",

  [string]$ProjectRoot = "C:\bys360\project",
  [string]$BackupRoot = "C:\bys360\backups",
  [string]$ServiceName = "BYS360 Live Waitress 80",

  # ValidateEnv modunda ger?ek canl? env dosya yolu verilir.
  # Bu dosya evidence paketine kopyalanmaz.
  [string]$EnvFile = "",

  # HttpSmokePlan modunda ?rn:
  # https://bys360.canakkaletarihialan.gov.tr
  [string]$BaseUrl = ""
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
  Write-Host "[BYS360-A8] $msg"
}

Write-Step "Mode=$Mode"
Write-Step "ProjectRoot=$ProjectRoot"
Write-Step "BackupRoot=$BackupRoot"
Write-Step "ServiceName=$ServiceName"

if (!(Test-Path $ProjectRoot)) {
  throw "ProjectRoot bulunamad?: $ProjectRoot"
}

Set-Location $ProjectRoot

if ($Mode -eq "Plan") {
  Write-Step "Plan modu: Canl?ya dokunulmaz."
  Write-Host ""
  Write-Host "A8 canl? ?ncesi ger?ek ortam s?ras?:"
  Write-Host "1) Ger?ek canl? env dosyas?n? strict gate ile do?rula:"
  Write-Host "   powershell -ExecutionPolicy Bypass -File .\scripts\windows\a8_live_cutover_guard.ps1 -Mode ValidateEnv -EnvFile '<CANLI_ENV_YOLU>'"
  Write-Host ""
  Write-Host "2) Canl? yedek/rollback plan?n? haz?rla:"
  Write-Host "   powershell -ExecutionPolicy Bypass -File .\scripts\windows\a8_live_cutover_guard.ps1 -Mode BackupPlan"
  Write-Host ""
  Write-Host "3) Yay?n sonras? ger?ek URL smoke plan?n? haz?rla:"
  Write-Host "   powershell -ExecutionPolicy Bypass -File .\scripts\windows\a8_live_cutover_guard.ps1 -Mode HttpSmokePlan -BaseUrl 'https://bys360.canakkaletarihialan.gov.tr'"
  Write-Host ""
  Write-Host "Not: Bu mod hi?bir dosya kopyalama, DB dump veya HTTP istek ?al??t?rmaz."
  exit 0
}

if ($Mode -eq "ValidateEnv") {
  if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    throw "ValidateEnv modu i?in -EnvFile zorunlu."
  }

  if (!(Test-Path $EnvFile)) {
    throw "EnvFile bulunamad?: $EnvFile"
  }

  Write-Step "Ger?ek canl? env strict gate ile do?rulanacak. Env i?eri?i rapora kopyalanmaz."
  & .\.venv\Scripts\python.exe .\scripts\security\validate_a6e_production_env_contract.py --env-file "$EnvFile" --strict
  $exitCode = $LASTEXITCODE

  Write-Host "A8_VALIDATE_ENV_EXIT_CODE=$exitCode"

  if ($exitCode -ne 0) {
    throw "Canl? env strict gate ba?ar?s?z."
  }

  exit 0
}

if ($Mode -eq "BackupPlan") {
  Write-Step "Pre-live backup script Plan modunda ?a?r?l?yor. Canl?ya dokunmaz."
  & powershell -ExecutionPolicy Bypass -File .\scripts\windows\pre_live_backup_plan.ps1 `
    -ProjectRoot "$ProjectRoot" `
    -BackupRoot "$BackupRoot" `
    -ServiceName "$ServiceName" `
    -Mode Plan

  Write-Host ""
  Write-Host "Ger?ek canl? yedek i?in, yay?n penceresinde ve yetkili ki?iyle:"
  Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\windows\pre_live_backup_plan.ps1 -ProjectRoot '$ProjectRoot' -BackupRoot '$BackupRoot' -ServiceName '$ServiceName' -Mode Backup"
  Write-Host ""
  Write-Host "DB yede?i dahil al?nacaksa:"
  Write-Host "powershell -ExecutionPolicy Bypass -File .\scripts\windows\pre_live_backup_plan.ps1 -ProjectRoot '$ProjectRoot' -BackupRoot '$BackupRoot' -ServiceName '$ServiceName' -Mode Backup -IncludeDbBackup -DatabaseUrl '<CANLI_DATABASE_URL>'"
  exit 0
}

if ($Mode -eq "HttpSmokePlan") {
  if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
    throw "HttpSmokePlan modu i?in -BaseUrl zorunlu."
  }

  Write-Step "HTTP smoke plan? g?steriliyor. Bu komut ger?ek HTTP iste?i ba?latmaz."
  Write-Host ""
  Write-Host "Yay?n sonras? ger?ek HTTP smoke i?in:"
  Write-Host ".\.venv\Scripts\python.exe .\scripts\live_readiness\a7d_local_smoke_contract.py --base-url '$BaseUrl'"
  Write-Host ""
  Write-Host "Beklenen:"
  Write-Host "A7D_OK: True"
  Write-Host "A7D_FAILED: 0"
  exit 0
}
