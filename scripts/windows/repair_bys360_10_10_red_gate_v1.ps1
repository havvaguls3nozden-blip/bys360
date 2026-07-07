param(
    [string]$ProjectRoot = "C:\bys360\project",
    [switch]$NoCi
)

$ErrorActionPreference = "Stop"
Write-Host "=== BYS360 10/10 Red Gate V1 ==="
Set-Location $ProjectRoot

if (Test-Path .git) {
    Write-Host "--- Git durum ---"
    git status --short
    $branch = "phase10-red-gate-v1"
    $current = (git branch --show-current).Trim()
    if ($current -ne $branch) {
        git checkout -B $branch
    }
}

$args = @(".\scripts\local\repair_bys360_10_10_red_gate_v1.py", "--project-root", $ProjectRoot)
if ($NoCi) { $args += "--no-ci" }
python @args

Write-Host "--- Önerilen doğrulama ---"
python -m pytest tests/security/test_xss_red_gate_v1.py -q
python -m ruff check app config.py tests/security/test_xss_red_gate_v1.py --select E9,F63,F7,F82,F821

Write-Host "OK: Red Gate V1 tamamlandı. Rapor: reports\security\BYS360_10_10_RED_GATE_V1_REPORT.md"
