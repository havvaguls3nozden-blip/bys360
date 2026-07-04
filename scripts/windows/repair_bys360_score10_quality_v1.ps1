param(
  [string]$ProjectRoot = "C:\bys360\project",
  [ValidateSet("audit", "clean-package", "gate")]
  [string]$Mode = "audit",
  [string]$OutputRoot = "C:\bys360\releases"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

if ($Mode -eq "audit") {
  python .\scripts\quality\check_bys360_score10_quality_gate_v1.py --project-root $ProjectRoot --allow-local-env
  exit $LASTEXITCODE
}

if ($Mode -eq "clean-package") {
  python .\scripts\packaging\build_bys360_clean_release_v1.py --project-root $ProjectRoot --output-root $OutputRoot --name BYS360_SCORE10_CLEAN_SOURCE
  exit $LASTEXITCODE
}

if ($Mode -eq "gate") {
  python .\scripts\quality\check_bys360_score10_quality_gate_v1.py --project-root $ProjectRoot
  exit $LASTEXITCODE
}
