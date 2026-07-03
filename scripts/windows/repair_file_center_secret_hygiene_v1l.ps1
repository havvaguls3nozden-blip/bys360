param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$QuarantineRoot = "C:\bys360\_local_secrets\file_center_v1l",
    [switch]$MoveRootEnv
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $ProjectRoot)) { throw "Proje yolu bulunamadı: $ProjectRoot" }
New-Item -ItemType Directory -Force $QuarantineRoot | Out-Null

$Moved = @()
$Patterns = @(".env", ".env.local", ".env.production", ".flaskenv")
$Candidates = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object {
        $rel = $_.FullName.Substring($ProjectRoot.Length).TrimStart('\')
        ($Patterns -contains $_.Name -or ($_.Name -like ".env.*" -and $_.Name -notlike "*.example")) -and
        ($MoveRootEnv -or $rel -like "backups\*" -or $rel -like "archive\*" -or $rel -like "overlays\*")
    }

foreach ($File in $Candidates) {
    $rel = $File.FullName.Substring($ProjectRoot.Length).TrimStart('\')
    $safeName = ($rel -replace '[:\\/]', '__')
    $dest = Join-Path $QuarantineRoot $safeName
    Move-Item -LiteralPath $File.FullName -Destination $dest -Force
    $Moved += [pscustomobject]@{ From = $rel; To = $dest }
}

$Report = Join-Path $QuarantineRoot "secret_hygiene_report.json"
$Moved | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $Report -Encoding UTF8
Write-Host "OK: Secret hygiene tamamlandı. Taşınan dosya: $($Moved.Count)"
Write-Host "Rapor: $Report"
if (-not $MoveRootEnv) {
    Write-Host "Not: Kök .env taşınmadı. Onu da taşımak için -MoveRootEnv kullanın. Canlıda gerçek secret rotate etmeyi unutmayın."
}
