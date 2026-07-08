param(
  [string]$ProjectRoot = "C:\bys360\project",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Push-Location $ProjectRoot
try {
  $argsList = @(".\scripts\quality\restore_p14f4_source_aware_existing_assistant_v1.py", "--project-root", $ProjectRoot)
  if ($DryRun) {
    $argsList += "--dry-run"
  }
  python @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "P14F4 kaynak kontrollü mevcut asistan geri getirme başarısız."
  }
}
finally {
  Pop-Location
}
