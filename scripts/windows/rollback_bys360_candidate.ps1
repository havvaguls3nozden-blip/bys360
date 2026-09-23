<#
BYS360 Candidate Rollback Script V1
======================================

WHAT THIS DOES
  Restores a previously-live application tree (parked under
  C:\bys360\previous\<timestamp>_<SourceSha>\ by cutover_bys360_candidate.ps1
  -- cutover moves the outgoing tree there, it NEVER deletes it) back into
  C:\bys360\project, after quarantining (moving aside, never deleting) the
  current tree being rolled back FROM. This is APPLICATION-CODE rollback
  only. See "TWO ROLLBACK PATHS" below for what this does and does not
  cover regarding the database.

THIS SCRIPT NEVER RUNS AN AUTOMATIC ALEMBIC DOWNGRADE -- NOT EVER, NOT
UNDER ANY FLAG. There is no -Downgrade / -RunAlembicDowngrade switch and
none will be added. The current database revision is read and logged for
operator AWARENESS ONLY (Get-CurrentDbRevisionForAwareness); it is never
acted upon destructively. If a real schema downgrade is genuinely required,
that is a separate, manual, human-reviewed operation outside this script's
scope, exactly as documented in this project's existing
rollback_bys360_live_release_v1.ps1 ("VERITABANI rollback'i ... bu scriptin
KAPSAMI DISINDADIR; otomatiklestirilmez").

TWO ROLLBACK PATHS -- read this before running (also enforced in code by
Test-AppTreeDbCompatibilityGate, not just documented)

  (a) PRE-MIGRATION rollback (trivial, always safe): a cutover attempt
      failed before its `flask db upgrade` against the live database ever
      ran (or that migration itself failed and was correctly never
      applied -- see cutover_bys360_candidate.ps1's Invoke-LiveMigration,
      which never starts the service on a failed migration). The database
      is still at whatever revision the PREVIOUS tree already natively
      supports. Swapping the application tree back is unconditionally
      safe here -- the DB was never touched relative to that tree's own
      expectations. This script detects this case automatically (current
      DB revision == the previous tree's own recorded MIGRATION_HEAD, from
      its own CANDIDATE_READY.json if present) and does not require any
      extra confirmation.

  (b) POST-MIGRATION rollback (requires an explicit, evidence-based
      operator decision): a cutover succeeded all the way through the live
      migration (the DB is now at the FAILED candidate's migration head)
      but something later failed (health check, smoke check, security
      scan) and the operator now wants the application CODE rolled back
      while the DB stays at its new, already-migrated revision. This is
      ONLY safe if the previous tree's application code is actually
      compatible with the already-advanced schema -- e.g. because the
      previous and candidate source trees are byte-identical in app/,
      config.py, wsgi.py, run_server.py aside from additive/adoptive
      migrations (exactly the situation this wave's own coordinator asked
      to have verified: `git diff --stat cb2e57c..ec4e56b` was re-run
      directly in this worktree while writing this script and shows
      exactly 7 changed files, all under docs/handover/,
      migrations/versions/, tests/migrations/ -- app/, config.py, wsgi.py,
      run_server.py, requirements.txt are BYTE-IDENTICAL between those two
      specific commits, so a real ec4e56b-to-cb2e57c rollback after a
      completed migration WOULD be safe). This script does NOT hardcode
      that -- or any other -- specific pairing as always-safe, because:
        1. A production host has no .git directory to re-derive this from
           at rollback time (release packages are built from `git
           ls-files`, not a full clone -- see
           scripts\release\build_bys360_safe_release.py).
        2. A future previous/candidate pairing could easily NOT be
           app-code-identical, and asserting a blanket guarantee here
           would be exactly the kind of unverified claim this wave was
           explicitly asked not to make.
      Instead, this path REQUIRES the operator to pass
      -PostMigrationAppTreeCompatible explicitly, as a deliberate,
      evidence-based attestation (e.g. having run the equivalent git diff
      themselves on a dev machine for the ACTUAL pairing being rolled
      back). Without it, this script fails closed rather than guess.

WHAT THIS SCRIPT NEVER DOES
  - Never deletes anything. The tree being rolled back FROM is quarantined
    (moved, not deleted) under C:\bys360\previous\; the tree being rolled
    back TO is copied (not moved) from C:\bys360\previous\, so it remains
    intact for a retry or audit. DB backups are never touched at all.
  - Never runs an Alembic downgrade (see above).
  - Never guesses which previous snapshot to restore -- -PreviousDir is a
    mandatory, explicit parameter; this script performs no "most recent"
    auto-discovery.

FAILURE PHASES (recorded verbatim in the failure receipt's "Phase" field)
  PRECHECK_FAILED, PREVIOUS_DIR_INVALID, CURRENT_IDENTITY_FAILED,
  DEPLOYMENT_RECEIPT_INVALID, ACTIVE_DEPLOYMENT_IDENTITY_MISMATCH,
  PREVIOUS_DIR_DEPLOYMENT_MISMATCH, PREVIOUS_SHA_DEPLOYMENT_MISMATCH,
  COMPATIBILITY_GATE_FAILED, SERVICE_STOP_FAILED, QUARANTINE_FAILED,
  RESTORE_FAILED, IDENTITY_VERIFY_FAILED, SERVICE_START_FAILED,
  LOCAL_HEALTH_FAILED

ACTIVE-DEPLOYMENT RECEIPT BINDING (Phase 3a, coordinator addition,
2026-08-26 -- closes a real gap: Phase 3 used to only RECORD the active
tree's own SOURCE_SHA, never compare it against anything independently
sourced, so rollback would restore -PreviousDir onto whatever tree
happened to be sitting in ProjectRoot, right or wrong)
  -ActiveDeploymentReceiptPath is a MANDATORY, explicit pointer to the
  exact DEPLOYMENT_RECEIPT.txt written by cutover_bys360_candidate.ps1's
  Write-SuccessReceipt (its Phase 20/20, reached only on a fully
  successful cutover) for the SPECIFIC deployment being rolled back. This
  script performs NO "latest receipt" auto-discovery -- exactly the same
  explicit, no-guessing philosophy already used for -PreviousDir itself.
  The receipt is parsed deterministically and required to structurally
  validate (required fields present, no duplicates among them, SHA fields
  in this project's real 40-hex-char git-SHA format, DEPLOY_EXIT_CODE=0)
  before ANYTHING else is checked. Only once the receipt itself is proven
  valid does this phase bind it to BOTH explicit operator inputs: the
  active ProjectRoot's own SOURCE_SHA must equal the receipt's
  CANDIDATE_SOURCE_SHA, the supplied -PreviousDir must canonically resolve
  to the receipt's own PREVIOUS_DIR, and -PreviousDir's own SOURCE_SHA must
  equal the receipt's PREVIOUS_SOURCE_SHA. The receipt only PROVES the two
  explicit inputs (ProjectRoot, -PreviousDir) belong to the same successful
  cutover -- it never redirects rollback to a different tree than what the
  operator supplied. Any mismatch fails closed, before Phase 6 (service
  stop) -- no task stop, no tree move, no DB action.
#>

[CmdletBinding()]
param(
    # ---- Which previous snapshot to restore -- mandatory, no guessing ----
    [Parameter(Mandatory = $true)][string]$PreviousDir,

    # ---- Which cutover's DEPLOYMENT_RECEIPT.txt binds ProjectRoot and
    # -PreviousDir together -- mandatory, explicit, no "latest" guessing,
    # same philosophy as -PreviousDir itself. See header "ACTIVE-DEPLOYMENT
    # RECEIPT BINDING". ----
    [Parameter(Mandatory = $true)][string]$ActiveDeploymentReceiptPath,

    # ---- Server / host identity -----------------------------------------
    [string]$ExpectedHostName = "CATAB-BYS360",

    # ---- Filesystem roots -------------------------------------------------
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$PreviousRoot = "C:\bys360\previous",
    [string]$StorageRoot = "C:\bys360\storage",
    [string]$LocalStorageRoot = "C:\bys360\local_storage",
    [string]$DeployLogsRoot = "C:\bys360\deploy_logs",

    # ---- PostgreSQL (read-only awareness only -- see header) --------------
    [string]$PgBinPath = "C:\Program Files\PostgreSQL\15\bin",
    [string]$ProductionDbName,
    [string]$EnvFilePath,   # defaults to "$ProjectRoot\.env" (the tree being rolled back FROM)

    # ---- Scheduled Task -------------------------------------------------------
    [string]$TaskName = "BYS360 Live Waitress 80",
    [int]$AppPort = 80,
    [string]$PublicHostName = "bys360.canakkaletarihialan.gov.tr",

    # ---- The explicit, evidence-based operator attestation -- see header
    # "TWO ROLLBACK PATHS (b)". NEVER pass this without having actually
    # verified app-code/schema compatibility for the SPECIFIC pairing being
    # rolled back.
    [switch]$PostMigrationAppTreeCompatible,

    [switch]$SkipPublicHealthCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =====================================================================
# Global state / logging / receipt helpers -- same pattern as the other
# two scripts in this wave; duplicated deliberately to keep this script
# fully self-contained.
# =====================================================================

$Script:DeployId = Get-Date -Format "yyyyMMdd_HHmmss"
$Script:DeployLogDir = Join-Path $DeployLogsRoot "rollback_$($Script:DeployId)"
$Script:LogFile = $null
$Script:Receipt = [ordered]@{
    PREVIOUS_DIR              = $PreviousDir
    PREVIOUS_SOURCE_SHA       = ""
    CURRENT_SOURCE_SHA_BEFORE = ""
    DEPLOYMENT_BINDING        = ""
    QUARANTINE_DIR            = ""
    DB_REVISION_AWARENESS     = ""
    ROLLBACK_PATH             = ""   # PRE_MIGRATION | POST_MIGRATION_ATTESTED
    SERVICE_RESULT            = ""
    LOCAL_HEALTH              = ""
    PUBLIC_HEALTH             = ""
    ROLLBACK_EXIT_CODE        = ""
}

function Write-DeployLog {
    param([Parameter(Mandatory)][string]$Message, [string]$Level = "INFO")
    $line = "[{0}] [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Write-Host $line
    if ($Script:LogFile) {
        Add-Content -Path $Script:LogFile -Value $line -Encoding UTF8
    }
}

function Write-FailureReceipt {
    param([Parameter(Mandatory)][string]$Phase, [Parameter(Mandatory)][string]$Reason)
    if (-not (Test-Path $Script:DeployLogDir)) {
        New-Item -ItemType Directory -Force -Path $Script:DeployLogDir | Out-Null
    }
    $receiptPath = Join-Path $Script:DeployLogDir "FAILURE_RECEIPT.txt"
    $lines = @(
        "BYS360 CANDIDATE ROLLBACK -- FAILURE RECEIPT"
        "================================================================"
        "Phase          : $Phase"
        "Timestamp      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        "Reason         : $Reason"
        "Log path       : $($Script:LogFile)"
        "Deploy log dir : $($Script:DeployLogDir)"
        ""
        "Quarantine dir (if the current tree was already moved aside): $($Script:Receipt.QUARANTINE_DIR)"
        ""
        "No Alembic downgrade was attempted (this script never runs one)."
        "No DB backups were touched or deleted."
    )
    Set-Content -Path $receiptPath -Value $lines -Encoding UTF8
    Write-DeployLog -Level "FATAL" -Message "PHASE FAILED: $Phase -- $Reason (receipt: $receiptPath)"
    return $receiptPath
}

function Invoke-FailClosed {
    param([Parameter(Mandatory)][string]$Phase, [Parameter(Mandatory)][string]$Reason)
    $receiptPath = Write-FailureReceipt -Phase $Phase -Reason $Reason
    throw "[$Phase] $Reason (see $receiptPath)"
}

function Assert-NativeSuccess {
    param([Parameter(Mandatory)][string]$Phase, [Parameter(Mandatory)][string]$CommandDescription)
    if ($LASTEXITCODE -ne 0) {
        Invoke-FailClosed -Phase $Phase -Reason "$CommandDescription exit_code=$LASTEXITCODE"
    }
}

function Invoke-Native {
    param([Parameter(Mandatory)][scriptblock]$Command)
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Command
    } finally {
        $ErrorActionPreference = $previousEap
    }
}

function Assert-SafeMutationTarget {
    <# Ported from cutover_bys360_candidate.ps1's Assert-SafeMutationTarget
       (itself adapted from V4's Assert-SafeDeletionTarget). Hard guard
       before ANY Move-Item/Copy-Item mutation against a computed path: the
       resolved path must exactly equal the expected path, be at least 3
       segments deep, and match the required directory-shape regex. #>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedExact,
        [Parameter(Mandatory)][string]$Phase,
        [Parameter(Mandatory)][string]$RequiredSuffixRegex
    )
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $expected = [System.IO.Path]::GetFullPath($ExpectedExact)
    if ($resolved -ne $expected) {
        Invoke-FailClosed -Phase $Phase -Reason "Refusing mutation: resolved path '$resolved' does not exactly equal expected '$expected'."
    }
    $segments = $resolved.TrimEnd('\').Split('\') | Where-Object { $_ -ne "" }
    if ($segments.Count -lt 3) {
        Invoke-FailClosed -Phase $Phase -Reason "Refusing mutation: resolved path '$resolved' is too shallow ($($segments.Count) segments)."
    }
    if ($resolved -notmatch $RequiredSuffixRegex) {
        Invoke-FailClosed -Phase $Phase -Reason "Refusing mutation: resolved path '$resolved' does not match required shape '$RequiredSuffixRegex'."
    }
}

function ConvertFrom-DatabaseUrl {
    param([Parameter(Mandatory)][string]$Url)
    $pattern = '^postgresql(?:\+[a-zA-Z0-9_]+)?://(?<user>[^:@/]+):(?<pass>.+)@(?<host>[^:@/]+):(?<port>\d+)/(?<db>[^?\s]+)'
    $m = [regex]::Match($Url, $pattern)
    if (-not $m.Success) { return $null }
    return @{
        User = $m.Groups['user'].Value
        Password = $m.Groups['pass'].Value
        HostName = $m.Groups['host'].Value
        Port = [int]$m.Groups['port'].Value
        Database = $m.Groups['db'].Value
    }
}

function Get-ProductionDbConnection {
    param([Parameter(Mandatory)][string]$EnvPath)
    if (-not (Test-Path $EnvPath)) {
        Write-DeployLog -Level "WARN" "Env file not found at '$EnvPath' -- DB-revision awareness step will be skipped (this is informational-only, not a hard gate by itself)."
        return $null
    }
    $line = (Get-Content -Path $EnvPath -Encoding UTF8) | Where-Object { $_ -match '^\s*DATABASE_URL\s*=' } | Select-Object -First 1
    if (-not $line) {
        Write-DeployLog -Level "WARN" "DATABASE_URL not found in '$EnvPath' -- DB-revision awareness step will be skipped."
        return $null
    }
    $value = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    $parsed = ConvertFrom-DatabaseUrl -Url $value
    if (-not $parsed) {
        Write-DeployLog -Level "WARN" "DATABASE_URL in '$EnvPath' could not be parsed -- DB-revision awareness step will be skipped."
        return $null
    }
    Write-DeployLog "Resolved DB connection for awareness-only revision check: host=$($parsed.HostName) port=$($parsed.Port) db=$($parsed.Database) user=$($parsed.User) (password withheld)"
    return $parsed
}

function Test-LogForRealErrors {
    <# NOTE (found via direct testing while developing/testing the other
       two scripts in this wave): a plain
       [Parameter(Mandatory)][string]$LogText rejects an EMPTY string, not
       only $null. [AllowEmptyString()] fixes this. #>
    param([Parameter(Mandatory)][AllowEmptyString()][string]$LogText)
    $patterns = @(
        '\|\s*(ERROR|CRITICAL)\s*\|',
        '(?m)^(ERROR|CRITICAL)\s*:',
        '\b(ERROR|CRITICAL)\b\s*:',
        '(?m)^\[(ERROR|CRITICAL)\]',
        'Traceback \(most recent call last\)',
        '\bUnicodeEncodeError\b',
        '\bUnicodeDecodeError\b',
        'sqlalchemy\.exc\.OperationalError'
    )
    $hits = @()
    foreach ($p in $patterns) {
        if ($LogText -match $p) { $hits += $p }
    }
    return ,$hits
}

# =====================================================================
# Phase 1: host prerequisites
# =====================================================================

function Test-HostPrerequisites {
    Write-DeployLog "Phase 1/12: PRECHECK -- host prerequisites"

    $actualHostName = $env:COMPUTERNAME
    if ($actualHostName -ne $ExpectedHostName) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "hostname mismatch: expected '$ExpectedHostName', actual '$actualHostName'."
    }
    Write-DeployLog "Hostname OK: $actualHostName"

    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "Current PowerShell session is not running elevated (Administrator) -- required because this script stops/starts a Scheduled Task."
    }
    Write-DeployLog "Elevated session confirmed."

    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "Scheduled Task '$TaskName' does not exist."
    }
    Write-DeployLog "Scheduled Task state guard: '$TaskName' current state = $($task.State)"

    if (-not (Test-Path $ProjectRoot)) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "ProjectRoot does not exist: $ProjectRoot (nothing to roll back FROM)."
    }

    Write-DeployLog "HOST PREREQUISITES PASSED."
}

# =====================================================================
# Phase 2: exact previous-directory identity check
# =====================================================================

function Test-PreviousDirIdentity {
    Write-DeployLog "Phase 2/12: exact previous-directory identity check"

    Assert-SafeMutationTarget -Path $PreviousDir -ExpectedExact $PreviousDir -Phase "PREVIOUS_DIR_INVALID" -RequiredSuffixRegex ([regex]::Escape("\bys360\previous\"))

    if (-not (Test-Path $PreviousDir)) {
        Invoke-FailClosed -Phase "PREVIOUS_DIR_INVALID" -Reason "-PreviousDir does not exist: $PreviousDir"
    }
    $requiredMarkers = @("app", "config.py", "run_server.py", "wsgi.py")
    foreach ($m in $requiredMarkers) {
        if (-not (Test-Path (Join-Path $PreviousDir $m))) {
            Invoke-FailClosed -Phase "PREVIOUS_DIR_INVALID" -Reason "-PreviousDir is missing expected marker '$m': $PreviousDir"
        }
    }
    if (-not (Test-Path (Join-Path $PreviousDir ".venv\Scripts\python.exe"))) {
        Invoke-FailClosed -Phase "PREVIOUS_DIR_INVALID" -Reason "-PreviousDir has no .venv\Scripts\python.exe -- cannot serve as a runnable application tree: $PreviousDir"
    }
    if (-not (Test-Path (Join-Path $PreviousDir ".env"))) {
        Invoke-FailClosed -Phase "PREVIOUS_DIR_INVALID" -Reason "-PreviousDir has no .env: $PreviousDir"
    }

    $previousReceiptPath = Join-Path $PreviousDir "CANDIDATE_READY.json"
    $previousSha = "UNKNOWN"
    $previousMigrationHead = "UNKNOWN"
    if (Test-Path $previousReceiptPath) {
        try {
            $previousReceipt = Get-Content -Path $previousReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $previousSha = [string]$previousReceipt.SOURCE_SHA
            $previousMigrationHead = [string]$previousReceipt.MIGRATION_HEAD
        } catch {
            Write-DeployLog -Level "WARN" "-PreviousDir has a CANDIDATE_READY.json but it could not be parsed: $($_.Exception.Message)"
        }
    } else {
        Write-DeployLog -Level "WARN" "-PreviousDir has no CANDIDATE_READY.json (pre-dates this architecture, or was placed manually). PreviousSourceSha/MigrationHead recorded as UNKNOWN -- this makes the compatibility gate (Phase 5) stricter, not more lenient."
    }

    $Script:Receipt.PREVIOUS_SOURCE_SHA = $previousSha
    Write-DeployLog "Previous-directory identity confirmed: dir=$PreviousDir SourceSha=$previousSha MigrationHead=$previousMigrationHead"
    Write-DeployLog "PREVIOUS-DIRECTORY IDENTITY CHECK PASSED."
    return @{ SourceSha = $previousSha; MigrationHead = $previousMigrationHead }
}

# =====================================================================
# Phase 3: exact current-active-identity check
# =====================================================================

function Test-CurrentActiveIdentity {
    Write-DeployLog "Phase 3/12: exact current-active-identity check"

    $expectedProjectFull = [System.IO.Path]::GetFullPath($ProjectRoot)
    $previousDirFull = [System.IO.Path]::GetFullPath($PreviousDir)
    if ($expectedProjectFull -eq $previousDirFull) {
        Invoke-FailClosed -Phase "CURRENT_IDENTITY_FAILED" -Reason "ProjectRoot and -PreviousDir resolve to the SAME path ($expectedProjectFull) -- refusing to roll back a tree onto itself."
    }

    $currentReceiptPath = Join-Path $ProjectRoot "CANDIDATE_READY.json"
    $currentSha = "UNKNOWN"
    $currentMigrationHead = "UNKNOWN"
    if (Test-Path $currentReceiptPath) {
        try {
            $currentReceipt = Get-Content -Path $currentReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $currentSha = [string]$currentReceipt.SOURCE_SHA
            $currentMigrationHead = [string]$currentReceipt.MIGRATION_HEAD
        } catch {
            Write-DeployLog -Level "WARN" "Current tree has a CANDIDATE_READY.json but it could not be parsed: $($_.Exception.Message)"
        }
    } else {
        Write-DeployLog -Level "WARN" "Current tree has no CANDIDATE_READY.json -- CurrentSourceSha recorded as UNKNOWN."
    }

    $Script:Receipt.CURRENT_SOURCE_SHA_BEFORE = $currentSha
    Write-DeployLog "Current active identity confirmed: dir=$ProjectRoot SourceSha=$currentSha MigrationHead=$currentMigrationHead"
    Write-DeployLog "CURRENT-ACTIVE-IDENTITY CHECK PASSED."
    return @{ SourceSha = $currentSha; MigrationHead = $currentMigrationHead }
}

# =====================================================================
# Phase 3a: active-deployment receipt binding -- see header
# "ACTIVE-DEPLOYMENT RECEIPT BINDING". Additive: does not change Phase 2/3
# above, only adds a gate after both have already run.
# =====================================================================

function Assert-ActiveDeploymentBinding {
    param(
        [Parameter(Mandatory)][hashtable]$CurrentIdentity,
        [Parameter(Mandatory)][hashtable]$PreviousIdentity
    )
    Write-DeployLog "Phase 3a/12: active-deployment receipt binding"

    if (-not (Test-Path $ActiveDeploymentReceiptPath)) {
        Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "-ActiveDeploymentReceiptPath does not exist: $ActiveDeploymentReceiptPath"
    }
    $actualFileName = [System.IO.Path]::GetFileName($ActiveDeploymentReceiptPath)
    if ($actualFileName -ne "DEPLOYMENT_RECEIPT.txt") {
        Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "-ActiveDeploymentReceiptPath must point to a file literally named 'DEPLOYMENT_RECEIPT.txt', got '$actualFileName'."
    }

    # Deterministic KEY : VALUE parse (matches cutover's Write-SuccessReceipt
    # "{0,-24}: {1}" format). Values may themselves contain colons (e.g.
    # Windows paths like "C:\..."), so only the FIRST colon after the
    # identifier-shaped key is treated as the separator.
    $requiredKeys = @("CANDIDATE_SOURCE_SHA", "PREVIOUS_SOURCE_SHA", "PREVIOUS_DIR", "DEPLOY_EXIT_CODE")
    $parsed = @{}
    $seenCounts = @{}
    # Coordinator fix (2026-08-26, mechanically proven via isolated read-only
    # testing against both this synthetic fixture and the real successful
    # cutover's DEPLOYMENT_RECEIPT.txt): plain `-match` is case-INSENSITIVE
    # by default, and .NET's culture-aware case folding under this host's
    # Turkish (tr-TR) locale breaks [A-Za-z]-style character-class ranges
    # for any string containing the letter "I" (the well-known "Turkish I"
    # culture bug -- the same root-cause class already fixed elsewhere in
    # this codebase for Sort-Object's ordinal-vs-culture wheelhouse-identity
    # sort). Confirmed directly: "CANDIDATE_SOURCE_SHA" (contains "I") failed
    # to match `^([A-Za-z0-9_]+)\s*:\s*(.*)$` via -match while the identical
    # pattern via -cmatch (case-sensitive, bypassing the buggy culture-aware
    # path) matched correctly -- and since [A-Za-z0-9_] already spells out
    # both cases explicitly, case-insensitive matching was never needed
    # here. -cmatch/-cnotmatch used throughout this function accordingly.
    $rawLines = Get-Content -Path $ActiveDeploymentReceiptPath -Encoding UTF8
    foreach ($line in $rawLines) {
        if ($line -cmatch '^([A-Za-z0-9_]+)\s*:\s*(.*)$') {
            $key = $Matches[1]
            $value = $Matches[2].Trim()
            if ($seenCounts.ContainsKey($key)) {
                $seenCounts[$key] = $seenCounts[$key] + 1
            } else {
                $seenCounts[$key] = 1
            }
            $parsed[$key] = $value
        }
    }

    foreach ($key in $requiredKeys) {
        if (-not $seenCounts.ContainsKey($key)) {
            Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "Deployment receipt is missing required field '$key': $ActiveDeploymentReceiptPath"
        }
        if ($seenCounts[$key] -gt 1) {
            Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "Deployment receipt has duplicate entries for required field '$key' ($($seenCounts[$key]) occurrences) -- refusing to guess which is authoritative: $ActiveDeploymentReceiptPath"
        }
    }

    $shaPattern = '^[0-9a-f]{40}$'
    foreach ($shaKey in @("CANDIDATE_SOURCE_SHA", "PREVIOUS_SOURCE_SHA")) {
        if ($parsed[$shaKey] -cnotmatch $shaPattern) {
            Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "Deployment receipt field '$shaKey' = '$($parsed[$shaKey])' is not a valid 40-character lowercase git SHA."
        }
    }
    if (-not $parsed["PREVIOUS_DIR"]) {
        Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "Deployment receipt field 'PREVIOUS_DIR' is empty."
    }
    if ($parsed["DEPLOY_EXIT_CODE"] -ne "0") {
        Invoke-FailClosed -Phase "DEPLOYMENT_RECEIPT_INVALID" -Reason "Deployment receipt DEPLOY_EXIT_CODE = '$($parsed['DEPLOY_EXIT_CODE'])', expected '0' -- this receipt does not represent a fully successful cutover."
    }
    Write-DeployLog "Deployment receipt parsed and structurally valid: CANDIDATE_SOURCE_SHA=$($parsed['CANDIDATE_SOURCE_SHA']) PREVIOUS_SOURCE_SHA=$($parsed['PREVIOUS_SOURCE_SHA']) DEPLOY_EXIT_CODE=$($parsed['DEPLOY_EXIT_CODE'])"

    if ($CurrentIdentity.SourceSha -ne $parsed["CANDIDATE_SOURCE_SHA"]) {
        Invoke-FailClosed -Phase "ACTIVE_DEPLOYMENT_IDENTITY_MISMATCH" -Reason "Active ProjectRoot SOURCE_SHA ('$($CurrentIdentity.SourceSha)') does not match the deployment receipt's CANDIDATE_SOURCE_SHA ('$($parsed['CANDIDATE_SOURCE_SHA'])') -- this receipt is not for the currently active deployment. Refusing to proceed."
    }

    $suppliedPreviousDirFull = [System.IO.Path]::GetFullPath($PreviousDir)
    $receiptPreviousDirFull = [System.IO.Path]::GetFullPath($parsed["PREVIOUS_DIR"])
    if ($suppliedPreviousDirFull -ne $receiptPreviousDirFull) {
        Invoke-FailClosed -Phase "PREVIOUS_DIR_DEPLOYMENT_MISMATCH" -Reason "Supplied -PreviousDir ('$suppliedPreviousDirFull') does not match the deployment receipt's PREVIOUS_DIR ('$receiptPreviousDirFull') -- refusing to roll back the correct active deployment onto an unrelated previous tree."
    }

    if ($PreviousIdentity.SourceSha -ne $parsed["PREVIOUS_SOURCE_SHA"]) {
        Invoke-FailClosed -Phase "PREVIOUS_SHA_DEPLOYMENT_MISMATCH" -Reason "-PreviousDir's own SOURCE_SHA ('$($PreviousIdentity.SourceSha)') does not match the deployment receipt's PREVIOUS_SOURCE_SHA ('$($parsed['PREVIOUS_SOURCE_SHA'])')."
    }

    $Script:Receipt.DEPLOYMENT_BINDING = "PASS (receipt=$ActiveDeploymentReceiptPath)"
    Write-DeployLog "ACTIVE-DEPLOYMENT RECEIPT BINDING PASSED: ProjectRoot and -PreviousDir both verified against $ActiveDeploymentReceiptPath"
}

# =====================================================================
# Phase 4: DB-revision awareness -- read-only, never acted on
# destructively, no Alembic downgrade ever.
# =====================================================================

function Get-CurrentDbRevisionForAwareness {
    Write-DeployLog "Phase 4/12: DB-revision awareness (read-only; NEVER acted on destructively; no Alembic downgrade is ever run by this script)"

    if (-not $ProductionDbName) {
        Write-DeployLog -Level "WARN" "-ProductionDbName not supplied -- DB-revision awareness step skipped. The Phase 5 compatibility gate will treat this as UNKNOWN and require -PostMigrationAppTreeCompatible."
        $Script:Receipt.DB_REVISION_AWARENESS = "UNKNOWN (no -ProductionDbName supplied)"
        return $null
    }

    if (-not $EnvFilePath) { $EnvFilePath = Join-Path $ProjectRoot ".env" }
    $dbConn = Get-ProductionDbConnection -EnvPath $EnvFilePath
    if (-not $dbConn) {
        $Script:Receipt.DB_REVISION_AWARENESS = "UNKNOWN (could not resolve DATABASE_URL)"
        return $null
    }
    if ($dbConn.Database -ne $ProductionDbName) {
        Write-DeployLog -Level "WARN" "-ProductionDbName '$ProductionDbName' does not match DATABASE_URL's database ('$($dbConn.Database)') -- DB-revision awareness step skipped."
        $Script:Receipt.DB_REVISION_AWARENESS = "UNKNOWN (db name mismatch)"
        return $null
    }

    $psql = Join-Path $PgBinPath "psql.exe"
    if (-not (Test-Path $psql)) {
        Write-DeployLog -Level "WARN" "psql.exe not found at $PgBinPath -- DB-revision awareness step skipped."
        $Script:Receipt.DB_REVISION_AWARENESS = "UNKNOWN (psql.exe not found)"
        return $null
    }

    $env:PGPASSWORD = $dbConn.Password
    try {
        $revRaw = Invoke-Native { & $psql -h $dbConn.HostName -p $dbConn.Port -U $dbConn.User -d $dbConn.Database -t -A -c "SELECT version_num FROM alembic_version;" 2>&1 }
        $exitCode = $LASTEXITCODE
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
    if ($exitCode -ne 0) {
        Write-DeployLog -Level "WARN" "Could not read current DB revision (exit_code=$exitCode) -- treated as UNKNOWN for the compatibility gate."
        $Script:Receipt.DB_REVISION_AWARENESS = "UNKNOWN (query failed)"
        return $null
    }
    $rev = ($revRaw | Out-String).Trim()
    $Script:Receipt.DB_REVISION_AWARENESS = $rev
    Write-DeployLog "Current DB revision (awareness only, will NOT be acted upon): $rev"
    return $rev
}

# =====================================================================
# Phase 5: the compatibility gate -- see header "TWO ROLLBACK PATHS".
# =====================================================================

function Test-AppTreeDbCompatibilityGate {
    param(
        [Parameter(Mandatory)][AllowNull()][string]$CurrentDbRevision,
        [Parameter(Mandatory)][hashtable]$PreviousIdentity
    )
    Write-DeployLog "Phase 5/12: app-tree / DB compatibility gate"

    if (-not $CurrentDbRevision) {
        if ($PostMigrationAppTreeCompatible) {
            Write-DeployLog -Level "WARN" "DB revision could not be determined, but -PostMigrationAppTreeCompatible was supplied -- proceeding on the operator's explicit attestation. ROLLBACK_PATH=POST_MIGRATION_ATTESTED."
            $Script:Receipt.ROLLBACK_PATH = "POST_MIGRATION_ATTESTED (db revision unknown)"
            return
        }
        Invoke-FailClosed -Phase "COMPATIBILITY_GATE_FAILED" -Reason "DB revision could not be determined and -PostMigrationAppTreeCompatible was not supplied. Cannot prove this is a safe pre-migration rollback. See script header 'TWO ROLLBACK PATHS'. Re-run with -PostMigrationAppTreeCompatible ONLY after independently verifying app-code/schema compatibility for this specific pairing."
    }

    if ($PreviousIdentity.MigrationHead -ne "UNKNOWN" -and $CurrentDbRevision -eq $PreviousIdentity.MigrationHead) {
        Write-DeployLog "PRE-MIGRATION rollback confirmed: current DB revision ($CurrentDbRevision) matches the previous tree's own recorded migration head -- the database was never advanced past what the previous tree natively expects. Safe unconditionally."
        $Script:Receipt.ROLLBACK_PATH = "PRE_MIGRATION"
        return
    }

    if ($PostMigrationAppTreeCompatible) {
        Write-DeployLog -Level "WARN" "POST-MIGRATION rollback: current DB revision ($CurrentDbRevision) does NOT match the previous tree's migration head ($($PreviousIdentity.MigrationHead)) -- the database has been advanced. Proceeding ONLY because -PostMigrationAppTreeCompatible was explicitly supplied, i.e. the operator has independently attested that the previous application code is compatible with the current (advanced) schema for this specific pairing."
        $Script:Receipt.ROLLBACK_PATH = "POST_MIGRATION_ATTESTED"
        return
    }

    Invoke-FailClosed -Phase "COMPATIBILITY_GATE_FAILED" -Reason "POST-MIGRATION rollback scenario detected: current DB revision ($CurrentDbRevision) does not match the previous tree's migration head ($($PreviousIdentity.MigrationHead)). Rolling back the application code here is only safe if that code is compatible with the already-advanced schema, and this script cannot verify that on its own (no git available on a deployed tree). Refusing to guess. Re-run with -PostMigrationAppTreeCompatible ONLY after independently verifying compatibility for this specific pairing (e.g. a git diff --stat between the two source SHAs on a dev machine, confirming app/config.py/wsgi.py/run_server.py are unchanged aside from additive/adoptive migrations). This script NEVER runs an automatic Alembic downgrade as an alternative."
}

# =====================================================================
# Phase 6: stop live Scheduled Task
# =====================================================================

function Stop-LiveService {
    Write-DeployLog "Phase 6/12: stop live Scheduled Task"
    $task = Get-ScheduledTask -TaskName $TaskName
    if ($task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 3
    }
    $afterState = (Get-ScheduledTask -TaskName $TaskName).State
    if ($afterState -eq "Running") {
        Invoke-FailClosed -Phase "SERVICE_STOP_FAILED" -Reason "Task '$TaskName' still reports Running after Stop-ScheduledTask."
    }
    Write-DeployLog "Task '$TaskName' state after stop: $afterState"
    $listening = Get-NetTCPConnection -LocalPort $AppPort -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-DeployLog -Level "WARN" "Something is still listening on port $AppPort after stopping the task (pid(s): $($listening.OwningProcess -join ','))."
    } else {
        Write-DeployLog "Confirmed: nothing listening on port $AppPort."
    }
    Write-DeployLog "SERVICE STOP PASSED."
}

# =====================================================================
# Phase 7-9: quarantine current tree, restore previous tree (COPY, not
# move, so -PreviousDir remains intact for a retry/audit), reconcile
# .env/instance\ to the most recent versions (from the tree being rolled
# back FROM), verify restored identity.
# =====================================================================

function Move-CurrentTreeToQuarantine {
    param([Parameter(Mandatory)][string]$CurrentSourceSha)
    Write-DeployLog "Phase 7/12: quarantine current tree (move, never delete)"

    Assert-SafeMutationTarget -Path $ProjectRoot -ExpectedExact $ProjectRoot -Phase "QUARANTINE_FAILED" -RequiredSuffixRegex ([regex]::Escape("\bys360\project"))

    $shaForQuarantine = if ($CurrentSourceSha -and $CurrentSourceSha -ne "UNKNOWN") { $CurrentSourceSha } else { "unknown" }
    $quarantineDir = Join-Path $PreviousRoot "$($Script:DeployId)_$($shaForQuarantine)_rolled_back"
    Assert-SafeMutationTarget -Path $quarantineDir -ExpectedExact $quarantineDir -Phase "QUARANTINE_FAILED" -RequiredSuffixRegex ([regex]::Escape("\bys360\previous\"))

    if (Test-Path $quarantineDir) {
        Invoke-FailClosed -Phase "QUARANTINE_FAILED" -Reason "Computed quarantine destination already exists unexpectedly: $quarantineDir"
    }
    if (-not (Test-Path $PreviousRoot)) {
        New-Item -ItemType Directory -Force -Path $PreviousRoot | Out-Null
    }

    # Preserve the CURRENT (about-to-be-quarantined) tree's own .env/instance\
    # BEFORE moving it, so Restore-PersistentStateFromQuarantine can bring
    # the most recent configuration/instance data forward onto the restored
    # previous tree afterward.
    $preserveDir = Join-Path $Script:DeployLogDir "preserved_state"
    New-Item -ItemType Directory -Force -Path $preserveDir | Out-Null
    $envSrc = Join-Path $ProjectRoot ".env"
    if (Test-Path $envSrc) {
        Copy-Item -Path $envSrc -Destination (Join-Path $preserveDir ".env") -Force
    } else {
        Write-DeployLog -Level "WARN" "Current tree has no .env to preserve before quarantine."
    }
    $instanceSrc = Join-Path $ProjectRoot "instance"
    if (Test-Path $instanceSrc) {
        Copy-Item -Path $instanceSrc -Destination (Join-Path $preserveDir "instance") -Recurse -Force
    }

    Move-Item -Path $ProjectRoot -Destination $quarantineDir -Force
    Write-DeployLog "Quarantined current tree: $ProjectRoot -> $quarantineDir (NOT deleted)"
    $Script:Receipt.QUARANTINE_DIR = $quarantineDir

    Write-DeployLog "QUARANTINE PASSED."
    return $preserveDir
}

function Copy-PreviousTreeIntoPlace {
    Write-DeployLog "Phase 8/12: restore previous tree into place (copy, not move -- -PreviousDir remains intact)"

    if (Test-Path $ProjectRoot) {
        Invoke-FailClosed -Phase "RESTORE_FAILED" -Reason "ProjectRoot unexpectedly already exists after quarantine: $ProjectRoot"
    }
    New-Item -ItemType Directory -Force -Path $ProjectRoot | Out-Null

    try {
        Get-ChildItem -Path $PreviousDir -Force | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination (Join-Path $ProjectRoot $_.Name) -Recurse -Force
        }
    } catch {
        Invoke-FailClosed -Phase "RESTORE_FAILED" -Reason "Copying -PreviousDir into ProjectRoot failed: $($_.Exception.Message). The quarantined tree is still intact at $($Script:Receipt.QUARANTINE_DIR) and can be moved back manually if needed."
    }

    Write-DeployLog "Previous tree copied into place: $PreviousDir -> $ProjectRoot (source directory left intact)"
    Write-DeployLog "RESTORE PASSED."
}

function Restore-PersistentStateFromQuarantine {
    param([Parameter(Mandatory)][string]$PreserveDir)
    Write-DeployLog "Phase 9/12: reconcile .env / instance\ to the most recent versions"

    $preservedEnv = Join-Path $PreserveDir ".env"
    if (Test-Path $preservedEnv) {
        Copy-Item -Path $preservedEnv -Destination (Join-Path $ProjectRoot ".env") -Force
        Write-DeployLog "Restored the most recent .env (captured from the tree being rolled back FROM) onto the restored previous tree."
    } else {
        Write-DeployLog -Level "WARN" "No preserved .env available -- the restored previous tree keeps its own (possibly older) .env."
    }
    $preservedInstance = Join-Path $PreserveDir "instance"
    if (Test-Path $preservedInstance) {
        Copy-Item -Path $preservedInstance -Destination (Join-Path $ProjectRoot "instance") -Recurse -Force
        Write-DeployLog "Restored the most recent instance\ onto the restored previous tree."
    }
    Write-DeployLog "($StorageRoot and $LocalStorageRoot were never touched.)"
    Write-DeployLog "PERSISTENT STATE RECONCILIATION PASSED."
}

function Test-RestoredTreeIdentity {
    param([Parameter(Mandatory)][string]$ExpectedPreviousSourceSha)
    Write-DeployLog "Phase 10/12: verify restored tree identity"

    foreach ($m in @("app", "config.py", "run_server.py", "wsgi.py")) {
        if (-not (Test-Path (Join-Path $ProjectRoot $m))) {
            Invoke-FailClosed -Phase "IDENTITY_VERIFY_FAILED" -Reason "Restored tree is missing expected marker '$m'."
        }
    }
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Invoke-FailClosed -Phase "IDENTITY_VERIFY_FAILED" -Reason "Restored tree venv python.exe not found: $venvPython"
    }
    if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
        Invoke-FailClosed -Phase "IDENTITY_VERIFY_FAILED" -Reason "Restored tree has no .env after reconciliation."
    }
    $receiptPath = Join-Path $ProjectRoot "CANDIDATE_READY.json"
    if ((Test-Path $receiptPath) -and ($ExpectedPreviousSourceSha -ne "UNKNOWN")) {
        $receipt = Get-Content -Path $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($receipt.SOURCE_SHA -ne $ExpectedPreviousSourceSha) {
            Invoke-FailClosed -Phase "IDENTITY_VERIFY_FAILED" -Reason "Restored tree CANDIDATE_READY.json SOURCE_SHA '$($receipt.SOURCE_SHA)' != expected '$ExpectedPreviousSourceSha'."
        }
    }
    Write-DeployLog "Restored tree identity confirmed."
    Write-DeployLog "IDENTITY VERIFICATION PASSED."
    return $venvPython
}

# =====================================================================
# Phase 11: start service + health verification (required after the
# app-tree rollback completes)
# =====================================================================

function Start-LiveServiceAfterRollback {
    Write-DeployLog "Phase 11/12: start live Scheduled Task + health verification"
    if (Test-Path "C:\bys360\logs\bys360_live_waitress_80.log") {
        $preStartSize = (Get-Item "C:\bys360\logs\bys360_live_waitress_80.log").Length
    } else {
        $preStartSize = 0
    }

    Start-ScheduledTask -TaskName $TaskName
    $started = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Seconds 2
        $listening = Get-NetTCPConnection -LocalPort $AppPort -State Listen -ErrorAction SilentlyContinue
        if ($listening) { $started = $true; break }
    }
    if (-not $started) {
        $Script:Receipt.SERVICE_RESULT = "FAIL"
        Invoke-FailClosed -Phase "SERVICE_START_FAILED" -Reason "Nothing is listening on port $AppPort after 40 seconds post Start-ScheduledTask."
    }
    Write-DeployLog "Confirmed listening on port $AppPort."
    $Script:Receipt.SERVICE_RESULT = "PASS"

    # NOTE (found via direct testing while developing/testing
    # prepare_bys360_candidate.ps1's equivalent check): Invoke-WebRequest's
    # `-Headers @{"Host"=...}` does NOT actually change the wire-level Host
    # header under Windows PowerShell 5.1 (.NET's HttpWebRequest treats Host
    # as a restricted header and silently ignores a same-named entry in the
    # generic Headers collection) -- confirmed directly: the request still
    # 400s on TRUSTED_HOSTS validation even with the header "set" this way.
    # curl.exe (used here, matching V4's own Test-LocalHealth) has no such
    # restriction.
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) {
        Invoke-FailClosed -Phase "LOCAL_HEALTH_FAILED" -Reason "curl.exe not found on PATH -- required for a Host-header-correct local health check."
    }
    try {
        $code = (Invoke-Native {
            & curl.exe -s -o NUL -w "%{http_code}" --max-time 15 -H "Host: $PublicHostName" -H "X-Forwarded-Proto: https" "http://127.0.0.1:$AppPort/healthz" 2>&1
        } | Out-String).Trim()
    } catch {
        $Script:Receipt.LOCAL_HEALTH = "REQUEST_ERROR"
        Invoke-FailClosed -Phase "LOCAL_HEALTH_FAILED" -Reason "Local /healthz request failed after rollback: $($_.Exception.Message)"
    }
    if ($code -ne "200") {
        $Script:Receipt.LOCAL_HEALTH = "$code"
        Invoke-FailClosed -Phase "LOCAL_HEALTH_FAILED" -Reason "Local /healthz returned HTTP $code after rollback, expected 200."
    }
    $Script:Receipt.LOCAL_HEALTH = "200"
    Write-DeployLog "LOCAL HEALTH CHECK PASSED (HTTP 200) after rollback."

    if ($SkipPublicHealthCheck) {
        $Script:Receipt.PUBLIC_HEALTH = "SKIPPED"
    } else {
        try {
            $presp = Invoke-WebRequest -Uri "https://$PublicHostName/healthz" -UseBasicParsing -TimeoutSec 15
            $Script:Receipt.PUBLIC_HEALTH = "$([int]$presp.StatusCode)"
        } catch {
            $Script:Receipt.PUBLIC_HEALTH = "NETWORK_ERROR"
            Write-DeployLog -Level "WARN" "Public health check after rollback failed (non-fatal, LB/network-dependent): $($_.Exception.Message)"
        }
    }

    Write-DeployLog "SERVICE START + HEALTH VERIFICATION PASSED."
}

# =====================================================================
# Phase 12: receipt
# =====================================================================

function Write-RollbackReceipt {
    Write-DeployLog "Phase 12/12: write rollback receipt"
    $Script:Receipt.ROLLBACK_EXIT_CODE = "0"
    $receiptPath = Join-Path $Script:DeployLogDir "ROLLBACK_RECEIPT.txt"
    $lines = @("BYS360 CANDIDATE ROLLBACK -- RECEIPT", "================================================================", "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')", "")
    foreach ($key in $Script:Receipt.Keys) {
        $lines += "{0,-28}: {1}" -f $key, $Script:Receipt[$key]
    }
    $lines += ""
    $lines += "No Alembic downgrade was attempted. No DB backups were touched or deleted."
    $lines += "-PreviousDir was COPIED (not moved) and remains intact at: $PreviousDir"
    Set-Content -Path $receiptPath -Value $lines -Encoding UTF8
    Write-DeployLog "ROLLBACK RECEIPT WRITTEN: $receiptPath"
    return $receiptPath
}

# =====================================================================
# MAIN
# =====================================================================

function Main {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"

    New-Item -ItemType Directory -Force -Path $Script:DeployLogDir | Out-Null
    $Script:LogFile = Join-Path $Script:DeployLogDir "rollback.log"
    Write-DeployLog "================================================================"
    Write-DeployLog "BYS360 CANDIDATE ROLLBACK -- START (DeployId=$($Script:DeployId))"
    Write-DeployLog "================================================================"
    Write-DeployLog "  PreviousDir = $PreviousDir"
    Write-DeployLog "  ProjectRoot = $ProjectRoot"
    Write-DeployLog "  PostMigrationAppTreeCompatible = $($PostMigrationAppTreeCompatible.IsPresent)"

    Test-HostPrerequisites
    $previousIdentity = Test-PreviousDirIdentity
    $currentIdentity = Test-CurrentActiveIdentity
    Assert-ActiveDeploymentBinding -CurrentIdentity $currentIdentity -PreviousIdentity $previousIdentity

    $currentDbRevision = Get-CurrentDbRevisionForAwareness
    Test-AppTreeDbCompatibilityGate -CurrentDbRevision $currentDbRevision -PreviousIdentity $previousIdentity

    Stop-LiveService
    $preserveDir = Move-CurrentTreeToQuarantine -CurrentSourceSha $currentIdentity.SourceSha
    Copy-PreviousTreeIntoPlace
    Restore-PersistentStateFromQuarantine -PreserveDir $preserveDir
    Test-RestoredTreeIdentity -ExpectedPreviousSourceSha $previousIdentity.SourceSha | Out-Null

    Start-LiveServiceAfterRollback

    $receiptPath = Write-RollbackReceipt
    Write-DeployLog "================================================================"
    Write-DeployLog "ROLLBACK SUCCEEDED. Receipt: $receiptPath"
    Write-DeployLog "ACTIVE_SOURCE_SHA=$($previousIdentity.SourceSha) ROLLBACK_PATH=$($Script:Receipt.ROLLBACK_PATH) QUARANTINED=$($Script:Receipt.QUARANTINE_DIR)"
    Write-DeployLog "================================================================"
}

try {
    Main
    exit 0
} catch {
    $Script:Receipt.ROLLBACK_EXIT_CODE = "1"
    $existingFailureReceipt = if ($Script:DeployLogDir) { Join-Path $Script:DeployLogDir "FAILURE_RECEIPT.txt" } else { $null }
    if ($existingFailureReceipt -and (Test-Path $existingFailureReceipt)) {
        Write-DeployLog -Level "FATAL" "Stopping after phase failure (see $existingFailureReceipt)."
    } else {
        Write-DeployLog -Level "FATAL" "UNHANDLED (no prior phase-specific failure receipt): $($_.Exception.Message)"
        if ($Script:DeployLogDir) {
            Write-FailureReceipt -Phase "UNHANDLED" -Reason $_.Exception.Message | Out-Null
        }
    }
    exit 1
}
