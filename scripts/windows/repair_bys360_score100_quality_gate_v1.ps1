<#
BYS360 SCORE 100 QUALITY GATE V1

Kullanım:
  cd C:\bys360\project
  powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit

Modlar:
  audit    : Sadece ölçer, dosya değiştirmez.
  fix-safe : Düşük riskli düzeltmeleri yapar; örn. key.properties.example parola alanlarını placeholder yapar ve .gitignore secret kurallarını ekler.
  gate     : CI/kalite kapısıdır. FAIL varsa non-zero exit verir.

Python çözümleme (BYS360 Phase 6 dependency-audit closure, 2026-07-27):
  Bu betik artık ilk bulunan python.exe'yi sessizce kabul etmez. Öncelik sırası:
    1. Açık -PythonPath parametresi
    2. BYS360_CANONICAL_PYTHON environment variable
    3. Repo-local .venv / venv (ProjectRoot altında)
    4. Bilinen local canonical project venv (-CanonicalSiblingPythonPath, varsayılan
       C:\bys360\project\.venv\Scripts\python.exe -- yalnız bu makinede varsa denenir,
       GitHub Actions gibi ortamlarda yoksa sessizce atlanır, zorunlu değildir)
    5. PATH üzerindeki python/python3/py -- yalnız sürüm (major.minor) ve modül
       import doğrulaması geçerse kabul edilir
    6. Hiçbiri uygun değilse: SCORE100_PYTHON_UNAVAILABLE, nonzero exit (fail-closed)
  Her adayın sürümü `<aday> -c "import sys; ..."` ile gerçekten çalıştırılarak ölçülür;
  bir dosyanın var olması tek başına yeterli kabul edilmez. Seçilen yol, sürüm ve
  kaynak SCORE100_PYTHON_PATH / SCORE100_PYTHON_VERSION / SCORE100_PYTHON_SOURCE
  olarak açıkça loglanır.

Dependency audit policy:
  -DependencyAuditPolicy Strict|Diagnostic parametresiyle açıkça belirlenebilir.
  Belirtilmezse: $env:CI -eq 'true' ise Strict, değilse Diagnostic varsayılır
  (GitHub Actions runner'ları CI=true'yu otomatik ayarlar). Seçilen politika
  DEPENDENCY_AUDIT_POLICY olarak loglanır ve Python gate script'ine
  --dependency-audit-policy ile iletilir; gerçek PASS/FAIL/BLOCKED sınıflandırması
  ve Strict modda BLOCKED/FAIL'in gate'i kırma kararı script tarafında verilir.
#>

[CmdletBinding()]
param(
    [string]$ProjectRoot = ".",
    [ValidateSet("audit", "fix-safe", "gate")]
    [string]$Mode = "audit",
    [string]$OutputRoot = "",
    [switch]$RunPipAudit,
    [switch]$RunRuff,
    [switch]$RunAppFactoryDuplicateCheck,
    [switch]$Strict,
    [string]$Allowlist = "",
    [string]$PythonPath = "",
    [string]$CanonicalSiblingPythonPath = "C:\bys360\project\.venv\Scripts\python.exe",
    [ValidateSet("", "Strict", "Diagnostic")]
    [string]$DependencyAuditPolicy = "",
    [string]$RequiredPythonMajorMinor = "3.12"
)

$ErrorActionPreference = "Stop"

function Get-BysPythonCandidateVersion {
    param([Parameter(Mandatory = $true)][string]$PythonExePath)
    try {
        $versionOutput = & $PythonExePath -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')" 2>$null
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($versionOutput)) {
            return $null
        }
        return $versionOutput.Trim()
    } catch {
        return $null
    }
}

function Test-BysPythonModulesImportable {
    param([Parameter(Mandatory = $true)][string]$PythonExePath)
    try {
        & $PythonExePath -c "import ast, argparse, json, subprocess, pathlib, dataclasses, datetime, re, shutil, sys" 2>$null 1>$null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Test-BysPythonCandidate {
    <#
    Tek bir aday yorumlayıcıyı kabul-edilebilirlik sözleşmesine göre doğrular:
    dosya var mı, sürüm gerçekten calistirilarak olculebiliyor mu, major.minor
    beklenen sözleşmeyle eşleşiyor mu, gerekli stdlib modülleri import edilebiliyor mu.
    Başarılıysa PSCustomObject{Path;Version;Source}, değilse $null döner ve
    nedeni $AttemptsLog listesine ekler.
    #>
    param(
        [string]$CandidatePath,
        [string]$Source,
        [string]$RequiredMajorMinor,
        [System.Collections.Generic.List[string]]$AttemptsLog
    )
    if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
        return $null
    }
    if (-not (Test-Path -LiteralPath $CandidatePath -PathType Leaf)) {
        $AttemptsLog.Add("$Source : NOT_FOUND ($CandidatePath)")
        return $null
    }
    $version = Get-BysPythonCandidateVersion -PythonExePath $CandidatePath
    if (-not $version) {
        $AttemptsLog.Add("$Source : VERSION_CHECK_FAILED ($CandidatePath)")
        return $null
    }
    $parts = $version -split '\.'
    $majorMinor = "$($parts[0]).$($parts[1])"
    if ($majorMinor -ne $RequiredMajorMinor) {
        $AttemptsLog.Add("$Source : VERSION_MISMATCH ($CandidatePath -> $version, beklenen $RequiredMajorMinor.x)")
        return $null
    }
    if (-not (Test-BysPythonModulesImportable -PythonExePath $CandidatePath)) {
        $AttemptsLog.Add("$Source : MODULE_IMPORT_FAILED ($CandidatePath)")
        return $null
    }
    return [PSCustomObject]@{
        Path    = $CandidatePath
        Version = $version
        Source  = $Source
    }
}

function Resolve-BysPython {
    <#
    Deterministik, fail-closed Python çözümleme. Öncelik sırası modül üstü
    dokümantasyonda açıklanmıştır. İlk bulunan python.exe'yi sessizce kabul
    etmez; her aday sürüm ve modül-import doğrulamasından geçmelidir.
    Açık -ExplicitPythonPath veya env var verilip geçersizse, daha düşük
    öncelikli adaylara sessizce düşmez -- bu, yanlış bir yolun kasıtlı olarak
    verildiği ama farkında olunmadan görmezden gelinmesini engeller.
    #>
    param(
        [string]$Root,
        [string]$ExplicitPythonPath = "",
        [string]$CanonicalSiblingPythonPath = "",
        [string]$RequiredMajorMinor = "3.12"
    )

    $attempts = [System.Collections.Generic.List[string]]::new()

    if (-not [string]::IsNullOrWhiteSpace($ExplicitPythonPath)) {
        $result = Test-BysPythonCandidate -CandidatePath $ExplicitPythonPath -Source "explicit" -RequiredMajorMinor $RequiredMajorMinor -AttemptsLog $attempts
        if ($result) { return $result }
        Write-Host "SCORE100_PYTHON_RESOLUTION_FAILED: -PythonPath acikca verildi ama gecersiz: $ExplicitPythonPath" -ForegroundColor Red
        foreach ($a in $attempts) { Write-Host "  - $a" }
        Write-Host "SCORE100_PYTHON_UNAVAILABLE"
        exit 6
    }

    $envPython = $env:BYS360_CANONICAL_PYTHON
    if (-not [string]::IsNullOrWhiteSpace($envPython)) {
        $result = Test-BysPythonCandidate -CandidatePath $envPython -Source "env" -RequiredMajorMinor $RequiredMajorMinor -AttemptsLog $attempts
        if ($result) { return $result }
        Write-Host "SCORE100_PYTHON_RESOLUTION_FAILED: BYS360_CANONICAL_PYTHON acikca verildi ama gecersiz: $envPython" -ForegroundColor Red
        foreach ($a in $attempts) { Write-Host "  - $a" }
        Write-Host "SCORE100_PYTHON_UNAVAILABLE"
        exit 6
    }

    $repoVenvCandidates = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        (Join-Path $Root "venv\Scripts\python.exe")
    )
    foreach ($candidate in $repoVenvCandidates) {
        $result = Test-BysPythonCandidate -CandidatePath $candidate -Source "repo-venv" -RequiredMajorMinor $RequiredMajorMinor -AttemptsLog $attempts
        if ($result) { return $result }
    }

    if (-not [string]::IsNullOrWhiteSpace($CanonicalSiblingPythonPath)) {
        $result = Test-BysPythonCandidate -CandidatePath $CanonicalSiblingPythonPath -Source "canonical-sibling" -RequiredMajorMinor $RequiredMajorMinor -AttemptsLog $attempts
        if ($result) { return $result }
    }

    foreach ($cmdName in @("python", "python3", "py")) {
        $cmd = Get-Command $cmdName -ErrorAction SilentlyContinue
        if ($cmd) {
            $result = Test-BysPythonCandidate -CandidatePath $cmd.Source -Source "validated-path" -RequiredMajorMinor $RequiredMajorMinor -AttemptsLog $attempts
            if ($result) { return $result }
        } else {
            $attempts.Add("validated-path($cmdName) : COMMAND_NOT_FOUND")
        }
    }

    Write-Host "SCORE100_PYTHON_RESOLUTION_FAILED: uygun (major.minor=$RequiredMajorMinor) Python bulunamadi." -ForegroundColor Red
    foreach ($a in $attempts) { Write-Host "  - $a" }
    Write-Host "SCORE100_PYTHON_UNAVAILABLE"
    exit 6
}

function Resolve-BysDependencyAuditPolicy {
    param([string]$Explicit = "")
    if (-not [string]::IsNullOrWhiteSpace($Explicit)) {
        return $Explicit
    }
    if ($env:CI -and $env:CI.ToLowerInvariant() -eq "true") {
        return "Strict"
    }
    return "Diagnostic"
}

# BYS360_SCORE100_DOT_SOURCE_GUARD: bu betik test amaçlı dot-source edildiğinde
# (". .\repair_bys360_score100_quality_gate_v1.ps1") yalnızca yukarıdaki
# fonksiyonlar tanımlanır, asagidaki ana çalıştırma gövdesi tetiklenmez. Bu,
# Resolve-BysPython / Resolve-BysDependencyAuditPolicy fonksiyonlarının gerçek
# ağ veya gerçek Score100 çalıştırması gerekmeden izole test edilebilmesini saglar.
if ($MyInvocation.InvocationName -ne '.') {

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$ScriptPath = Join-Path $ProjectRoot "scripts\quality\bys360_score100_quality_gate_v1.py"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Gate script bulunamadı: $ScriptPath. Overlay doğru klasöre açılmamış olabilir."
}

$resolvedPython = Resolve-BysPython -Root $ProjectRoot -ExplicitPythonPath $PythonPath -CanonicalSiblingPythonPath $CanonicalSiblingPythonPath -RequiredMajorMinor $RequiredPythonMajorMinor
$Python = $resolvedPython.Path
$resolvedPolicy = Resolve-BysDependencyAuditPolicy -Explicit $DependencyAuditPolicy

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $ProjectRoot "reports\quality\score100_quality_gate_v1"
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

Write-Host "BYS360 SCORE 100 QUALITY GATE V1 başlıyor..." -ForegroundColor Cyan
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"
Write-Host "SCORE100_PYTHON_PATH=$($resolvedPython.Path)"
Write-Host "SCORE100_PYTHON_VERSION=$($resolvedPython.Version)"
Write-Host "SCORE100_PYTHON_SOURCE=$($resolvedPython.Source)"
Write-Host "DEPENDENCY_AUDIT_POLICY=$resolvedPolicy"
Write-Host "OutputRoot=$OutputRoot"

$argsList = @(
    $ScriptPath,
    "--project-root", $ProjectRoot,
    "--mode", $Mode,
    "--output-dir", $OutputRoot,
    "--dependency-audit-policy", $resolvedPolicy.ToLowerInvariant()
)

if ($RunPipAudit) { $argsList += "--run-pip-audit" }
if ($RunRuff) { $argsList += "--run-ruff" }
if ($RunAppFactoryDuplicateCheck) { $argsList += "--run-app-factory-duplicate-check" }
if ($Strict) { $argsList += "--strict" }
if (-not [string]::IsNullOrWhiteSpace($Allowlist)) { $argsList += @("--allowlist", $Allowlist) }

& $Python @argsList
$exit = $LASTEXITCODE

$ReportMd = Join-Path $OutputRoot "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.md"
$ReportJson = Join-Path $OutputRoot "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json"

Write-Host ""
Write-Host "Raporlar:" -ForegroundColor Yellow
Write-Host "- $ReportMd"
Write-Host "- $ReportJson"

if ($exit -ne 0) {
    Write-Host "BYS360 SCORE 100 QUALITY GATE V1 başarısız. Raporu inceleyin." -ForegroundColor Red
    exit $exit
}

Write-Host "BYS360 SCORE 100 QUALITY GATE V1 tamamlandı." -ForegroundColor Green
exit 0

}
