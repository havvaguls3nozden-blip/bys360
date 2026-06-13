param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$BackupRoot = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360_QUALITY_10_10_P1_ROLLBACK_START"
Write-Host "ProjectRoot=$ProjectRoot"

if (-not (Test-Path $ProjectRoot)) {
    throw "ProjectRoot bulunamadı: $ProjectRoot"
}

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $backupParent = Join-Path $ProjectRoot ".quality_backup"
    if (-not (Test-Path $backupParent)) {
        throw ".quality_backup klasörü bulunamadı: $backupParent"
    }

    $candidate = Get-ChildItem -Path $backupParent -Directory |
        Where-Object { $_.Name -like "silent_except_logging_v1_*" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $candidate) {
        throw "silent_except_logging_v1_* yedeği bulunamadı. Elle BackupRoot verin."
    }

    $BackupRoot = $candidate.FullName
}

if (-not (Test-Path $BackupRoot)) {
    throw "BackupRoot bulunamadı: $BackupRoot"
}

Write-Host "BackupRoot=$BackupRoot"

$files = Get-ChildItem -Path $BackupRoot -Recurse -File
if (-not $files -or $files.Count -eq 0) {
    throw "Yedek klasörde geri yüklenecek dosya bulunamadı."
}

$restored = 0
foreach ($file in $files) {
    $relative = $file.FullName.Substring($BackupRoot.Length).TrimStart('\','/')
    $target = Join-Path $ProjectRoot $relative
    $targetDir = Split-Path -Parent $target

    if ($DryRun) {
        Write-Host ("DRYRUN restore: {0}" -f $relative)
    } else {
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    }
    $restored += 1
}

Write-Host "BYS360_QUALITY_10_10_P1_ROLLBACK_SUMMARY"
Write-Host "files_restored=$restored"
if ($DryRun) {
    Write-Host "BYS360_QUALITY_10_10_P1_ROLLBACK_DRYRUN_OK"
} else {
    Write-Host "BYS360_QUALITY_10_10_P1_ROLLBACK_OK"
}
