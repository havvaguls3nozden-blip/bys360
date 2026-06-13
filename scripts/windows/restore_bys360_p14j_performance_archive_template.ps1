param(
  [string]$ProjectRoot = "C:\bys360\project",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

Push-Location $ProjectRoot
try {
  $argsList = @(".\scripts\quality\restore_p14j_performance_archive_template_v1.py", "--project-root", $ProjectRoot)
  if ($DryRun) {
    $argsList += "--dry-run"
  }

  python @argsList
  if ($LASTEXITCODE -ne 0) {
    throw "P14J performans arşivi template restore başarısız."
  }
}
finally {
  Pop-Location
}
