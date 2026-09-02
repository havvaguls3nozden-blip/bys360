<#
BYS360 Candidate Preparation Script V1
=======================================

WHY THIS EXISTS (read before running)
  deploy_bys360_ec4e56b_production_v1..v4.ps1 (see scripts\windows\, kept as
  historical reference, NOT modified by this script) are monolithic
  "stop-live-then-hope" scripts: the live Scheduled Task ("BYS360 Live
  Waitress 80") is stopped and C:\bys360\project is deleted BEFORE the new
  Python venv/dependencies are fully proven installable and runnable. A real
  V4 production run got all the way through PRECHECK / PACKAGE HASH / PYTHON
  RESOLUTION / STATE CAPTURE / STAGING / DB BACKUP / a full shadow-DB
  migration rehearsal (all PASSED) and only then failed in the VENV phase --
  AFTER the live service was already stopped and the old tree already
  deleted. Post-hoc manual checks proved the runtime was actually fine; the
  real defect was SEQUENCING, not any one check.

  This script is the fix for that sequencing defect: it builds and PROVES a
  complete, independent "candidate" application tree -- its own venv, its
  own config validation, its own rehearsed migration, its own real HTTP
  health check on a non-live port -- while never touching the live service,
  the live application tree, or the live database. Only once this script
  has written a signed-off CANDIDATE_READY.json does
  cutover_bys360_candidate.ps1 become eligible to run at all (it hard-checks
  that receipt before doing anything).

WHAT THIS SCRIPT NEVER DOES (hard constraints, enforced structurally, not by
convention)
  - Never stops, starts, or reconfigures the "BYS360 Live Waitress 80"
    Scheduled Task, or any other Scheduled Task.
  - Never deletes, moves, or writes into C:\bys360\project.
  - Never migrates the LIVE database (Alembic is only ever pointed at a
    disposable shadow database created and dropped by this script itself).
  - Never binds port 80 (the candidate health boot uses a resolved,
    collision-checked, non-live port -- see Resolve-CandidateHealthPort).
  - Never writes into C:\bys360\storage or C:\bys360\local_storage.
  - Never writes a plaintext copy of production .env anywhere on disk --
    production configuration is read once (Get-Bys360ProductionEnvValues,
    via the real python-dotenv library, same parser config.py itself uses)
    and injected only as process-local environment variables for the
    duration of specific child-process calls (Invoke-WithBys360RuntimeEnvironment),
    with exact original-state restore in every case, success or failure.
  This script's own filesystem writes are confined to: C:\bys360\candidate\<SOURCE_SHA>\,
  C:\bys360\backups\, and C:\bys360\deploy_logs\.

TECHNIQUES DELIBERATELY CARRIED OVER FROM V4 (read there for the full
reasoning; not reinvented here)
  - Invoke-Native: under Set-StrictMode + $ErrorActionPreference='Stop', a
    native command's stderr merged via 2>&1 throws a TERMINATING exception
    on ANY stderr line, even with exit code 0 (Alembic logs to stderr by
    default). Every native call that captures 2>&1 goes through this
    wrapper.
  - Absolute-path Python resolution only -- never a bare `python`/`py` on
    PATH (see Resolve-Bys360BasePython312).
  - Admin PostgreSQL credential, prompted interactively exactly once
    (Read-Host -AsSecureString) only when the shadow-rehearsal phase
    actually begins, used ONLY for CREATE DATABASE / DROP DATABASE of the
    disposable shadow database -- the application role is never granted
    CREATEDB.
  - pg_restore --no-owner --no-privileges, strict exit_code -eq 0 required
    (V4 found and fixed the real bug here: a plain restore fails on
    `ALTER FUNCTION ... OWNER TO postgres` when the connecting role isn't
    postgres).
  - Assert-ShadowDatabaseTarget: a hard guard, immediately before every
    Alembic invocation against the shadow DB, that parses the ACTUAL
    runtime DATABASE_URL and refuses to proceed unless it resolves to the
    expected shadow database and NOT to any production database name.
  - Get-Bys360ProductionEnvValues / Invoke-WithBys360RuntimeEnvironment:
    real python-dotenv parsing of the CURRENT production .env, injected as
    process-local $env: variables for a child process only, restored
    exactly afterward.
  - Set-StrictMode -Version Latest, $ErrorActionPreference = 'Stop',
    fail-closed throughout, FAILURE_RECEIPT.txt written by Invoke-FailClosed
    for every phase.

ARCHITECTURAL SIMPLIFICATION THIS SCRIPT ADDS OVER V4 (disclosed, not
accidental)
  V4 had to borrow the EXISTING production venv's already-installed
  Alembic/Flask to inspect the staged package's migration head, because its
  own new venv wasn't built until after the live service was already
  stopped. This script builds the candidate's OWN venv much earlier (step
  5, entirely before anything DB- or migration-related happens) precisely
  so every later step -- Alembic head inspection, create_app() checks, the
  shadow rehearsal, the health boot -- can run fully self-sufficiently
  against the candidate's own interpreter. There is no dependency on the
  live venv anywhere in this script.

OFFLINE DEPENDENCY INSTALL -- requirements.lock / wheelhouse
  The intended, documented production path (see New-CandidateVirtualEnv) is
  fully offline: `pip install --no-index --find-links <wheelhouse> -r
  <requirements.lock>`, consuming a requirements.lock file and a wheelhouse/
  directory that a FULL release package is expected to carry at its root
  (built by scripts\release\build_bys360_wheelhouse.py, owned by a sibling
  workstream -- not present in this worktree yet at the time this script was
  written). By DEFAULT this script fails closed (VENV_FAILED) if a
  candidate package does not contain both requirements.lock and wheelhouse\.
  A single, explicitly-named, off-by-default switch,
  -AllowNetworkInstallFallback, exists ONLY so this script could be
  developed and tested against real local infrastructure before that
  sibling deliverable landed; it is loudly logged as NOT FOR PRODUCTION USE
  whenever it fires and must never be passed on a real candidate prep run.

CANDIDATE HEALTH BOOT DATABASE TARGET -- design decision (read before
assuming this connects anywhere near production)
  Step 13 boots the candidate app for a real HTTP /healthz check. Reading
  app\bootstrap\application_bootstrap.py / app\startup_checks.py /
  app\schema_guard_engine.py directly (not guessed) shows create_app()'s
  only DB-touching boot-time work is run_schema_guard_bootstrap(): a
  read-only schema check UNLESS AUTO_REPAIR_SCHEMA=true AND
  should_auto_repair_schema() -- both gated off by default
  (factory_bootstrap.py: `app.config.setdefault("AUTO_REPAIR_SCHEMA", ...
  False)`), and this script forces AUTO_REPAIR_SCHEMA=false as an explicit
  override regardless of what production's own .env says, so boot-time DB
  interaction is read-only by construction. run_startup_security_audit only
  logs. Even so, this script points the health-boot's DATABASE_URL at the
  SAME disposable shadow database already created, restored, and migrated
  to head in step 12 -- never at production, in any mode, including
  read-only -- because the shadow DB is fully disposable, already proven to
  be at the correct target revision, and this removes any real-vs-candidate
  DB coupling entirely. The shadow DB is dropped in a `finally` that wraps
  BOTH the rehearsal and the health boot, so cleanup is never skipped.
  BYS360_FEEDBACK_FOLLOWUP_SCHEDULER is confirmed (feedback_followup_scheduler.py)
  to default OFF and is force-set to "0" anyway as defense-in-depth so the
  health-boot process can never start a real background APScheduler job.

FAILURE PHASES (recorded verbatim in the failure receipt's "Phase" field)
  PRECHECK_FAILED, PACKAGE_FAILED, MANIFEST_FAILED, EXTRACT_FAILED,
  SOURCE_SHA_FAILED, VENV_FAILED, PIP_CHECK_FAILED, IMPORT_GATE_FAILED,
  APP_FACTORY_FAILED, MIGRATION_HEAD_FAILED, DB_BACKUP_FAILED,
  SHADOW_REHEARSAL_FAILED, HEALTH_BOOT_FAILED, RECEIPT_FAILED

EMBEDDED SOURCE SHA -- release-provenance trust chain (BYS360 DEFECT AH,
2026-09-02)
  scripts\release\build_bys360_safe_release.py embeds RELEASE_SOURCE_SHA.txt
  INSIDE the release ZIP itself, written before the ZIP's own per-file
  SHA256SUMS are computed -- so that file's bytes are covered by the
  whole-ZIP hash this script already verifies in Phase 2 (Test-PackageHash).
  Test-EmbeddedSourceSha (Phase 4b, right after extraction, before the
  extracted-candidate secret re-scan) reads that file
  from the extracted candidate tree, validates its format, and requires it
  to equal what Phase 3 (Test-PackageManifest) read from the sidecar
  manifest.json -- the sidecar alone is NOT cryptographically bound to the
  ZIP (it is a plain file sitting next to it) and is no longer trusted on
  its own. From that point on the EMBEDDED value is authoritative:
  $Script:Receipt.SOURCE_SHA is overwritten with it, so CANDIDATE_READY.json
  and every later phase (Test-CandidateMigrationHead's already-existing
  cross-checks, cutover_bys360_candidate.ps1's Test-ReleaseIdentityBinding,
  /versionz) are bound to a source identity that is provably part of the
  verified package bytes, not a free-standing claim next to them.
#>

[CmdletBinding()]
param(
    # ---- Release package identity --------------------------------------
    [Parameter(Mandatory = $true)][string]$PackagePath,
    [Parameter(Mandatory = $true)][string]$ExpectedPackageSha256,
    [string]$ExpectedSourceSha,          # optional cross-check; if omitted, taken from the sidecar manifest
    [string]$ExpectedTargetDbRevision,   # optional cross-check; if omitted, the candidate's own resolved Alembic head is authoritative

    # ---- Server / host identity (defense-in-depth; see script header) ---
    [string]$ExpectedHostName = "CATAB-BYS360",

    # ---- Filesystem roots -------------------------------------------------
    [string]$ProjectRoot = "C:\bys360\project",           # read-only reference only; NEVER written by this script
    [string]$CandidateRoot = "C:\bys360\candidate",
    [string]$StorageRoot = "C:\bys360\storage",            # never touched
    [string]$LocalStorageRoot = "C:\bys360\local_storage", # never touched
    [string]$BackupRoot = "C:\bys360\backups",
    [string]$DeployLogsRoot = "C:\bys360\deploy_logs",

    # ---- PostgreSQL -------------------------------------------------------
    [string]$PgBinPath = "C:\Program Files\PostgreSQL\15\bin",
    [string]$ProductionDbName,               # intentionally no default -- see Get-ProductionDbConnection
    [string]$ProductionEnvFilePath,          # defaults to "$ProjectRoot\.env" if not supplied; READ-ONLY, never copied verbatim to disk
    [string]$PostgresAdminUser = "postgres",
    # Deliberately NO -PostgresAdminPassword parameter -- see V4 header for
    # why (PowerShell history / process-listing leakage). Prompted once,
    # interactively, only when the shadow-rehearsal phase begins.

    # ---- Candidate health boot ---------------------------------------------
    [int]$CandidateHealthPortPreferred = 18080,
    [int[]]$CandidateHealthPortFallbacks = @(18081, 18082, 18083, 18084, 18085, 18086, 18087, 18088, 18089, 18090),

    # ---- Behavior toggles -----------------------------------------------------
    [switch]$AllowNetworkInstallFallback   # NEVER for production use -- see script header
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =====================================================================
# Global state / logging / receipt helpers (ported from V4; see its
# header comments for the full rationale of each pattern)
# =====================================================================

$Script:DeployId = Get-Date -Format "yyyyMMdd_HHmmss"
$Script:DeployLogDir = Join-Path $DeployLogsRoot "candidate_prep_$($Script:DeployId)"
$Script:LogFile = $null
$Script:Receipt = [ordered]@{
    SCHEMA_VERSION            = 1
    RECEIPT_KIND              = "CANDIDATE_READY"
    GENERATED_AT              = ""
    SOURCE_SHA                = ""
    PACKAGE_PATH              = $PackagePath
    PACKAGE_SHA256            = $ExpectedPackageSha256.ToLowerInvariant()
    CANDIDATE_DIR             = ""
    DEPENDENCY_LOCK_MODE      = ""   # OFFLINE_WHEELHOUSE | NETWORK_FALLBACK_TEST_ONLY
    DEPENDENCY_LOCK_FILE      = ""
    DEPENDENCY_LOCK_SHA256    = ""
    WHEELHOUSE_IDENTITY_SHA256 = ""
    PIP_CHECK                 = ""
    IMPORT_GATES              = ""
    APP_FACTORY_CHECK         = ""
    MIGRATION_HEAD            = ""
    DB_BACKUP_PATH            = ""
    SHADOW_REHEARSAL_RESULT   = ""
    SCHEMA_CONTRACT_CHECK     = ""
    FILE_CENTER_TABLES        = ""
    HEALTH_BOOT_PORT          = ""
    HEALTH_CHECK_RESULT       = ""
    CANDIDATE_READY           = "NO"
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
        "BYS360 CANDIDATE PREPARATION -- FAILURE RECEIPT"
        "================================================================"
        "Phase          : $Phase"
        "Timestamp      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        "Reason         : $Reason"
        "Log path       : $($Script:LogFile)"
        "Deploy log dir : $($Script:DeployLogDir)"
        ""
        "The live application, live database, and live Scheduled Task were"
        "NEVER touched by this script -- candidate preparation only ever"
        "writes under CandidateRoot/BackupRoot/DeployLogsRoot."
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
    <# See V4 header for the full explanation: under $ErrorActionPreference
       ='Stop', a native command's 2>&1-captured stderr throws a terminating
       exception on ANY stderr line, even with exit code 0. Every native
       call that captures 2>&1 must go through this wrapper. #>
    param([Parameter(Mandatory)][scriptblock]$Command)
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $Command
    } finally {
        $ErrorActionPreference = $previousEap
    }
}

function Assert-SafeDeletionTarget {
    <# Hard guard before ANY Remove-Item -Recurse against a computed path.
       Ported from V4; adapted so the expected suffix is parameterized
       (candidate directories live under C:\bys360\candidate\<SOURCE_SHA>\,
       not \project). #>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedExact,
        [Parameter(Mandatory)][string]$Phase
    )
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $expected = [System.IO.Path]::GetFullPath($ExpectedExact)
    if ($resolved -ne $expected) {
        Invoke-FailClosed -Phase $Phase -Reason "Refusing deletion: resolved path '$resolved' does not exactly equal expected '$expected'."
    }
    $segments = $resolved.TrimEnd('\').Split('\') | Where-Object { $_ -ne "" }
    if ($segments.Count -lt 3) {
        Invoke-FailClosed -Phase $Phase -Reason "Refusing deletion: resolved path '$resolved' is too shallow ($($segments.Count) segments) to be a safe deletion target."
    }
    if ($resolved -notmatch [regex]::Escape("\bys360\candidate\")) {
        Invoke-FailClosed -Phase $Phase -Reason "Refusing deletion: resolved path '$resolved' is not under \bys360\candidate\ -- this script must never delete anything outside the candidate tree."
    }
}

# =====================================================================
# PostgreSQL DATABASE_URL parsing (never logs/prints the password) --
# ported verbatim from V4.
# =====================================================================

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
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "Production .env not found at '$EnvPath'; cannot resolve DATABASE_URL."
    }
    $line = (Get-Content -Path $EnvPath -Encoding UTF8) | Where-Object { $_ -match '^\s*DATABASE_URL\s*=' } | Select-Object -First 1
    if (-not $line) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "DATABASE_URL not found in '$EnvPath'."
    }
    $value = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    $parsed = ConvertFrom-DatabaseUrl -Url $value
    if (-not $parsed) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "DATABASE_URL in '$EnvPath' could not be parsed as a postgresql:// URL (value itself is never logged)."
    }
    Write-DeployLog "Resolved DB connection for backup/rehearsal source: host=$($parsed.HostName) port=$($parsed.Port) db=$($parsed.Database) user=$($parsed.User) (password withheld)"
    return $parsed
}

function Test-SafePostgresIdentifier {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Identifier)
    return $Identifier -match '^[A-Za-z_][A-Za-z0-9_]{0,62}$'
}

function Test-LogForRealErrors {
    <# Ported from V4 -- deliberately NOT a bare substring match on
       "error"/"critical" (also appears in benign text like "critical=0").
       NOTE (found via direct testing, not guessed): V4's own signature is
       `[Parameter(Mandatory)][string]$LogText` -- PowerShell's Mandatory
       binding rejects an EMPTY string, not only $null ("Cannot bind
       argument to parameter 'LogText' because it is an empty string"),
       confirmed directly when a freshly-started process had produced zero
       bytes of new log output yet. [AllowEmptyString()] fixes this without
       changing the match semantics at all (an empty string correctly
       matches zero patterns either way). This is a real, latent bug
       inherited from V4 (never caught there because V4 has never been run
       end-to-end -- see its own header). #>
    param([Parameter(Mandatory)][AllowEmptyString()][string]$LogText)
    $patterns = @(
        '\|\s*(ERROR|CRITICAL)\s*\|',
        '(?m)^(ERROR|CRITICAL)\s*:',
        '\b(ERROR|CRITICAL)\b\s*:',
        '(?m)^\[(ERROR|CRITICAL)\]',
        'Traceback \(most recent call last\)',
        '\bUnicodeEncodeError\b',
        '\bUnicodeDecodeError\b',
        'sqlalchemy\.exc\.OperationalError',
        '\bSchemaAdoptionError\b'
    )
    $hits = @()
    foreach ($p in $patterns) {
        if ($LogText -match $p) { $hits += $p }
    }
    return ,$hits   # leading comma load-bearing -- see V4 for why
}

# =====================================================================
# Schema-v3 FULL-package manifest cross-binding (coordinator addition,
# 2026-08-25, schema-contract-drift wave close-out).
#
# scripts\release\build_bys360_safe_release.py's FULL build mode
# (schema_version=3, triggered by --wheelhouse-dir) records a set of
# claimed values in the sidecar manifest -- requirements_lock_sha256,
# wheelhouse_identity_sha256, wheelhouse_file_count, wheelhouse_total_bytes,
# migration_head, and SHA256 of this script and its cutover/rollback/
# secret-scanner siblings. Test-PackageManifest (Phase 3) reads and stores
# those CLAIMS (nothing to independently verify yet -- the package isn't
# extracted at that point). $Script:ExpectedFullManifest holds them; every
# later phase that independently (re)computes the real value from actual
# on-disk candidate content (New-CandidateVirtualEnv for the lock/wheelhouse
# hashes, Test-CandidateMigrationHead for the migration head, extraction
# time for the script hashes) cross-checks its OWN fresh computation
# against this claim and fails closed on any mismatch. This is the same
# "recompute fresh, never trust blindly" pattern cutover_bys360_candidate.ps1's
# Assert-ValidCandidateReceipt already uses against CANDIDATE_READY.json --
# applied here one layer earlier, against the release package's own manifest.
# $null when the package is a legacy schema_version=2 build (no FULL fields
# to cross-check against; every later gate below no-ops in that case).
# =====================================================================

$Script:ExpectedFullManifest = $null

function Get-WheelhouseIdentitySha256 {
    <# Independently recomputes the wheelhouse identity hash from actual
       on-disk .whl files -- must byte-for-byte match
       scripts\release\build_bys360_wheelhouse.py's wheelhouse_identity():
       sha256 over a UTF-8 text blob of sorted "filename:sha256\n" lines
       (case-insensitive filename sort), one line per wheel, trailing
       newline included. Returns $null if the directory has no .whl files
       (caller decides whether that is itself a failure).

       Sort MUST use ordinal (codepoint) comparison, not PowerShell's
       default culture-aware `Sort-Object` -- confirmed by real
       reproduction on this host (Turkish system locale): Python's
       `sorted(..., key=str.lower)` and PowerShell's plain
       `Sort-Object { $_.Name.ToLowerInvariant() }` produced two DIFFERENT
       orderings of the exact same 59 real wheel filenames (only
       flask-3.1.3-py3-none-any.whl's position differed), which silently
       changes the final hash even though every individual file and hash
       is identical -- a spurious cross-host/cross-locale mismatch, not a
       real integrity problem. [string]::CompareOrdinal matches Python's
       ordinal string comparison regardless of the host's locale. #>
    param([Parameter(Mandatory)][string]$WheelhouseDir)
    if (-not (Test-Path $WheelhouseDir)) {
        return $null
    }
    $wheelFiles = [System.Collections.Generic.List[System.IO.FileInfo]]::new(
        [System.IO.FileInfo[]](Get-ChildItem -Path $WheelhouseDir -Filter "*.whl" -File)
    )
    $wheelFiles.Sort([Comparison[System.IO.FileInfo]]{
        param($a, $b)
        [string]::CompareOrdinal($a.Name.ToLowerInvariant(), $b.Name.ToLowerInvariant())
    })
    if ($wheelFiles.Count -eq 0) {
        return $null
    }
    $lines = foreach ($f in $wheelFiles) {
        $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$($f.Name):$hash"
    }
    $blob = ($lines -join "`n") + "`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($blob)
    $sha256Alg = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha256Alg.ComputeHash($bytes)
    } finally {
        $sha256Alg.Dispose()
    }
    return ([System.BitConverter]::ToString($hashBytes) -replace '-', '').ToLowerInvariant()
}

function Assert-FullManifestFieldMatches {
    <# Fails closed (MANIFEST_FAILED) when $Script:ExpectedFullManifest is
       set (a schema_version=3 FULL package) and an independently-computed
       actual value diverges from what the package manifest claimed at
       build time -- proof that candidate content matches what was
       verified/signed off at build time, not just that it "looks similar". #>
    param(
        [Parameter(Mandatory)][string]$FieldLabel,
        [Parameter(Mandatory)][AllowNull()]$Expected,
        [Parameter(Mandatory)][AllowNull()]$Actual
    )
    if ($null -eq $Script:ExpectedFullManifest) { return }
    if ("$Expected" -ne "$Actual") {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "FULL package manifest cross-check failed for '$FieldLabel': manifest claims '$Expected', actual candidate content is '$Actual'. The candidate content does not match what the release manifest recorded at build time."
    }
    Write-DeployLog "FULL manifest cross-check OK: $FieldLabel = $Actual"
}

# =====================================================================
# Phase 0: Python runtime resolution -- absolute path only, never a bare
# `python`/`py` on PATH. Unlike V4, this script has no dependency on any
# EXISTING production venv (see header's "architectural simplification");
# BasePython312 is resolved once via the `py` launcher purely for path
# resolution, never invoked directly again for real work.
# =====================================================================

function Resolve-Bys360BasePython312 {
    Write-DeployLog "Phase 0: resolve base Python 3.12 runtime (absolute path only)"
    $pyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
    if (-not $pyLauncher) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "The 'py' launcher is not present on PATH; cannot resolve an absolute Python 3.12 interpreter. No bare 'python' fallback is used, per design."
    }
    $resolvedRaw = Invoke-Native { & py -3.12 -c "import sys; print(sys.executable)" 2>&1 }
    if ($LASTEXITCODE -ne 0) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "'py -3.12' failed to resolve an interpreter (exit_code=$LASTEXITCODE): $resolvedRaw"
    }
    $candidate = ($resolvedRaw | Out-String).Trim()
    if (-not (Test-Path $candidate)) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "'py -3.12' resolved a path that does not exist on disk: '$candidate'."
    }
    $candidateVersion = (Invoke-Native { & $candidate --version 2>&1 } | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $candidateVersion -notmatch 'Python 3\.12\.') {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "'py -3.12' resolved '$candidate', but it is not a working Python 3.12.x interpreter (version check: '$candidateVersion')."
    }
    Write-DeployLog "BasePython312 resolved: $candidate ($candidateVersion)"
    return $candidate
}

# =====================================================================
# Phase 1: host prerequisites
# =====================================================================

function Test-HostPrerequisites {
    Write-DeployLog "Phase 1/16: PRECHECK -- host prerequisites"

    $actualHostName = $env:COMPUTERNAME
    if ($actualHostName -ne $ExpectedHostName) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "hostname mismatch: expected '$ExpectedHostName', actual '$actualHostName'. Candidate preparation refuses to run on any host other than the production host, even though it never touches the live service, as defense-in-depth."
    }
    Write-DeployLog "Hostname OK: $actualHostName"

    if (-not (Test-Path (Join-Path $PgBinPath "pg_dump.exe"))) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "pg_dump.exe not found at expected path: $PgBinPath"
    }
    if (-not (Test-Path (Join-Path $PgBinPath "pg_restore.exe"))) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "pg_restore.exe not found at expected path: $PgBinPath"
    }
    if (-not (Test-Path (Join-Path $PgBinPath "psql.exe"))) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "psql.exe not found at expected path: $PgBinPath"
    }
    Write-DeployLog "PostgreSQL 15 client tools confirmed at $PgBinPath"

    if (-not $ProductionDbName) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "-ProductionDbName was not supplied and has no default, by design (see Get-ProductionDbConnection). Re-run with -ProductionDbName <actual-db-name>."
    }

    if (-not (Test-Path $CandidateRoot)) {
        New-Item -ItemType Directory -Force -Path $CandidateRoot | Out-Null
        Write-DeployLog "Created CandidateRoot: $CandidateRoot"
    }
    if (-not (Test-Path $BackupRoot)) {
        New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
    }

    Write-DeployLog "HOST PREREQUISITES PASSED."
}

# =====================================================================
# Phase 2: package SHA256 hash gate (no extraction yet)
# =====================================================================

function Test-PackageHash {
    Write-DeployLog "Phase 2/16: PACKAGE -- hash gate"
    if (-not (Test-Path $PackagePath)) {
        Invoke-FailClosed -Phase "PACKAGE_FAILED" -Reason "Package not found at '$PackagePath'."
    }
    $actualHash = (Get-FileHash -Path $PackagePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $expectedHash = $ExpectedPackageSha256.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) {
        Invoke-FailClosed -Phase "PACKAGE_FAILED" -Reason "Package SHA256 mismatch. expected=$expectedHash actual=$actualHash. Package NOT extracted."
    }
    Write-DeployLog "Package hash OK: $actualHash"
    Write-DeployLog "PACKAGE HASH GATE PASSED."
}

# =====================================================================
# Phase 3: sidecar manifest verification
#
# NOTE (honest disclosure): scripts\release\build_bys360_safe_release.py's
# sidecar manifest schema (schema_version=2, at the time this script was
# written) carries schema_version / package / generated_at / source_sha /
# included_count / files[] / excluded_count / excluded_sample /
# sha256sums_file -- it does NOT carry a migration-head/db-revision field.
# "Verify migration head matches what the package manifest declares"
# (task step 10) is therefore realized in Test-CandidateMigrationHead
# (Phase 8, after the candidate venv exists) against the candidate's OWN
# migrations\ tree, optionally hard-cross-checked against an
# operator-supplied -ExpectedTargetDbRevision -- not against a manifest
# JSON field, because no such field exists upstream. This is disclosed
# here and in the final report, not silently worked around.
# =====================================================================

function Test-PackageManifest {
    Write-DeployLog "Phase 3/16: MANIFEST -- sidecar manifest verification"

    $sidecarStem = [System.IO.Path]::GetFileNameWithoutExtension($PackagePath)
    $packageDir = Split-Path -Parent $PackagePath
    $manifestPath = Join-Path $packageDir "$sidecarStem.manifest.json"
    $sha256sumsPath = Join-Path $packageDir "$sidecarStem.sha256sums.txt"

    if (-not (Test-Path $manifestPath)) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Sidecar manifest not found next to package: $manifestPath"
    }

    try {
        $manifest = Get-Content -Path $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Sidecar manifest is not valid JSON: $($_.Exception.Message)"
    }

    if (-not $manifest.schema_version) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest missing required field: schema_version"
    }
    if (-not $manifest.source_sha) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest missing required field: source_sha"
    }
    if ($null -eq $manifest.included_count) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest missing required field: included_count"
    }
    if (-not $manifest.files -or @($manifest.files).Count -eq 0) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest 'files' array is missing or empty."
    }
    if (@($manifest.files).Count -ne [int]$manifest.included_count) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest included_count ($($manifest.included_count)) does not match files[] length ($(@($manifest.files).Count))."
    }

    $requiredPrefixes = @("app/", "migrations/", "requirements.txt", "wsgi.py", "run_server.py", "config.py")
    foreach ($prefix in $requiredPrefixes) {
        $found = @($manifest.files) | Where-Object { $_ -eq $prefix -or $_.StartsWith($prefix) } | Select-Object -First 1
        if (-not $found) {
            Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest does not list required content: $prefix"
        }
    }

    if ($ExpectedSourceSha -and $manifest.source_sha -ne $ExpectedSourceSha) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Manifest source_sha '$($manifest.source_sha)' != -ExpectedSourceSha '$ExpectedSourceSha'."
    }

    if ($manifest.schema_version -eq 3) {
        Write-DeployLog "Phase 3a/16: schema-v3 FULL package manifest -- reading claimed binding fields"
        $fullRequiredFields = @(
            "requirements_lock_sha256", "wheelhouse_identity_sha256", "wheelhouse_file_count",
            "wheelhouse_total_bytes", "migration_head", "candidate_script_sha256",
            "cutover_script_sha256", "rollback_script_sha256", "secret_scanner_sha256"
        )
        foreach ($field in $fullRequiredFields) {
            $value = $manifest.$field
            if ($null -eq $value -or "$value" -eq "") {
                Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "FULL package manifest (schema_version=3) is missing required field: $field"
            }
        }
        if ($manifest.secret_scan_status -ne "PASS" -or [int]$manifest.secret_scan_findings -ne 0) {
            Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "FULL package manifest records secret_scan_status='$($manifest.secret_scan_status)' secret_scan_findings='$($manifest.secret_scan_findings)' -- release build did not pass its own assembled-tree secret gate. Refusing to prepare a candidate from a package the builder itself did not certify secret-clean."
        }
        $Script:ExpectedFullManifest = @{
            requirements_lock_sha256   = [string]$manifest.requirements_lock_sha256
            wheelhouse_identity_sha256 = [string]$manifest.wheelhouse_identity_sha256
            wheelhouse_file_count      = [int]$manifest.wheelhouse_file_count
            wheelhouse_total_bytes     = [long]$manifest.wheelhouse_total_bytes
            migration_head             = [string]$manifest.migration_head
            candidate_script_sha256    = [string]$manifest.candidate_script_sha256
            cutover_script_sha256      = [string]$manifest.cutover_script_sha256
            rollback_script_sha256     = [string]$manifest.rollback_script_sha256
            secret_scanner_sha256      = [string]$manifest.secret_scanner_sha256
        }
        Write-DeployLog "FULL manifest claims recorded (to be cross-checked against actual candidate content in later phases): migration_head=$($Script:ExpectedFullManifest.migration_head) wheelhouse_file_count=$($Script:ExpectedFullManifest.wheelhouse_file_count) secret_scan_status=PASS secret_scan_findings=0"
    } else {
        Write-DeployLog "Manifest schema_version=$($manifest.schema_version) (legacy, no FULL wheelhouse/migration-head/script-hash fields to cross-bind)."
    }

    if (Test-Path $sha256sumsPath) {
        $sumsLineCount = @(Get-Content -Path $sha256sumsPath -Encoding UTF8 | Where-Object { $_.Trim() -ne "" }).Count
        if ($sumsLineCount -ne [int]$manifest.included_count) {
            Write-DeployLog -Level "WARN" "sha256sums.txt line count ($sumsLineCount) differs from manifest included_count ($($manifest.included_count)) -- informational only, the whole-ZIP hash gate (Phase 2) already passed."
        }
    } else {
        Write-DeployLog -Level "WARN" "No sidecar sha256sums.txt found next to the package -- per-file cross-check skipped (whole-ZIP hash gate already passed)."
    }

    $Script:Receipt.SOURCE_SHA = $manifest.source_sha
    Write-DeployLog "Manifest verified: schema_version=$($manifest.schema_version) source_sha=$($manifest.source_sha) included_count=$($manifest.included_count)"
    Write-DeployLog "MANIFEST VERIFICATION PASSED."
    return $manifest.source_sha
}

# =====================================================================
# Phase 4: extract package into C:\bys360\candidate\<SOURCE_SHA>\
# =====================================================================

function Expand-CandidatePackage {
    param([Parameter(Mandatory)][string]$SourceSha)

    Write-DeployLog "Phase 4/16: extract release package into candidate tree"

    $candidateDir = Join-Path $CandidateRoot $SourceSha
    if (Test-Path $candidateDir) {
        Write-DeployLog -Level "WARN" "Candidate directory already exists (stale run?): $candidateDir -- removing before re-extraction."
        Assert-SafeDeletionTarget -Path $candidateDir -ExpectedExact $candidateDir -Phase "EXTRACT_FAILED"
        Remove-Item -Path $candidateDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $candidateDir | Out-Null

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    try {
        [System.IO.Compression.ZipFile]::ExtractToDirectory($PackagePath, $candidateDir)
    } catch {
        Invoke-FailClosed -Phase "EXTRACT_FAILED" -Reason "ZIP extraction failed: $($_.Exception.Message)"
    }

    $requiredPaths = @("app", "migrations", "requirements.txt", "wsgi.py", "run_server.py", "config.py")
    foreach ($rp in $requiredPaths) {
        if (-not (Test-Path (Join-Path $candidateDir $rp))) {
            Invoke-FailClosed -Phase "EXTRACT_FAILED" -Reason "Required package content missing after extraction: $rp"
        }
    }

    $Script:Receipt.CANDIDATE_DIR = $candidateDir
    Write-DeployLog "Candidate package extracted and required content verified: $candidateDir"

    if ($Script:ExpectedFullManifest) {
        Write-DeployLog "Phase 4a/16: FULL manifest script-hash cross-check (extracted candidate vs. manifest claim)"
        $scriptChecks = @(
            @{ Label = "candidate_script_sha256"; RelPath = "scripts\windows\prepare_bys360_candidate.ps1" },
            @{ Label = "cutover_script_sha256";   RelPath = "scripts\windows\cutover_bys360_candidate.ps1" },
            @{ Label = "rollback_script_sha256";  RelPath = "scripts\windows\rollback_bys360_candidate.ps1" },
            @{ Label = "secret_scanner_sha256";   RelPath = "scripts\release\scan_bys360_release_secrets.py" }
        )
        foreach ($check in $scriptChecks) {
            $fullPath = Join-Path $candidateDir $check.RelPath
            if (-not (Test-Path $fullPath)) {
                Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "FULL manifest claims a $($check.Label) but the extracted candidate is missing the file it should hash: $($check.RelPath)"
            }
            $actualHash = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
            Assert-FullManifestFieldMatches -FieldLabel $check.Label -Expected $Script:ExpectedFullManifest[$check.Label] -Actual $actualHash
        }
    }

    Write-DeployLog "EXTRACTION PASSED."
    return $candidateDir
}

# =====================================================================
# Phase 4b: embedded RELEASE_SOURCE_SHA.txt verification (BYS360 DEFECT AH)
#
# See the script header's "EMBEDDED SOURCE SHA" section for the full
# rationale. Summary: Phase 3 (Test-PackageManifest) read source_sha from
# the sidecar manifest.json, which is NOT cryptographically bound to the
# ZIP (Phase 2's whole-ZIP hash only covers the ZIP's own bytes). An
# attacker or an honest mistake (e.g. a stale manifest.json copied next to
# a newer zip) editing that one sidecar field alone would previously go
# completely undetected. scripts\release\build_bys360_safe_release.py now
# embeds RELEASE_SOURCE_SHA.txt INSIDE the ZIP before its own SHA256SUMS
# are computed, so that file's bytes ARE covered by Phase 2's hash gate.
# This function makes the sidecar no longer the sole source of truth: it
# requires the embedded value to equal what Phase 3 read from the sidecar,
# then makes the EMBEDDED value authoritative for everything downstream
# (CANDIDATE_READY.json, cutover's Test-ReleaseIdentityBinding, /versionz).
# =====================================================================

function Test-EmbeddedSourceSha {
    param([Parameter(Mandatory)][string]$CandidateDir)

    Write-DeployLog "Phase 4b/16: embedded RELEASE_SOURCE_SHA.txt verification"

    $embeddedPath = Join-Path $CandidateDir "RELEASE_SOURCE_SHA.txt"
    if (-not (Test-Path $embeddedPath)) {
        Invoke-FailClosed -Phase "SOURCE_SHA_FAILED" -Reason "Extracted candidate is missing RELEASE_SOURCE_SHA.txt -- this release package does not embed an authenticated source SHA (built by an older/incompatible builder, or the embedded file was stripped). Refusing to trust the sidecar manifest source_sha alone."
    }

    $embeddedRaw = Get-Content -Path $embeddedPath -Raw -Encoding UTF8
    $embeddedSha = $embeddedRaw.Trim().ToLowerInvariant()

    if ($embeddedSha -notmatch '^[0-9a-f]{40}$') {
        Invoke-FailClosed -Phase "SOURCE_SHA_FAILED" -Reason "Embedded RELEASE_SOURCE_SHA.txt content is not a valid 40-hex-character git SHA: '$embeddedRaw'."
    }

    $sidecarSha = $Script:Receipt.SOURCE_SHA
    if ($embeddedSha -ne $sidecarSha) {
        Invoke-FailClosed -Phase "SOURCE_SHA_FAILED" -Reason "Sidecar manifest source_sha ('$sidecarSha') does not match the embedded, package-integrity-authenticated RELEASE_SOURCE_SHA.txt ('$embeddedSha'). manifest.json is not cryptographically bound to the ZIP and may have been edited independently -- refusing to trust it. The embedded value is authoritative and the two disagree, so this candidate is rejected."
    }

    if ($ExpectedSourceSha -and $embeddedSha -ne $ExpectedSourceSha.ToLowerInvariant()) {
        Invoke-FailClosed -Phase "SOURCE_SHA_FAILED" -Reason "Embedded RELEASE_SOURCE_SHA.txt ('$embeddedSha') != -ExpectedSourceSha ('$ExpectedSourceSha')."
    }

    $Script:Receipt.SOURCE_SHA = $embeddedSha
    Write-DeployLog "Embedded source SHA verified and now authoritative: SOURCE_SHA=$embeddedSha (matches sidecar manifest and, if supplied, -ExpectedSourceSha)."
    Write-DeployLog "EMBEDDED SOURCE SHA VERIFICATION PASSED."
    return $embeddedSha
}

# =====================================================================
# Phase 4c: extracted-candidate secret re-scan (defense in depth).
#
# scripts\release\build_bys360_safe_release.py already requires a clean
# scripts\release\scan_bys360_release_secrets.py pass against the ASSEMBLED
# staging tree before it will finalize a FULL (schema_version=3) package at
# all (secret_scan_status/secret_scan_findings, already required to be
# PASS/0 by Test-PackageManifest above). This step independently re-runs
# that same scanner -- using the extracted CANDIDATE's own on-disk copy of
# it, the one just hash-verified in Phase 4a -- directly against
# $CandidateDir, so candidate preparation never merely trusts the
# manifest's claim: it proves EXTRACTED_RELEASE_SECRET_FINDINGS = 0 on the
# actual bytes about to become a running candidate. The scanner is pure
# stdlib (re/math/json/argparse/dataclasses/pathlib) so BasePython312 is
# sufficient; the candidate venv does not need to exist yet.
# =====================================================================

function Test-CandidateExtractedSecretScan {
    param(
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$BasePython312
    )
    Write-DeployLog "Phase 4c/16: extracted-candidate secret re-scan (defense in depth)"

    $scannerPath = Join-Path $CandidateDir "scripts\release\scan_bys360_release_secrets.py"
    if (-not (Test-Path $scannerPath)) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Extracted candidate is missing scripts\release\scan_bys360_release_secrets.py -- cannot perform the required extracted-release secret re-scan."
    }

    $scanOutput = Invoke-Native { & $BasePython312 $scannerPath $CandidateDir --json 2>&1 }
    $scanExit = $LASTEXITCODE
    $scanText = ($scanOutput | Out-String).Trim()

    $scanJson = $null
    try { $scanJson = $scanText | ConvertFrom-Json } catch { $scanJson = $null }

    if ($scanExit -eq 2 -or $null -eq $scanJson) {
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "Extracted-candidate secret scan could not be completed (usage/parse error, exit_code=$scanExit): $scanText"
    }
    if ($scanExit -ne 0 -or $scanJson.finding_count -ne 0) {
        # Findings are already redacted by the scanner itself -- safe to log verbatim.
        Invoke-FailClosed -Phase "MANIFEST_FAILED" -Reason "EXTRACTED_RELEASE_SECRET_FINDINGS != 0 (found $($scanJson.finding_count) across $($scanJson.files_scanned) files). Candidate preparation refuses to proceed with a candidate tree that fails its own secret gate: $scanText"
    }
    Write-DeployLog "EXTRACTED_RELEASE_SECRET_FINDINGS = 0 (files_scanned=$($scanJson.files_scanned))."
    Write-DeployLog "EXTRACTED-CANDIDATE SECRET RE-SCAN PASSED."
}

# =====================================================================
# Phase 5: candidate virtual environment -- offline-first (see script
# header for the full design rationale and the -AllowNetworkInstallFallback
# escape hatch, which must NEVER be used in production).
# =====================================================================

function New-CandidateVirtualEnv {
    param(
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$BasePython312
    )

    Write-DeployLog "Phase 5/16: build candidate virtual environment"

    $venvPath = Join-Path $CandidateDir ".venv"
    if (Test-Path $venvPath) {
        Remove-Item -Recurse -Force -Path $venvPath
    }
    Invoke-Native { & $BasePython312 -m venv $venvPath 2>&1 } | ForEach-Object { Write-DeployLog "venv: $_" }
    Assert-NativeSuccess -Phase "VENV_FAILED" -CommandDescription "candidate venv creation"

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Invoke-FailClosed -Phase "VENV_FAILED" -Reason "venv python.exe not found after creation: $venvPython"
    }

    Invoke-Native { & $venvPython -m pip install --quiet --disable-pip-version-check --upgrade pip 2>&1 } | ForEach-Object { Write-DeployLog "pip: $_" }
    Assert-NativeSuccess -Phase "VENV_FAILED" -CommandDescription "pip upgrade"

    # ---- REAL production path: fully offline, consuming the FULL
    # package's own bundled requirements.lock + wheelhouse\ (produced by
    # scripts\release\build_bys360_wheelhouse.py, a sibling workstream's
    # deliverable). This is the path the script actually implements and
    # documents as its intended behavior.
    $lockFile = Join-Path $CandidateDir "requirements.lock"
    $wheelhouseDir = Join-Path $CandidateDir "wheelhouse"
    $offlineAvailable = (Test-Path $lockFile) -and (Test-Path $wheelhouseDir)

    if ($offlineAvailable) {
        Write-DeployLog "Offline dependency install: requirements.lock + wheelhouse\ found in candidate package -- using --no-index --find-links (no network access)."
        Push-Location $CandidateDir
        try {
            Invoke-Native { & $venvPython -m pip install --quiet --disable-pip-version-check --no-index --find-links $wheelhouseDir -r $lockFile 2>&1 } | ForEach-Object { Write-DeployLog "pip(offline): $_" }
            Assert-NativeSuccess -Phase "VENV_FAILED" -CommandDescription "offline requirements.lock install (--no-index --find-links wheelhouse)"
        } finally {
            Pop-Location
        }
        $Script:Receipt.DEPENDENCY_LOCK_MODE = "OFFLINE_WHEELHOUSE"
        $Script:Receipt.DEPENDENCY_LOCK_FILE = "requirements.lock"
        $Script:Receipt.DEPENDENCY_LOCK_SHA256 = (Get-FileHash -Path $lockFile -Algorithm SHA256).Hash.ToLowerInvariant()

        Write-DeployLog "Phase 5a/16: independently compute wheelhouse identity from actual extracted wheel files"
        $wheelFilesActual = @(Get-ChildItem -Path $wheelhouseDir -Filter "*.whl" -File)
        $actualWheelhouseIdentity = Get-WheelhouseIdentitySha256 -WheelhouseDir $wheelhouseDir
        if (-not $actualWheelhouseIdentity) {
            Invoke-FailClosed -Phase "VENV_FAILED" -Reason "Candidate wheelhouse directory contains no .whl files -- cannot compute wheelhouse identity: $wheelhouseDir"
        }
        $Script:Receipt.WHEELHOUSE_IDENTITY_SHA256 = $actualWheelhouseIdentity
        $actualWheelhouseTotalBytes = ($wheelFilesActual | Measure-Object -Property Length -Sum).Sum
        Write-DeployLog "Wheelhouse identity (independently computed, NOT copied from manifest): $actualWheelhouseIdentity ($($wheelFilesActual.Count) wheels, $actualWheelhouseTotalBytes bytes)"

        if ($Script:ExpectedFullManifest) {
            Assert-FullManifestFieldMatches -FieldLabel "requirements_lock_sha256" -Expected $Script:ExpectedFullManifest.requirements_lock_sha256 -Actual $Script:Receipt.DEPENDENCY_LOCK_SHA256
            Assert-FullManifestFieldMatches -FieldLabel "wheelhouse_identity_sha256" -Expected $Script:ExpectedFullManifest.wheelhouse_identity_sha256 -Actual $actualWheelhouseIdentity
            Assert-FullManifestFieldMatches -FieldLabel "wheelhouse_file_count" -Expected $Script:ExpectedFullManifest.wheelhouse_file_count -Actual $wheelFilesActual.Count
            Assert-FullManifestFieldMatches -FieldLabel "wheelhouse_total_bytes" -Expected $Script:ExpectedFullManifest.wheelhouse_total_bytes -Actual $actualWheelhouseTotalBytes
        }
    } elseif ($AllowNetworkInstallFallback) {
        Write-DeployLog -Level "WARN" "requirements.lock/wheelhouse NOT found in candidate package -- -AllowNetworkInstallFallback was supplied, falling back to a NETWORK pip install -r requirements.txt. THIS IS NOT FOR PRODUCTION USE. This fallback exists solely so this script could be developed/tested before the wheelhouse-builder sibling deliverable existed in this worktree."
        $reqFile = Join-Path $CandidateDir "requirements.txt"
        if (-not (Test-Path $reqFile)) {
            Invoke-FailClosed -Phase "VENV_FAILED" -Reason "Neither requirements.lock+wheelhouse nor requirements.txt found in candidate package: $CandidateDir"
        }
        Push-Location $CandidateDir
        try {
            Invoke-Native { & $venvPython -m pip install --quiet --disable-pip-version-check -r requirements.txt 2>&1 } | ForEach-Object { Write-DeployLog "pip(NETWORK-FALLBACK-TEST-ONLY): $_" }
            Assert-NativeSuccess -Phase "VENV_FAILED" -CommandDescription "NETWORK FALLBACK requirements.txt install (test-only path)"
        } finally {
            Pop-Location
        }
        $Script:Receipt.DEPENDENCY_LOCK_MODE = "NETWORK_FALLBACK_TEST_ONLY"
        $Script:Receipt.DEPENDENCY_LOCK_FILE = "requirements.txt"
        $Script:Receipt.DEPENDENCY_LOCK_SHA256 = (Get-FileHash -Path $reqFile -Algorithm SHA256).Hash.ToLowerInvariant()
    } else {
        Invoke-FailClosed -Phase "VENV_FAILED" -Reason "Candidate package does not contain both requirements.lock and wheelhouse\ under '$CandidateDir'. Offline install is the required production path and this script fails closed rather than silently reaching the network. If this is a deliberate local test run without the wheelhouse sibling deliverable, re-run with -AllowNetworkInstallFallback (NEVER on production)."
    }

    $versionOutput = (Invoke-Native { & $venvPython --version 2>&1 } | Out-String).Trim()
    Assert-NativeSuccess -Phase "VENV_FAILED" -CommandDescription "venv python --version"
    Write-DeployLog "Candidate venv Python: $versionOutput"
    if ($versionOutput -notmatch "3\.12") {
        Write-DeployLog -Level "WARN" "Candidate venv Python version is '$versionOutput', expected 3.12.x."
    }

    Write-DeployLog "CANDIDATE VIRTUAL ENVIRONMENT PASSED."
    return $venvPython
}

# =====================================================================
# Phase 6: pip check
# =====================================================================

function Test-CandidatePipCheck {
    param([Parameter(Mandatory)][string]$VenvPython)

    Write-DeployLog "Phase 6/16: pip check"
    $output = Invoke-Native { & $VenvPython -m pip check 2>&1 }
    $exitCode = $LASTEXITCODE
    $outputText = ($output | Out-String).Trim()
    Write-DeployLog "pip check output: $outputText"
    if ($exitCode -ne 0) {
        $Script:Receipt.PIP_CHECK = "FAIL"
        Invoke-FailClosed -Phase "PIP_CHECK_FAILED" -Reason "pip check failed (exit_code=$exitCode): $outputText"
    }
    $Script:Receipt.PIP_CHECK = "PASS"
    Write-DeployLog "PIP CHECK PASSED."
}

# =====================================================================
# Phase 7: import gates -- deliberately via importlib.metadata.version(),
# NOT `flask.__version__`-style attribute access. The coordinator's wave
# prompt explicitly flags the latter as exactly the class of brittle check
# that caused V4's false VENV_FAILED (the runtime was actually fine; the
# check itself was wrong). importlib.metadata reads installed-distribution
# metadata directly and does not depend on a package exposing a
# `__version__` attribute at all.
# =====================================================================

function Test-CandidateImportGates {
    param([Parameter(Mandatory)][string]$VenvPython)

    Write-DeployLog "Phase 7/16: import gates (importlib.metadata.version, not __version__ attributes)"

    $distributions = @(
        "Flask", "Flask-Login", "Flask-SQLAlchemy", "Flask-WTF", "Flask-Migrate",
        "SQLAlchemy", "psycopg2-binary", "python-dotenv", "WTForms", "waitress", "alembic"
    )
    # NOTE: the "dists = [...]" line is built into its own variable FIRST,
    # not inline as a "literal" + (...) expression inside the @() array
    # below -- found via direct testing that PowerShell's array-literal
    # comma-list parser silently splits an inline `"text" + (nested (...))
    # -join ...)` expression into TWO separate array elements (the plain
    # string, then the parenthesized remainder) instead of concatenating
    # them, with no error -- it just silently produces a broken Python
    # script ("dists = " on its own line, followed by "[...]" on the next).
    # Confirmed directly, not guessed. Assigning to a plain variable first
    # and referencing that bare variable inside @() avoids the ambiguity
    # entirely.
    $distsLiteral = "[" + (($distributions | ForEach-Object { '"' + $_ + '"' }) -join ", ") + "]"
    $distsLine = "dists = $distsLiteral"
    $pyLines = @(
        "import importlib.metadata as im",
        "import json, sys",
        $distsLine,
        "result = {}",
        "missing = []",
        "for d in dists:",
        "    try:",
        "        result[d] = im.version(d)",
        "    except im.PackageNotFoundError:",
        "        missing.append(d)",
        "print(json.dumps({'versions': result, 'missing': missing}))",
        "sys.exit(1 if missing else 0)"
    )
    $tmpScript = Join-Path $env:TEMP "bys360_import_gates_$($Script:DeployId).py"
    Set-Content -Path $tmpScript -Value $pyLines -Encoding UTF8
    try {
        $output = Invoke-Native { & $VenvPython $tmpScript 2>&1 }
        $exitCode = $LASTEXITCODE
    } finally {
        Remove-Item -Path $tmpScript -ErrorAction SilentlyContinue
    }
    $outputText = ($output | Out-String).Trim()
    Write-DeployLog "Import gate result: $outputText"
    if ($exitCode -ne 0) {
        $Script:Receipt.IMPORT_GATES = "FAIL"
        Invoke-FailClosed -Phase "IMPORT_GATE_FAILED" -Reason "One or more required distributions are not importable in the candidate venv: $outputText"
    }
    $Script:Receipt.IMPORT_GATES = "PASS"
    Write-DeployLog "IMPORT GATES PASSED."
}

# =====================================================================
# Production .env parsing + scoped environment injection -- ported from
# V4 (Get-Bys360ProductionEnvValues / Invoke-WithBys360RuntimeEnvironment).
# Uses the CANDIDATE's own venv (which now has python-dotenv installed,
# per requirements.txt/requirements.lock), not any production venv.
# =====================================================================

function Get-Bys360ProductionEnvValues {
    param(
        [Parameter(Mandatory)][string]$VenvPython,
        [Parameter(Mandatory)][string]$EnvFilePath
    )
    if (-not (Test-Path $EnvFilePath)) {
        Invoke-FailClosed -Phase "APP_FACTORY_FAILED" -Reason "Production .env not found at '$EnvFilePath' -- cannot build the injected runtime environment."
    }
    $pyLines = @(
        'import sys, json',
        'from dotenv import dotenv_values',
        'values = dotenv_values(sys.argv[1])',
        'print(json.dumps({k: v for k, v in values.items() if v is not None}))'
    )
    $tmpScript = Join-Path $env:TEMP "bys360_dotenv_parse_$($Script:DeployId).py"
    Set-Content -Path $tmpScript -Value $pyLines -Encoding UTF8
    try {
        $jsonOutput = Invoke-Native { & $VenvPython $tmpScript $EnvFilePath 2>&1 }
        $exitCode = $LASTEXITCODE
    } finally {
        Remove-Item -Path $tmpScript -ErrorAction SilentlyContinue
    }
    if ($exitCode -ne 0) {
        Invoke-FailClosed -Phase "APP_FACTORY_FAILED" -Reason "Failed to parse production .env via python-dotenv (exit_code=$exitCode)."
    }
    try {
        $parsed = ($jsonOutput | Out-String).Trim() | ConvertFrom-Json
    } catch {
        Invoke-FailClosed -Phase "APP_FACTORY_FAILED" -Reason "Production .env parse output was not valid JSON."
    }
    $result = @{}
    foreach ($prop in $parsed.PSObject.Properties) {
        $result[$prop.Name] = [string]$prop.Value
    }
    Write-DeployLog "Production .env parsed via python-dotenv: $($result.Count) variables loaded (values withheld)."
    return $result
}

function Invoke-WithBys360RuntimeEnvironment {
    <# Ported verbatim from V4 -- see its header for the closure/scoping
       notes. Restores EVERY injected variable to its EXACT prior state
       (original value, or fully removed if absent) in `finally`. #>
    param(
        [Parameter(Mandatory)][hashtable]$EnvironmentValues,
        [Parameter(Mandatory)][scriptblock]$ScriptBlock
    )
    $priorState = @{}
    foreach ($key in $EnvironmentValues.Keys) {
        $hadValue = Test-Path "Env:\$key"
        $priorState[$key] = @{ HadValue = $hadValue; Value = if ($hadValue) { (Get-Item "Env:\$key").Value } else { $null } }
        Set-Item -Path "Env:\$key" -Value $EnvironmentValues[$key]
    }
    try {
        & $ScriptBlock
    } finally {
        foreach ($key in $priorState.Keys) {
            if ($priorState[$key].HadValue) {
                Set-Item -Path "Env:\$key" -Value $priorState[$key].Value
            } else {
                Remove-Item -Path "Env:\$key" -ErrorAction SilentlyContinue
            }
        }
    }
}

# =====================================================================
# Phase 8: create_app() import + config validation, under the injected
# production environment. This is the exact SECRET_KEY-class check V4
# needed at its Phase 10 (see V4 header, section "V4 HOTFIX"). Unlike V4's
# shadow migration step, DATABASE_URL is deliberately overridden away from
# BOTH production and the (not-yet-created) shadow DB, to a local sqlite
# target -- see script header design note. This keeps this specific check
# scoped to "does config.py / create_app() accept the real secret material"
# without any DB dependency at all; the real DB-touching health boot
# happens later in Phase 12-13, against the disposable shadow database.
# =====================================================================

function Test-CandidateAppFactory {
    param(
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$VenvPython,
        [Parameter(Mandatory)][hashtable]$ProductionEnvValues
    )

    Write-DeployLog "Phase 8/16: create_app() import + config validation (real production secret material, DATABASE_URL overridden to a local sqlite target for this check only)"

    $scratchSqlite = Join-Path $env:TEMP "bys360_candidate_factory_check_$($Script:DeployId).sqlite3"
    $overrides = @{
        DATABASE_URL = "sqlite:///$scratchSqlite"
        FLASK_APP = "wsgi.py"
        FLASK_SKIP_SCHEMA_VALIDATION = "1"
        AUTO_REPAIR_SCHEMA = "false"
        STRICT_ENV_VALIDATION = "false"
        REQUIRE_DOTENV_FILE = "false"
        BYS360_FEEDBACK_FOLLOWUP_SCHEDULER = "0"
    }
    $runtimeEnv = @{}
    foreach ($k in $ProductionEnvValues.Keys) { $runtimeEnv[$k] = $ProductionEnvValues[$k] }
    foreach ($k in $overrides.Keys) { $runtimeEnv[$k] = $overrides[$k] }

    # NOTE (found via direct testing): `python <script.py>` puts the
    # SCRIPT's OWN directory on sys.path[0], NOT the process's current
    # working directory -- Push-Location $CandidateDir below does not, by
    # itself, make `from app import create_app` resolvable when the probe
    # script physically lives under $env:TEMP. sys.path.insert(0, ...) with
    # the candidate directory fixes this regardless of where the temp
    # script file itself is written.
    $probeLines = @(
        "import sys",
        "sys.path.insert(0, r'$CandidateDir')",
        "from app import create_app",
        "app = create_app()",
        "print('CREATE_APP_OK')"
    )
    $tmpProbe = Join-Path $env:TEMP "bys360_factory_probe_$($Script:DeployId).py"
    Set-Content -Path $tmpProbe -Value $probeLines -Encoding UTF8

    Push-Location $CandidateDir
    try {
        Invoke-WithBys360RuntimeEnvironment -EnvironmentValues $runtimeEnv -ScriptBlock {
            $Script:ProbeOutput = Invoke-Native { & $VenvPython $tmpProbe 2>&1 }
            $Script:ProbeExit = $LASTEXITCODE
        }
    } finally {
        Pop-Location
        Remove-Item -Path $tmpProbe -ErrorAction SilentlyContinue
        Remove-Item -Path $scratchSqlite -ErrorAction SilentlyContinue
    }

    $probeText = ($Script:ProbeOutput | Out-String)
    Write-DeployLog "create_app() probe output: $probeText"
    if ($Script:ProbeExit -ne 0 -or $probeText -notmatch "CREATE_APP_OK") {
        $Script:Receipt.APP_FACTORY_CHECK = "FAIL"
        Invoke-FailClosed -Phase "APP_FACTORY_FAILED" -Reason "create_app() did not import/validate cleanly under the injected production environment (exit_code=$($Script:ProbeExit)): $probeText"
    }
    $Script:Receipt.APP_FACTORY_CHECK = "PASS"
    Write-DeployLog "CREATE_APP() + CONFIG VALIDATION PASSED."
}

# =====================================================================
# Phase 9: migration head verification (candidate's own venv, own
# migrations\ tree -- see the Phase 3 note above on why this is not a
# literal manifest-JSON field cross-check).
# =====================================================================

function Test-CandidateMigrationHead {
    param(
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$VenvPython
    )

    Write-DeployLog "Phase 9/16: migration head verification"

    Push-Location $CandidateDir
    try {
        $headCheck = Invoke-Native { & $VenvPython -c "from alembic.config import Config; from alembic.script import ScriptDirectory; c=Config('migrations/alembic.ini'); c.set_main_option('script_location','migrations'); s=ScriptDirectory.from_config(c); h=s.get_heads(); print(len(h)); print(h[0] if h else '')" 2>&1 }
        Assert-NativeSuccess -Phase "MIGRATION_HEAD_FAILED" -CommandDescription "candidate Alembic head check"
        $headLines = $headCheck -split "`r?`n" | Where-Object { $_ -ne "" }
        if ($headLines.Count -lt 2 -or $headLines[0] -ne "1") {
            Invoke-FailClosed -Phase "MIGRATION_HEAD_FAILED" -Reason "Candidate package does not have exactly one Alembic head: $($headLines -join ' / ')"
        }
        $resolvedHead = $headLines[1]
        if ($ExpectedTargetDbRevision -and $resolvedHead -ne $ExpectedTargetDbRevision) {
            Invoke-FailClosed -Phase "MIGRATION_HEAD_FAILED" -Reason "Candidate Alembic head '$resolvedHead' != -ExpectedTargetDbRevision '$ExpectedTargetDbRevision'."
        }
        if ($Script:ExpectedFullManifest) {
            Assert-FullManifestFieldMatches -FieldLabel "migration_head" -Expected $Script:ExpectedFullManifest.migration_head -Actual $resolvedHead
        }
        $Script:Receipt.MIGRATION_HEAD = $resolvedHead
        Write-DeployLog "Candidate Alembic head confirmed: $resolvedHead (single head)."
    } finally {
        Pop-Location
    }
    Write-DeployLog "MIGRATION HEAD VERIFICATION PASSED."
    return $Script:Receipt.MIGRATION_HEAD
}

# =====================================================================
# Phase 10: fresh DB backup (source for the shadow rehearsal)
# =====================================================================

function Backup-SourceDatabase {
    param([Parameter(Mandatory)][hashtable]$DbConn)

    Write-DeployLog "Phase 10/16: PostgreSQL backup (rehearsal source)"

    $backupDir = Join-Path $BackupRoot "candidate_prep_$($Script:DeployId)"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $dumpPath = Join-Path $backupDir "$($DbConn.Database).dump"

    $pgDump = Join-Path $PgBinPath "pg_dump.exe"
    $env:PGPASSWORD = $DbConn.Password
    try {
        Invoke-Native { & $pgDump -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $DbConn.Database -F c -f $dumpPath 2>&1 } | ForEach-Object { Write-DeployLog "pg_dump: $_" }
        Assert-NativeSuccess -Phase "DB_BACKUP_FAILED" -CommandDescription "pg_dump"
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }

    if (-not (Test-Path $dumpPath)) {
        Invoke-FailClosed -Phase "DB_BACKUP_FAILED" -Reason "Dump file was not created: $dumpPath"
    }
    $dumpSize = (Get-Item $dumpPath).Length
    if ($dumpSize -le 0) {
        Invoke-FailClosed -Phase "DB_BACKUP_FAILED" -Reason "Dump file exists but is zero bytes: $dumpPath"
    }

    Write-DeployLog "Backup OK: $dumpPath ($dumpSize bytes)"
    $Script:Receipt.DB_BACKUP_PATH = $dumpPath
    Write-DeployLog "DB BACKUP PASSED."
    return $dumpPath
}

# =====================================================================
# Admin-only shadow DB lifecycle (ported from V4's Invoke-PostgresAdminCommand
# / Test-PostgresAdminAuth / New-ShadowDatabaseAsAdmin / Remove-ShadowDatabaseAsAdmin)
# =====================================================================

function Invoke-PostgresAdminCommand {
    param(
        [Parameter(Mandatory)][string]$AdminUser,
        [Parameter(Mandatory)][System.Security.SecureString]$AdminSecurePassword,
        [Parameter(Mandatory)][string]$HostName,
        [Parameter(Mandatory)][int]$Port,
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][string]$Sql
    )
    $hadPrevious = Test-Path Env:\PGPASSWORD
    $previousValue = if ($hadPrevious) { $env:PGPASSWORD } else { $null }
    $bstr = [IntPtr]::Zero
    try {
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminSecurePassword)
        $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
        $env:PGPASSWORD = $plainPassword
        $plainPassword = $null
        $psql = Join-Path $PgBinPath "psql.exe"
        $output = Invoke-Native { & $psql -h $HostName -p $Port -U $AdminUser -d $Database -t -A -c $Sql 2>&1 }
        return @{ Output = $output; ExitCode = $LASTEXITCODE }
    } finally {
        if ($bstr -ne [IntPtr]::Zero) {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        }
        if ($hadPrevious) {
            $env:PGPASSWORD = $previousValue
        } else {
            Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
        }
    }
}

function Test-PostgresAdminAuth {
    param(
        [Parameter(Mandatory)][string]$AdminUser,
        [Parameter(Mandatory)][System.Security.SecureString]$AdminSecurePassword,
        [Parameter(Mandatory)][hashtable]$DbConn
    )
    Write-DeployLog "Phase 11a: secure PostgreSQL admin authentication + capability check"

    $sql = "SELECT current_user, rolsuper, rolcreatedb FROM pg_roles WHERE rolname = current_user;"
    $result = Invoke-PostgresAdminCommand -AdminUser $AdminUser -AdminSecurePassword $AdminSecurePassword -HostName $DbConn.HostName -Port $DbConn.Port -Database "postgres" -Sql $sql
    if ($result.ExitCode -ne 0) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "PostgreSQL admin authentication/connectivity check failed (exit_code=$($result.ExitCode)). No database was touched."
    }
    $line = ($result.Output | Out-String).Trim()
    $parts = $line -split '\|'
    if ($parts.Count -lt 3) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Admin capability check returned an unexpected result shape."
    }
    $returnedUser = $parts[0].Trim()
    $isSuper = $parts[1].Trim() -eq "t"
    $canCreateDb = $parts[2].Trim() -eq "t"
    if ($returnedUser -ne $AdminUser) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Admin check returned current_user='$returnedUser', expected '$AdminUser'."
    }
    if (-not ($isSuper -or $canCreateDb)) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Admin user '$AdminUser' authenticated but has neither rolsuper nor rolcreatedb."
    }
    Write-DeployLog "Admin auth+capability check PASSED: user=$AdminUser rolsuper=$isSuper rolcreatedb=$canCreateDb"
}

function New-ShadowDatabaseAsAdmin {
    param(
        [Parameter(Mandatory)][string]$ShadowDbName,
        [Parameter(Mandatory)][string]$OwnerUser,
        [Parameter(Mandatory)][string]$AdminUser,
        [Parameter(Mandatory)][System.Security.SecureString]$AdminSecurePassword,
        [Parameter(Mandatory)][hashtable]$DbConn
    )
    Write-DeployLog "Phase 11b: create shadow database (admin-only operation)"
    if (-not (Test-SafePostgresIdentifier -Identifier $ShadowDbName)) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Shadow DB name '$ShadowDbName' failed safe-identifier validation."
    }
    if (-not (Test-SafePostgresIdentifier -Identifier $OwnerUser)) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Application DB user '$OwnerUser' failed safe-identifier validation."
    }
    if ($ShadowDbName -eq $DbConn.Database) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Refusing: shadow DB name '$ShadowDbName' collides with the source database name."
    }
    $sql = "CREATE DATABASE `"$ShadowDbName`" OWNER `"$OwnerUser`";"
    $result = Invoke-PostgresAdminCommand -AdminUser $AdminUser -AdminSecurePassword $AdminSecurePassword -HostName $DbConn.HostName -Port $DbConn.Port -Database "postgres" -Sql $sql
    if ($result.ExitCode -ne 0) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "CREATE DATABASE for shadow DB failed, exit_code=$($result.ExitCode)."
    }
    Write-DeployLog "Shadow database created: $ShadowDbName (owner=$OwnerUser)"
}

function Remove-ShadowDatabaseAsAdmin {
    param(
        [Parameter(Mandatory)][string]$ShadowDbName,
        [Parameter(Mandatory)][string]$AdminUser,
        [Parameter(Mandatory)][System.Security.SecureString]$AdminSecurePassword,
        [Parameter(Mandatory)][hashtable]$DbConn
    )
    Write-DeployLog "Phase 13c: drop shadow database (admin-only operation, always attempted, never skipped)"
    if ($ShadowDbName -eq $DbConn.Database -or -not (Test-SafePostgresIdentifier -Identifier $ShadowDbName)) {
        Write-DeployLog -Level "WARN" "SHADOW_CLEANUP_WARNING db=$ShadowDbName (refused: failed the safety check; should be structurally unreachable)."
        return $false
    }
    try {
        $terminateSql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$ShadowDbName' AND pid <> pg_backend_pid();"
        Invoke-PostgresAdminCommand -AdminUser $AdminUser -AdminSecurePassword $AdminSecurePassword -HostName $DbConn.HostName -Port $DbConn.Port -Database "postgres" -Sql $terminateSql | Out-Null
        $dropSql = "DROP DATABASE IF EXISTS `"$ShadowDbName`";"
        $result = Invoke-PostgresAdminCommand -AdminUser $AdminUser -AdminSecurePassword $AdminSecurePassword -HostName $DbConn.HostName -Port $DbConn.Port -Database "postgres" -Sql $dropSql
        if ($result.ExitCode -ne 0) {
            Write-DeployLog -Level "WARN" "SHADOW_CLEANUP_WARNING db=$ShadowDbName (DROP DATABASE exit_code=$($result.ExitCode))."
            return $false
        }
    } catch {
        Write-DeployLog -Level "WARN" "SHADOW_CLEANUP_WARNING db=$ShadowDbName (unexpected error: $($_.Exception.Message))."
        return $false
    }
    Write-DeployLog "Shadow database dropped: $ShadowDbName"
    return $true
}

function Assert-ShadowDatabaseTarget {
    <# Ported verbatim from V4 -- hard anti-live-DB guard immediately before
       every Alembic invocation against the shadow DB. #>
    param(
        [Parameter(Mandatory)][string]$ExpectedShadowDbName,
        [Parameter(Mandatory)][hashtable]$DbConn
    )
    $currentUrl = $env:DATABASE_URL
    if (-not $currentUrl) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "DATABASE_URL is not set in the runtime environment about to run the shadow migration."
    }
    $parsed = ConvertFrom-DatabaseUrl -Url $currentUrl
    if (-not $parsed) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Runtime DATABASE_URL could not be parsed as a postgresql:// URL."
    }
    Write-DeployLog "Shadow runtime DB target confirmed: host=$($parsed.HostName) port=$($parsed.Port) db=$($parsed.Database) user=$($parsed.User) password=WITHHELD"
    if ($parsed.Database -ne $ExpectedShadowDbName) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Resolved runtime DATABASE_URL targets db='$($parsed.Database)', expected shadow db='$ExpectedShadowDbName'."
    }
    if ($parsed.Database -eq $DbConn.Database) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Resolved runtime DATABASE_URL targets db='$($parsed.Database)', which equals the source database name. REFUSING to run migration."
    }
}

function Restore-ShadowDatabaseAsAppUser {
    <# pg_restore --no-owner --no-privileges, strict exit_code -eq 0 --
       ported from V4 (see its header for the real production bug this
       fixes: a plain restore fails on postgres-owned ALTER ... OWNER TO
       statements when the connecting role isn't postgres). #>
    param(
        [Parameter(Mandatory)][hashtable]$DbConn,
        [Parameter(Mandatory)][string]$ShadowDbName,
        [Parameter(Mandatory)][string]$DumpPath
    )
    Write-DeployLog "Phase 12a: restore backup into shadow database as application user ($($DbConn.User)), --no-owner --no-privileges"

    $psql = Join-Path $PgBinPath "psql.exe"
    $pgRestore = Join-Path $PgBinPath "pg_restore.exe"
    $env:PGPASSWORD = $DbConn.Password
    try {
        Invoke-Native { & $pgRestore -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $ShadowDbName --no-owner --no-privileges $DumpPath 2>&1 } | ForEach-Object { Write-DeployLog "pg_restore: $_" }
        if ($LASTEXITCODE -ne 0) {
            Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "pg_restore --no-owner --no-privileges failed, exit_code=$LASTEXITCODE. Fail-closed: exit_code must be 0."
        }
        $tableCountRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $ShadowDbName -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>&1 }
        Assert-NativeSuccess -Phase "SHADOW_REHEARSAL_FAILED" -CommandDescription "shadow DB restored-table-count query"
        $tableCount = [int](($tableCountRaw | Out-String).Trim())
        if ($tableCount -le 0) {
            Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Shadow database has 0 tables after restore."
        }
        Write-DeployLog "Shadow database restored cleanly (exit_code=0): $tableCount tables present."
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
}

function Test-ShadowSchemaContract {
    <# Coordinator addition (2026-08-25, schema-contract-drift wave):
       verifies the REAL app.bootstrap.schema_contract.get_expected_schema()
       / app.bootstrap.schema_validation.validate_required_schema() contract
       against the freshly-migrated shadow DB -- the exact function the live
       application itself runs at boot when STRICT_SCHEMA_CHECK is on
       (production/staging default). This is deliberately NOT a
       reimplementation: it imports and calls the app's own two functions,
       so it can never silently drift from what create_app() actually
       enforces. Added because a real, independently-verified gap was found
       this wave: c51c29032d4f closes 15 columns across 4 tables that the
       contract required but no earlier migration created -- a database
       built purely via `flask db upgrade` would previously reach head and
       then fail this exact check at boot. This gate makes candidate
       preparation catch that class of drift BEFORE it ever reaches a live
       cutover, for this migration chain and any future one. #>
    param(
        [Parameter(Mandatory)][hashtable]$DbConn,
        [Parameter(Mandatory)][string]$ShadowDbName,
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$VenvPython,
        [Parameter(Mandatory)][hashtable]$ProductionEnvValues
    )
    Write-DeployLog "Phase 12c-1: shadow schema-contract verification (real app.bootstrap.schema_contract / schema_validation)"

    $shadowUrl = "postgresql://$($DbConn.User):$($DbConn.Password)@$($DbConn.HostName):$($DbConn.Port)/$ShadowDbName"
    $overrides = @{
        DATABASE_URL = $shadowUrl
        FLASK_APP = "wsgi.py"
        FLASK_SKIP_SCHEMA_VALIDATION = "1"
        AUTO_REPAIR_SCHEMA = "false"
        REQUIRE_DOTENV_FILE = "false"
        BYS360_FEEDBACK_FOLLOWUP_SCHEDULER = "0"
    }
    $runtimeEnv = @{}
    foreach ($k in $ProductionEnvValues.Keys) { $runtimeEnv[$k] = $ProductionEnvValues[$k] }
    foreach ($k in $overrides.Keys) { $runtimeEnv[$k] = $overrides[$k] }

    $probeLines = @(
        "import sys",
        "sys.path.insert(0, r'$CandidateDir')",
        "from app import create_app",
        "from app.bootstrap.schema_contract import get_expected_schema",
        "from app.bootstrap.schema_validation import validate_required_schema",
        "app = create_app()",
        "with app.app_context():",
        "    validate_required_schema(app, get_expected_schema())",
        "    errors = app.extensions.get('schema_check_errors', [])",
        "    print('SCHEMA_CONTRACT_ERROR_COUNT=%d' % len(errors))",
        "    for e in errors:",
        "        print('SCHEMA_CONTRACT_ERROR: ' + e)"
    )
    $tmpProbe = Join-Path $env:TEMP "bys360_schema_contract_probe_$($Script:DeployId).py"
    Set-Content -Path $tmpProbe -Value $probeLines -Encoding UTF8

    Push-Location $CandidateDir
    try {
        Invoke-WithBys360RuntimeEnvironment -EnvironmentValues $runtimeEnv -ScriptBlock {
            Assert-ShadowDatabaseTarget -ExpectedShadowDbName $ShadowDbName -DbConn $DbConn
            $Script:ContractOutput = Invoke-Native { & $VenvPython $tmpProbe 2>&1 }
            $Script:ContractExit = $LASTEXITCODE
        }
    } finally {
        Pop-Location
        Remove-Item -Path $tmpProbe -ErrorAction SilentlyContinue
    }

    $contractText = ($Script:ContractOutput | Out-String)
    ($contractText).Split("`n") | ForEach-Object { if ($_.Trim()) { Write-DeployLog "schema-contract: $($_.Trim())" } }
    if ($Script:ContractExit -ne 0 -or $contractText -notmatch "SCHEMA_CONTRACT_ERROR_COUNT=0") {
        $Script:Receipt.SCHEMA_CONTRACT_CHECK = "FAIL"
        Invoke-FailClosed -Phase "SCHEMA_CONTRACT_FAILED" -Reason "Candidate migration chain does not satisfy app.bootstrap.schema_contract's expected schema -- see schema-contract log lines above for exact missing table/column names. This means a real STRICT_SCHEMA_CHECK boot in production/staging would fail."
    }
    $Script:Receipt.SCHEMA_CONTRACT_CHECK = "PASS"
    Write-DeployLog "SCHEMA CONTRACT VERIFICATION PASSED (zero missing required tables/columns)."
}

function Invoke-ShadowMigrationAsAppUser {
    <# `flask db upgrade` against the shadow DB, under the application
       user's own credentials, using the CANDIDATE's own venv + injected
       production runtime configuration. Ported/adapted from V4's
       Invoke-ShadowMigrationAsAppUser. #>
    param(
        [Parameter(Mandatory)][hashtable]$DbConn,
        [Parameter(Mandatory)][string]$ShadowDbName,
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$VenvPython,
        [Parameter(Mandatory)][hashtable]$ProductionEnvValues
    )
    Write-DeployLog "Phase 12b: shadow migration as application user ($($DbConn.User))"

    $shadowUrl = "postgresql://$($DbConn.User):$($DbConn.Password)@$($DbConn.HostName):$($DbConn.Port)/$ShadowDbName"
    $overrides = @{
        DATABASE_URL = $shadowUrl
        FLASK_APP = "wsgi.py"
        FLASK_SKIP_SCHEMA_VALIDATION = "1"
        AUTO_REPAIR_SCHEMA = "false"
        REQUIRE_DOTENV_FILE = "false"
        BYS360_FEEDBACK_FOLLOWUP_SCHEDULER = "0"
    }
    $runtimeEnv = @{}
    foreach ($k in $ProductionEnvValues.Keys) { $runtimeEnv[$k] = $ProductionEnvValues[$k] }
    foreach ($k in $overrides.Keys) { $runtimeEnv[$k] = $overrides[$k] }

    Push-Location $CandidateDir
    try {
        Invoke-WithBys360RuntimeEnvironment -EnvironmentValues $runtimeEnv -ScriptBlock {
            Assert-ShadowDatabaseTarget -ExpectedShadowDbName $ShadowDbName -DbConn $DbConn
            $Script:UpgradeOutput = Invoke-Native { & $VenvPython -m flask db upgrade 2>&1 }
            $Script:UpgradeExit = $LASTEXITCODE
        }
    } finally {
        Pop-Location
    }
    ($Script:UpgradeOutput | Out-String).Split("`n") | ForEach-Object { if ($_.Trim()) { Write-DeployLog "flask db upgrade (shadow): $($_.Trim())" } }
    if ($Script:UpgradeExit -ne 0) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "`flask db upgrade` against the SHADOW database failed with exit_code=$($Script:UpgradeExit)."
    }

    Write-DeployLog "Phase 12c: shadow post-migration verification"
    $psql = Join-Path $PgBinPath "psql.exe"
    $env:PGPASSWORD = $DbConn.Password
    try {
        $newRevRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $ShadowDbName -t -A -c "SELECT version_num FROM alembic_version;" 2>&1 }
        Assert-NativeSuccess -Phase "SHADOW_REHEARSAL_FAILED" -CommandDescription "shadow DB post-upgrade alembic_version query"
        $newRev = ($newRevRaw | Out-String).Trim()
        if ($newRev -ne $Script:Receipt.MIGRATION_HEAD) {
            Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Shadow DB revision after upgrade is '$newRev', expected '$($Script:Receipt.MIGRATION_HEAD)'."
        }

        Test-ShadowSchemaContract -DbConn $DbConn -ShadowDbName $ShadowDbName -CandidateDir $CandidateDir -VenvPython $VenvPython -ProductionEnvValues $ProductionEnvValues

        $fcTables = @(
            'file_storage_folders','file_storage_items','file_transfers','file_transfer_items',
            'file_transfer_recipients','file_share_links','file_requests','file_request_uploads',
            'file_download_logs','file_access_logs','file_quota_usage','file_security_scans',
            'file_audit_logs','file_quota_policies','file_upload_sessions','file_upload_chunks',
            'file_center_mail_logs','file_center_role_permissions','file_center_settings'
        )
        $inClause = ($fcTables | ForEach-Object { "'$_'" }) -join ","
        $fcCountRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $ShadowDbName -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ($inClause);" 2>&1 }
        Assert-NativeSuccess -Phase "SHADOW_REHEARSAL_FAILED" -CommandDescription "shadow DB File Center table count query"
        $fcCount = [int](($fcCountRaw | Out-String).Trim())
        $Script:Receipt.FILE_CENTER_TABLES = "$fcCount/19"
        if ($fcCount -ne 19) {
            Write-DeployLog -Level "WARN" "Shadow DB File Center table count = $fcCount/19 (expected 19 only if this candidate's migration chain includes the File Center adoption revision -- informational, not fatal, since not every candidate build necessarily includes it)."
        } else {
            Write-DeployLog "Shadow rehearsal migration: revision=$newRev, File Center tables=$fcCount/19."
        }

        $sanityRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $ShadowDbName -t -A -c "SELECT count(*) FROM users;" 2>&1 }
        if ($LASTEXITCODE -eq 0) {
            Write-DeployLog "Shadow DB 'users' row count after rehearsal (sanity: restored data not destroyed): $((($sanityRaw | Out-String).Trim()))"
        }
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
    $Script:Receipt.SHADOW_REHEARSAL_RESULT = "PASS"
    Write-DeployLog "SHADOW REHEARSAL PASSED."
}

# =====================================================================
# Phase 13: candidate health boot port resolution + collision check
# =====================================================================

function Resolve-CandidateHealthPort {
    Write-DeployLog "Phase 13a: resolve a non-live candidate health-boot port"
    $candidates = @($CandidateHealthPortPreferred) + $CandidateHealthPortFallbacks
    foreach ($port in $candidates) {
        $listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if (-not $listening) {
            Write-DeployLog "Selected candidate health-boot port: $port (confirmed not currently listening)"
            return $port
        }
        Write-DeployLog -Level "WARN" "Port $port is already in use -- trying next candidate."
    }
    Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "All candidate health-boot ports are occupied: $($candidates -join ', '). Refusing to guess a port; fail closed."
}

# =====================================================================
# Phase 13b-13e: launch candidate under Waitress on the resolved port,
# pointed at the SAME shadow DB migrated in Phase 12 (see script header
# design note), real HTTP /healthz check, clean stop.
# =====================================================================

function Start-CandidateHealthBootProcess {
    param(
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$VenvPython,
        [Parameter(Mandatory)][int]$Port,
        [Parameter(Mandatory)][string]$ShadowUrl,
        [Parameter(Mandatory)][hashtable]$ProductionEnvValues,
        [Parameter(Mandatory)][string]$StdOutLogPath,
        [Parameter(Mandatory)][string]$StdErrLogPath
    )
    Write-DeployLog "Phase 13b: start candidate under Waitress on 127.0.0.1:$Port (bound to the shadow DB, never production)"

    $overrides = @{
        DATABASE_URL = $ShadowUrl
        APP_ENV = "production"
        APP_HOST = "127.0.0.1"
        APP_PORT = "$Port"
        FLASK_SKIP_SCHEMA_VALIDATION = "0"   # this IS the real boot-time schema check -- see header design note (read-only unless AUTO_REPAIR_SCHEMA=true, which is forced false below)
        AUTO_REPAIR_SCHEMA = "false"
        REQUIRE_DOTENV_FILE = "false"
        # Defense-in-depth (see header + feedback_followup_scheduler.py):
        # already off by default, forced off anyway so the health-boot
        # process can never start a real background APScheduler job.
        BYS360_FEEDBACK_FOLLOWUP_SCHEDULER = "0"
    }
    $runtimeEnv = @{}
    foreach ($k in $ProductionEnvValues.Keys) { $runtimeEnv[$k] = $ProductionEnvValues[$k] }
    foreach ($k in $overrides.Keys) { $runtimeEnv[$k] = $overrides[$k] }

    # Environment must be set on THIS process before Start-Process, since
    # Start-Process launches a child that inherits the current process
    # environment block at launch time.
    $priorState = @{}
    foreach ($key in $runtimeEnv.Keys) {
        $hadValue = Test-Path "Env:\$key"
        $priorState[$key] = @{ HadValue = $hadValue; Value = if ($hadValue) { (Get-Item "Env:\$key").Value } else { $null } }
        Set-Item -Path "Env:\$key" -Value $runtimeEnv[$key]
    }
    try {
        $proc = Start-Process -FilePath $VenvPython -ArgumentList @("run_server.py") -WorkingDirectory $CandidateDir `
            -RedirectStandardOutput $StdOutLogPath -RedirectStandardError $StdErrLogPath -PassThru -WindowStyle Hidden
    } finally {
        foreach ($key in $priorState.Keys) {
            if ($priorState[$key].HadValue) {
                Set-Item -Path "Env:\$key" -Value $priorState[$key].Value
            } else {
                Remove-Item -Path "Env:\$key" -ErrorAction SilentlyContinue
            }
        }
    }
    return $proc
}

function Wait-CandidatePortListening {
    <# NOTE (found via direct testing, not guessed): filtering
       Get-NetTCPConnection by `-OwningProcess $Process.Id` is unreliable
       here -- confirmed directly that Start-Process's returned PID for the
       venv's python.exe on this host does NOT always match the PID that
       actually ends up owning the bound listening socket (observed
       directly: Start-Process reported one PID, Get-NetTCPConnection's
       OwningProcess for the real listener was a different PID entirely --
       a platform/interpreter-resolution quirk, not a script bug). V4's own
       Start-LiveService (see deploy_bys360_ec4e56b_production_v4.ps1) never
       filters by OwningProcess for this exact reason -- it only checks
       whether ANYTHING is listening on the target port. This function
       matches that same, already-relied-upon pattern: Resolve-CandidateHealthPort
       already confirmed nothing was listening on this port moments before
       this process was started, so a listener appearing now, in this
       narrow window, is not filtered further by PID. #>
    param([Parameter(Mandatory)][int]$Port, [Parameter(Mandatory)][System.Diagnostics.Process]$Process, [int]$TimeoutSeconds = 40)
    $started = $false
    for ($i = 0; $i -lt $TimeoutSeconds; $i++) {
        if ($Process.HasExited) {
            Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "Candidate process exited early (exit_code=$($Process.ExitCode)) before binding port $Port."
        }
        $listening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($listening) { $started = $true; break }
        Start-Sleep -Seconds 1
    }
    if (-not $started) {
        Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "Candidate process did not bind port $Port within $TimeoutSeconds seconds."
    }
    Write-DeployLog "Candidate process confirmed listening on 127.0.0.1:$Port (launcher pid=$($Process.Id); the actual listening process may report a different pid on this platform -- see function comment)."
}

function Test-CandidateHealthEndpoint {
    <# Real HTTP GET to /healthz. app\routes.py:72 registers
       `@main_bp.get("/healthz")` returning {"status":"ok",...} 200 -- the
       exact route confirmed by reading app\routes.py directly, not
       assumed.

       NOTE (found via direct testing, matching a pattern already proven in
       V4's Test-LocalHealth): a plain request to http://127.0.0.1:<port>/healthz
       with no Host header returns HTTP 400, NOT because the app or this
       script is broken, but because config.py resolves TRUSTED_HOSTS from
       the real APP_BASE_URL, and Werkzeug/Flask's host-header validation
       rejects a request whose Host does not match any trusted host.
       Confirmed directly this wave: the exact same plain-localhost request
       400s.

       SECOND finding, also confirmed directly this wave: Invoke-WebRequest's
       `-Headers @{"Host"=...}` does NOT actually change the wire-level Host
       header under Windows PowerShell 5.1 -- .NET's HttpWebRequest treats
       Host as a restricted header with its own dedicated property, and
       silently ignores a same-named entry passed through the generic
       Headers collection (confirmed: the request still 400s with "Host
       '127.0.0.1:<port>' is not trusted" even when -Headers @{"Host"=...}
       is supplied). This is exactly why V4's own Test-LocalHealth uses
       curl.exe instead of Invoke-WebRequest for this specific check --
       curl.exe, as a separate native process, has no such restriction and
       genuinely overrides the Host header on the wire. This function
       follows that same, already-proven pattern. #>
    param([Parameter(Mandatory)][int]$Port, [string]$ExpectedHostHeader)
    Write-DeployLog "Phase 13d: real HTTP GET http://127.0.0.1:$Port/healthz"

    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) {
        Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "curl.exe not found on PATH -- required for a Host-header-correct health check (plain Invoke-WebRequest would 400 on Trusted Host and must not be misreported as an app failure)."
    }
    try {
        if ($ExpectedHostHeader) {
            $code = (Invoke-Native {
                & curl.exe -s -o NUL -w "%{http_code}" --max-time 15 -H "Host: $ExpectedHostHeader" -H "X-Forwarded-Proto: https" "http://127.0.0.1:$Port/healthz" 2>&1
            } | Out-String).Trim()
        } else {
            $code = (Invoke-Native {
                & curl.exe -s -o NUL -w "%{http_code}" --max-time 15 "http://127.0.0.1:$Port/healthz" 2>&1
            } | Out-String).Trim()
        }
    } catch {
        $Script:Receipt.HEALTH_CHECK_RESULT = "REQUEST_ERROR"
        Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "HTTP request to /healthz failed: $($_.Exception.Message)"
    }
    if ($code -ne "200") {
        $Script:Receipt.HEALTH_CHECK_RESULT = "$code"
        Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "/healthz returned HTTP $code, expected 200."
    }
    $Script:Receipt.HEALTH_CHECK_RESULT = "200"
    Write-DeployLog "CANDIDATE HEALTH CHECK PASSED (HTTP 200)."
}

function Stop-CandidateHealthBootProcess {
    param([Parameter(Mandatory)][System.Diagnostics.Process]$Process, [Parameter(Mandatory)][int]$Port)
    Write-DeployLog "Phase 13e: stop candidate test process cleanly"
    if (-not $Process.HasExited) {
        try {
            Stop-Process -Id $Process.Id -Force -ErrorAction Stop
        } catch {
            Write-DeployLog -Level "WARN" "Stop-Process reported an error (process may have already exited): $($_.Exception.Message)"
        }
    }
    Start-Sleep -Seconds 1
    $stillListening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($stillListening) {
        Write-DeployLog -Level "WARN" "Port $Port still shows a listener after Stop-Process -- possible orphan (pid(s): $($stillListening.OwningProcess -join ',')). Investigate manually."
    } else {
        Write-DeployLog "Confirmed: nothing listening on port $Port after candidate process stop -- no orphaned process left."
    }
}

# =====================================================================
# Orchestrator: Phases 10-13 combined, so the shadow database created for
# the migration rehearsal can be reused for the health boot, and dropped
# EXACTLY ONCE at the very end in a `finally` that spans both -- this is
# the "drop shadow DB in a finally (never skipped even on failure)"
# requirement, extended to cover the health boot as well.
# =====================================================================

function Invoke-ShadowRehearsalAndHealthBoot {
    param(
        [Parameter(Mandatory)][hashtable]$DbConn,
        [Parameter(Mandatory)][string]$DumpPath,
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$VenvPython,
        [Parameter(Mandatory)][hashtable]$ProductionEnvValues
    )

    $shadowDbName = "bys360_shadow_prep_$($Script:DeployId)"
    if ($shadowDbName -eq $DbConn.Database) {
        Invoke-FailClosed -Phase "SHADOW_REHEARSAL_FAILED" -Reason "Computed shadow DB name collided with the source database name."
    }

    Write-Host ""
    Write-Host "PostgreSQL admin credential needed for the disposable shadow database (CREATE/DROP only -- $($DbConn.User) is never granted CREATEDB)."
    $adminSecurePassword = Read-Host -Prompt "PostgreSQL admin password for user '$PostgresAdminUser'" -AsSecureString

    $shadowCreated = $false
    $healthProcess = $null
    $healthPort = $null
    try {
        Test-PostgresAdminAuth -AdminUser $PostgresAdminUser -AdminSecurePassword $adminSecurePassword -DbConn $DbConn
        New-ShadowDatabaseAsAdmin -ShadowDbName $shadowDbName -OwnerUser $DbConn.User -AdminUser $PostgresAdminUser -AdminSecurePassword $adminSecurePassword -DbConn $DbConn
        $shadowCreated = $true

        Restore-ShadowDatabaseAsAppUser -DbConn $DbConn -ShadowDbName $shadowDbName -DumpPath $DumpPath
        Invoke-ShadowMigrationAsAppUser -DbConn $DbConn -ShadowDbName $shadowDbName -CandidateDir $CandidateDir -VenvPython $VenvPython -ProductionEnvValues $ProductionEnvValues

        $healthPort = Resolve-CandidateHealthPort
        $Script:Receipt.HEALTH_BOOT_PORT = "$healthPort"
        $shadowUrl = "postgresql://$($DbConn.User):$($DbConn.Password)@$($DbConn.HostName):$($DbConn.Port)/$shadowDbName"
        $stdOutLog = Join-Path $Script:DeployLogDir "candidate_health_boot.stdout.log"
        $stdErrLog = Join-Path $Script:DeployLogDir "candidate_health_boot.stderr.log"
        $healthProcess = Start-CandidateHealthBootProcess -CandidateDir $CandidateDir -VenvPython $VenvPython -Port $healthPort -ShadowUrl $shadowUrl -ProductionEnvValues $ProductionEnvValues -StdOutLogPath $stdOutLog -StdErrLogPath $stdErrLog
        Wait-CandidatePortListening -Port $healthPort -Process $healthProcess
        Start-Sleep -Seconds 2

        $expectedHostHeader = $null
        if ($ProductionEnvValues.ContainsKey('APP_BASE_URL') -and $ProductionEnvValues['APP_BASE_URL']) {
            try { $expectedHostHeader = ([uri]$ProductionEnvValues['APP_BASE_URL']).Host } catch { $expectedHostHeader = $null }
        }
        Test-CandidateHealthEndpoint -Port $healthPort -ExpectedHostHeader $expectedHostHeader

        $bootLogText = ""
        foreach ($p in @($stdOutLog, $stdErrLog)) {
            if (Test-Path $p) { $bootLogText += (Get-Content -Path $p -Raw -Encoding UTF8) }
        }
        $errorHits = Test-LogForRealErrors -LogText $bootLogText
        if ($errorHits.Count -gt 0) {
            Invoke-FailClosed -Phase "HEALTH_BOOT_FAILED" -Reason "Candidate health-boot log contains error-like patterns: $($errorHits -join '; ')"
        }
        Write-DeployLog "Candidate health-boot log clean (no error/critical patterns)."
    } finally {
        if ($healthProcess) {
            Stop-CandidateHealthBootProcess -Process $healthProcess -Port $healthPort
        }
        if ($shadowCreated) {
            $cleanupOk = Remove-ShadowDatabaseAsAdmin -ShadowDbName $shadowDbName -AdminUser $PostgresAdminUser -AdminSecurePassword $adminSecurePassword -DbConn $DbConn
            if (-not $cleanupOk) {
                Write-DeployLog -Level "WARN" "Shadow cleanup did not fully succeed -- see SHADOW_CLEANUP_WARNING above. The shadow DB is disposable; this does not affect any live system."
            }
        }
        $adminSecurePassword = $null
    }
}

# =====================================================================
# Phase 14: CANDIDATE_READY.json receipt
# =====================================================================

function Write-CandidateReadyReceipt {
    param([Parameter(Mandatory)][string]$CandidateDir)

    Write-DeployLog "Phase 14/16: write CANDIDATE_READY.json"

    $Script:Receipt.GENERATED_AT = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
    $Script:Receipt.CANDIDATE_READY = "YES"

    $receiptJson = $Script:Receipt | ConvertTo-Json -Depth 6
    $receiptPathInCandidate = Join-Path $CandidateDir "CANDIDATE_READY.json"
    $receiptPathInLogDir = Join-Path $Script:DeployLogDir "CANDIDATE_READY.json"
    Set-Content -Path $receiptPathInCandidate -Value $receiptJson -Encoding UTF8
    Set-Content -Path $receiptPathInLogDir -Value $receiptJson -Encoding UTF8

    Write-DeployLog "CANDIDATE_READY.json written: $receiptPathInCandidate"
    Write-DeployLog "(and archived at: $receiptPathInLogDir)"
    return $receiptPathInCandidate
}

# =====================================================================
# MAIN
# =====================================================================

function Main {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"

    New-Item -ItemType Directory -Force -Path $Script:DeployLogDir | Out-Null
    $Script:LogFile = Join-Path $Script:DeployLogDir "candidate_prep.log"
    Write-DeployLog "================================================================"
    Write-DeployLog "BYS360 CANDIDATE PREPARATION -- START (DeployId=$($Script:DeployId))"
    Write-DeployLog "================================================================"
    Write-DeployLog "Resolved (non-secret) configuration:"
    Write-DeployLog "  PackagePath                  = $PackagePath"
    Write-DeployLog "  ExpectedPackageSha256          = $ExpectedPackageSha256"
    Write-DeployLog "  ExpectedHostName                 = $ExpectedHostName"
    Write-DeployLog "  CandidateRoot                      = $CandidateRoot"
    Write-DeployLog "  ProductionDbName                     = $ProductionDbName"
    Write-DeployLog "  PostgresAdminUser                      = $PostgresAdminUser (password prompted interactively, never a parameter)"
    Write-DeployLog "  AllowNetworkInstallFallback               = $($AllowNetworkInstallFallback.IsPresent) (MUST be false in production)"
    Write-DeployLog "(DATABASE_URL / passwords / secret keys are never printed or logged.)"

    Test-HostPrerequisites
    Test-PackageHash
    $sourceSha = Test-PackageManifest

    $basePython312 = Resolve-Bys360BasePython312

    $candidateDir = Expand-CandidatePackage -SourceSha $sourceSha
    $sourceSha = Test-EmbeddedSourceSha -CandidateDir $candidateDir
    Test-CandidateExtractedSecretScan -CandidateDir $candidateDir -BasePython312 $basePython312
    $venvPython = New-CandidateVirtualEnv -CandidateDir $candidateDir -BasePython312 $basePython312

    Test-CandidatePipCheck -VenvPython $venvPython
    Test-CandidateImportGates -VenvPython $venvPython

    if (-not $ProductionEnvFilePath) { $ProductionEnvFilePath = Join-Path $ProjectRoot ".env" }
    $productionEnvValues = Get-Bys360ProductionEnvValues -VenvPython $venvPython -EnvFilePath $ProductionEnvFilePath

    Test-CandidateAppFactory -CandidateDir $candidateDir -VenvPython $venvPython -ProductionEnvValues $productionEnvValues
    Test-CandidateMigrationHead -CandidateDir $candidateDir -VenvPython $venvPython | Out-Null

    $dbConn = Get-ProductionDbConnection -EnvPath $ProductionEnvFilePath
    if ($dbConn.Database -ne $ProductionDbName) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "-ProductionDbName '$ProductionDbName' does not match the database name parsed from DATABASE_URL ('$($dbConn.Database)')."
    }
    $dumpPath = Backup-SourceDatabase -DbConn $dbConn

    Invoke-ShadowRehearsalAndHealthBoot -DbConn $dbConn -DumpPath $dumpPath -CandidateDir $candidateDir -VenvPython $venvPython -ProductionEnvValues $productionEnvValues

    $receiptPath = Write-CandidateReadyReceipt -CandidateDir $candidateDir

    Write-DeployLog "================================================================"
    Write-DeployLog "CANDIDATE PREPARATION SUCCEEDED. Receipt: $receiptPath"
    Write-DeployLog "SOURCE_SHA=$($Script:Receipt.SOURCE_SHA) CANDIDATE_DIR=$candidateDir MIGRATION_HEAD=$($Script:Receipt.MIGRATION_HEAD)"
    Write-DeployLog "The live application, live database, and live Scheduled Task were NEVER touched."
    Write-DeployLog "================================================================"
}

# BYS360 DEFECT AH (testability, zero behavioral change to real invocation):
# same dot-source guard already established in cutover_bys360_candidate.ps1
# (see its own comment above this identical check). $MyInvocation.
# InvocationName is '.' only when this script is DOT-SOURCED, never when
# run directly (-File or &) -- the only way this script is ever actually
# invoked for a real candidate preparation. Dot-sourcing loads every
# function definition above (Test-EmbeddedSourceSha, Test-PackageManifest,
# etc.) without running Main() or calling `exit`, so a test harness can
# call these pure, parameterized functions in isolation.
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Main
        exit 0
    } catch {
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
}
