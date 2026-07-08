param(
  [string]$ProjectRoot = "C:\bys360\project",
  [string]$BackupRoot = "C:\bys360\backups",
  [ValidateSet("Plan","Backup")]
  [string]$Mode = "Plan",
  [string]$ServiceName = "BYS360 Live Waitress 80",
  [string]$DatabaseUrl = "",
  [switch]$IncludeDbBackup
)

$ErrorActionPreference = "Stop"

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $BackupRoot "BYS360_PRELIVE_BACKUP_$stamp"

function Write-Step($message) {
  Write-Host "[BYS360-PRELIVE] $message"
}

function Mask-SecretText($text) {
  if ([string]::IsNullOrWhiteSpace($text)) { return $text }
  $masked = $text
  $masked = $masked -replace '(?i)(password=)[^; ]+', '$1***MASKED***'
  $masked = $masked -replace '(?i)(://[^:]+:)[^@]+(@)', '$1***MASKED***$2'
  return $masked
}

Write-Step "Mode=$Mode"
Write-Step "ProjectRoot=$ProjectRoot"
Write-Step "BackupRoot=$BackupRoot"
Write-Step "ServiceName=$ServiceName"

if (!(Test-Path $ProjectRoot)) {
  throw "ProjectRoot bulunamadı: $ProjectRoot"
}

if ($Mode -eq "Plan") {
  Write-Step "Plan modu: Dosya kopyalama, DB dump veya servis sorgusu yapılmayacak."
  Write-Step "Backup modunda çalıştırmak için: -Mode Backup"
  Write-Step "DB yedeği için ayrıca: -IncludeDbBackup -DatabaseUrl '<canli DATABASE_URL>'"
  exit 0
}

New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$codeZip = Join-Path $backupDir "BYS360_CODE_BACKUP_$stamp.zip"
$serviceOut = Join-Path $backupDir "BYS360_SERVICE_QC_$stamp.txt"
$tasksOut = Join-Path $backupDir "BYS360_SCHEDULED_TASKS_$stamp.txt"
$summaryOut = Join-Path $backupDir "BYS360_PRELIVE_BACKUP_SUMMARY_$stamp.md"

Write-Step "Kod yedeği hazırlanıyor..."

$tmp = Join-Path $backupDir "_code_tmp"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

robocopy $ProjectRoot $tmp /E `
  /XD .git .venv venv __pycache__ .pytest_cache .ruff_cache .mypy_cache node_modules releases quarantine instance reports `
  /XF .env .env.* *.sqlite *.sqlite3 *.db *.bak *.pyc *.log | Out-Null

Compress-Archive -Path "$tmp\*" -DestinationPath $codeZip -Force
Remove-Item $tmp -Recurse -Force

Write-Step "Servis konfigürasyonu kaydediliyor..."
try {
  sc.exe qc "$ServiceName" > $serviceOut
} catch {
  "SERVICE_QC_FAILED: $($_.Exception.Message)" | Set-Content -Path $serviceOut -Encoding UTF8
}

Write-Step "Zamanlanmış görevler kaydediliyor..."
try {
  schtasks /Query /FO LIST /V > $tasksOut
} catch {
  "SCHEDULED_TASKS_QUERY_FAILED: $($_.Exception.Message)" | Set-Content -Path $tasksOut -Encoding UTF8
}

$dbOut = ""
$dbExit = "SKIPPED"

if ($IncludeDbBackup) {
  if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    throw "IncludeDbBackup verildi ama DatabaseUrl boş. DB yedeği için DatabaseUrl gerekli."
  }

  $dbOut = Join-Path $backupDir "BYS360_DB_BACKUP_$stamp.dump"
  Write-Step "PostgreSQL dump alınacak. DatabaseUrl rapora maskeli yazılacak."

  $pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
  if ($null -eq $pgDump) {
    throw "pg_dump bulunamadı. PostgreSQL bin klasörü PATH içinde olmalı."
  }

  & pg_dump --format=custom --file="$dbOut" "$DatabaseUrl"
  $dbExit = $LASTEXITCODE

  if ($dbExit -ne 0) {
    throw "pg_dump başarısız. ExitCode=$dbExit"
  }
}

$hash = Get-FileHash $codeZip -Algorithm SHA256

@"
# BYS360 Pre-Live Backup Özeti

Tarih: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Çıktılar

- Backup klasörü: `$backupDir`
- Kod yedeği: `$codeZip`
- Kod yedeği SHA256: `$($hash.Hash)`
- Servis kaydı: `$serviceOut`
- Zamanlanmış görev kaydı: `$tasksOut`
- DB yedeği: `$dbOut`
- DB exit: `$dbExit`

## Gizlilik

- .env dosyaları dahil edilmedi.
- SQLite/DB dosyaları dahil edilmedi.
- instance, reports, quarantine dahil edilmedi.
- DatabaseUrl rapora açık yazılmadı.

## DatabaseUrl Maskeli

`$(Mask-SecretText $DatabaseUrl)`

## Rollback Notu

Canlıda sorun olursa:
1. Servisi durdur.
2. Kod yedeğini geri aç.
3. Gerekirse DB dump geri yükle.
4. Servis/görev ayarlarını kayıtlara göre doğrula.
5. Smoke test çalıştır.
"@ | Set-Content -Path $summaryOut -Encoding UTF8

Write-Step "PRELIVE_BACKUP_DONE"
Write-Host "BACKUP_DIR=$backupDir"
Write-Host "CODE_ZIP=$codeZip"
Write-Host "CODE_ZIP_SHA256=$($hash.Hash)"
Write-Host "SUMMARY=$summaryOut"
