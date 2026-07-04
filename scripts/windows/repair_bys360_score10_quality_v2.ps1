param(
    [string]$ProjectRoot = "C:\bys360\project",
    [ValidateSet("audit", "clean-package")]
    [string]$Mode = "audit",
    [string]$OutputRoot = "C:\bys360\releases"
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

function Assert-PathExists($Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Eksik dosya: $Path"
    }
}

$Checks = [ordered]@{}
$Problems = New-Object System.Collections.Generic.List[string]

$Required = @(
    ".github\workflows\bys360-ci.yml",
    "scripts\quality\bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "scripts\quality\bys360_mobile_response_suite_gate_p3f.py",
    "scripts\quality\bys360_phase2_test_coverage_evidence_gate_v1.py",
    "tests\architecture\snapshots\phase2b_route_snapshot_baseline.json",
    "reports\architecture\BYS360_ANDROID_RESPONSIVE_BASELINE_GATE_P5A_REPORT.json",
    "reports\architecture\BYS360_ANDROID_RESPONSIVE_HARDENING_P5B_REPORT.json"
)

foreach ($Rel in $Required) {
    $Full = Join-Path $ProjectRoot $Rel
    if (Test-Path -LiteralPath $Full) {
        $Checks[$Rel] = "OK"
    } else {
        $Checks[$Rel] = "MISSING"
        $Problems.Add("Eksik dosya: $Rel") | Out-Null
    }
}

$CiPath = Join-Path $ProjectRoot ".github\workflows\bys360-ci.yml"
if (Test-Path -LiteralPath $CiPath) {
    $CiText = Get-Content -LiteralPath $CiPath -Raw -Encoding UTF8
    if ($CiText -notmatch "name:\s*Run tests") {
        $Problems.Add("CI workflow adı Run tests değil.") | Out-Null
    }
}

$SnapshotPath = Join-Path $ProjectRoot "tests\architecture\snapshots\phase2b_route_snapshot_baseline.json"
if (Test-Path -LiteralPath $SnapshotPath) {
    $Snapshot = Get-Content -LiteralPath $SnapshotPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([int]$Snapshot.route_count -ne 1049) {
        $Problems.Add("Route snapshot route_count 1049 değil: $($Snapshot.route_count)") | Out-Null
    }
}

$GateFiles = @(
    "scripts\quality\bys360_mobile_auth_dashboard_assistant_response_gate_p3b.py",
    "scripts\quality\bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v2.py",
    "scripts\quality\bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3.py",
    "scripts\quality\bys360_mobile_performance_response_gate_p3e.py",
    "scripts\quality\bys360_mobile_personnel_kpi_communication_response_gate_p3c.py",
    "scripts\quality\bys360_mobile_response_suite_gate_p3f.py",
    "scripts\quality\bys360_mobile_role_boundary_matrix_gate_p4b.py",
    "scripts\quality\bys360_mobile_role_boundary_matrix_gate_p4b_v3.py",
    "scripts\quality\bys360_mobile_security_suite_gate_p4c.py",
    "scripts\quality\bys360_mobile_security_suite_gate_p4c_v2.py",
    "scripts\quality\bys360_mobile_support_survey_notifications_response_gate_p3d.py"
)
foreach ($Rel in $GateFiles) {
    $Full = Join-Path $ProjectRoot $Rel
    if (Test-Path -LiteralPath $Full) {
        $Txt = Get-Content -LiteralPath $Full -Raw -Encoding UTF8
        if ($Txt -match "EXPECTED_CONTRACT(?:_ROUTE)?_COUNT\s*=\s*24" -or $Txt -match '"expected_contract_route_count"\s*:\s*24') {
            $Problems.Add("Eski 24 route beklentisi kaldı: $Rel") | Out-Null
        }
    }
}

$Audit = [ordered]@{
    marker = "BYS360_SCORE10_QUALITY_FIX_V2_AUDIT"
    project_root = $ProjectRoot
    status = $(if ($Problems.Count -eq 0) { "PASS" } else { "FAIL" })
    problem_count = $Problems.Count
    problems = @($Problems)
    checks = $Checks
}

$AuditJson = $Audit | ConvertTo-Json -Depth 8
Write-Host $AuditJson

if ($Problems.Count -gt 0) {
    exit 1
}

if ($Mode -eq "clean-package") {
    $BuildScript = Join-Path $ProjectRoot "scripts\packaging\build_bys360_clean_release_v1.py"
    if (-not (Test-Path -LiteralPath $BuildScript)) {
        throw "Temiz paket scripti bulunamadı: $BuildScript"
    }
    python $BuildScript --root $ProjectRoot --output-root $OutputRoot
}
