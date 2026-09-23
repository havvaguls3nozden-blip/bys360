<#
BYS360 Candidate Cutover Script V1
====================================

WHAT THIS DOES
  Promotes an already-prepared, already-proven candidate application tree
  (built and verified end-to-end by prepare_bys360_candidate.ps1, which
  writes CANDIDATE_READY.json) to become the new live C:\bys360\project, and
  runs the LIVE database migration for real. This script is intentionally
  short and auditable: it does NOT build a venv, does NOT install
  dependencies, does NOT run a shadow-DB rehearsal, and does NOT resolve
  Python/PostgreSQL prerequisites from scratch -- all of that already
  happened in prepare_bys360_candidate.ps1 and is proven by the receipt this
  script verifies before doing anything else.

HARD GATE (read before anything else)
  This script REFUSES TO RUN -- fail-closed, before touching the live
  service, the live application tree, or the live database in any way --
  unless C:\bys360\candidate\<CandidateSourceSha>\CANDIDATE_READY.json
  exists and its bound values (source SHA, candidate directory, dependency
  lock hash, migration head, and every prior gate result) are recomputed
  and cross-checked against the actual on-disk candidate tree. See
  Assert-ValidCandidateReceipt. A receipt that merely exists but doesn't
  bind to the real files (tampered/stale/copied-from-elsewhere) is rejected
  exactly like a missing one.

WHAT THIS SCRIPT NEVER DOES
  - Never re-builds or re-installs the candidate's venv/dependencies.
  - Never re-runs a shadow-database rehearsal or dependency resolution.
  - Never attempts an automatic rollback on failure (see
    rollback_bys360_candidate.ps1 for that, which itself never runs an
    automatic Alembic downgrade either -- see its header).
  - Never deletes the previous application tree -- it is always MOVED to
    C:\bys360\previous\<timestamp>_<PreviousSourceSha>\, never removed.

SAFETY NET FOR THE TWO-STEP PROMOTION (read before assuming this is
perfectly atomic)
  NTFS same-volume Move-Item (rename) is fast and near-atomic for a SINGLE
  move, but promoting a candidate is structurally two moves: (a) the
  current C:\bys360\project -> C:\bys360\previous\<ts>\, then (b) the
  candidate directory -> C:\bys360\project. If (a) succeeds and (b) then
  fails, C:\bys360\project would not exist at all. Move-ApplicationTreeIntoPlace
  detects exactly this scenario and, as a best-effort safety net, moves the
  previous tree BACK into place before writing the failure receipt --
  restoring the pre-cutover state on disk (the Scheduled Task itself is
  left stopped either way; restarting it is always a separate, explicit,
  later action, whether via a fixed cutover re-run or
  rollback_bys360_candidate.ps1).

FAILURE POLICY AFTER THE LIVE MIGRATION STARTS (matches V4's policy, not
reinvented)
  If `flask db upgrade` against the LIVE database fails, this script does
  NOT attempt an automatic downgrade and does NOT start the Scheduled Task.
  The pre-cutover backup taken in this same run is preserved and its path
  is in both the failure receipt and the console log. A human operator (or
  rollback_bys360_candidate.ps1, for the app-tree-only path) must then
  decide the next step -- this script does not decide it for them.

FAILURE PHASES (recorded verbatim in the failure receipt's "Phase" field)
  RECEIPT_INVALID, PRECHECK_FAILED, DB_BACKUP_FAILED, STATE_PRESERVE_FAILED,
  SERVICE_STOP_FAILED, PROMOTION_FAILED, LIVE_MIGRATION_FAILED,
  SERVICE_START_FAILED, LOCAL_HEALTH_FAILED, RELEASE_IDENTITY_FAILED,
  READINESS_FAILED, PUBLIC_HEALTH_FAILED, SMOKE_FAILED,
  POST_DEPLOY_SECURITY_FAILED

DEFECT Z -- STALE/WRONG-PROCESS REJECTION (read before assuming "port is
listening and /healthz is 200" ever meant "the right process is up")
  Before this fix, SERVICE_STOP (Phase 7/8) only WARNED if something was
  still listening on $AppPort after Stop-ScheduledTask, and SERVICE_START
  (Phase 15) accepted ANY process listening on $AppPort as success -- with
  no PID/path/freshness check and no comparison of the release identity the
  responding process actually reports against the candidate this run
  intended to promote. A stale/orphaned process left over from before
  cutover (or, in principle, an unrelated process that happened to be
  listening) could therefore be silently accepted as "the new candidate is
  live." This is now closed by THREE independent, fail-closed bindings, all
  required together:
    1. PROCESS BINDING (Test-ProcessBinding, used by both Stop-LiveService
       -- which now fails closed instead of warning if anything is still
       listening after stop -- and Start-LiveService): the PID owning
       $AppPort must resolve (via Win32_Process) to the EXACT expected
       venv python.exe path under the just-promoted $ProjectRoot, its
       command line must reference run_server.py, and its process start
       time must be AFTER this run's own Start-ScheduledTask invocation --
       proving it is a genuinely fresh process this run started, not a
       leftover.
    2. RELEASE IDENTITY BINDING (Test-ReleaseIdentityBinding, new Phase
       16a/20): calls the now-extended GET /versionz (see
       app/routes.py::_bys360_release_identity -- the ONE minimal,
       justified app-source change this defect required, because every
       promoted release lives at the identical fixed path, so process/PID
       metadata alone can never prove WHICH release's code is loaded) and
       requires its source_sha/migration_head to exactly match the
       candidate this run intended to promote.
    3. READINESS GATE (Test-ReadinessGate, new Phase 16b/20): calls GET
       /readyz and requires both HTTP 200 and body status=="ready" --
       previously never called by this script at all.
  Any of the three failing prevents SUCCESS (Invoke-FailClosed), exactly
  like every other phase in this script; rollback via
  rollback_bys360_candidate.ps1 remains unaffected and still bound to the
  previous release the normal way (PREVIOUS_DIR in the receipt).
#>

[CmdletBinding()]
param(
    # ---- Which candidate to cut over ------------------------------------
    [Parameter(Mandatory = $true)][string]$CandidateSourceSha,
    [string]$ExpectedPackageSha256,   # optional extra cross-check; see Assert-ValidCandidateReceipt

    # ---- Server / host identity -----------------------------------------
    [string]$ExpectedHostName = "CATAB-BYS360",

    # ---- Filesystem roots -------------------------------------------------
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$CandidateRoot = "C:\bys360\candidate",
    [string]$PreviousRoot = "C:\bys360\previous",
    [string]$StorageRoot = "C:\bys360\storage",
    [string]$LocalStorageRoot = "C:\bys360\local_storage",
    [string]$BackupRoot = "C:\bys360\backups",
    [string]$DeployLogsRoot = "C:\bys360\deploy_logs",
    [string]$LogPath = "C:\bys360\logs\bys360_live_waitress_80.log",

    # ---- PostgreSQL ---------------------------------------------------------
    [string]$PgBinPath = "C:\Program Files\PostgreSQL\15\bin",
    [string]$ProductionDbName,
    [string]$EnvFilePath,   # defaults to "$ProjectRoot\.env" (the CURRENT live tree's .env, before it moves)

    # ---- Scheduled Task -------------------------------------------------------
    [string]$TaskName = "BYS360 Live Waitress 80",
    [int]$AppPort = 80,
    [string]$PublicHostName = "bys360.canakkaletarihialan.gov.tr",

    # ---- Behavior toggles -----------------------------------------------------
    [switch]$SkipPublicHealthCheck,       # same narrow precedent as V4 -- see its header
    [switch]$AllowDbRevisionMismatch,     # explicit opt-in for a recovery/rerun scenario
    [switch]$AllowSameSourceSha,          # explicit opt-in: candidate SHA equals current live SHA (recovery/rerun)
    [switch]$SkipFileCenterTableCheck     # only for a future release whose migration chain does not touch File Center
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =====================================================================
# Global state / logging / receipt helpers (same pattern as
# prepare_bys360_candidate.ps1 / V4 -- duplicated here deliberately so this
# script remains fully self-contained and independently runnable/auditable
# by an operator, matching this project's existing house convention of not
# dot-sourcing shared files between deploy scripts).
# =====================================================================

$Script:DeployId = Get-Date -Format "yyyyMMdd_HHmmss"
$Script:DeployLogDir = Join-Path $DeployLogsRoot "cutover_$($Script:DeployId)"
$Script:LogFile = $null
$Script:Receipt = [ordered]@{
    CANDIDATE_SOURCE_SHA     = $CandidateSourceSha
    PREVIOUS_SOURCE_SHA      = ""
    PREVIOUS_DIR             = ""
    DB_BACKUP_PATH           = ""
    DB_REVISION_BEFORE       = ""
    DB_REVISION_AFTER        = ""
    MIGRATION_RESULT         = ""
    FILE_CENTER_TABLES       = ""
    SCHEMA_CONTRACT_CHECK    = ""
    SERVICE_RESULT           = ""
    PROCESS_BINDING          = ""
    LOCAL_HEALTH             = ""
    RELEASE_IDENTITY         = ""
    READINESS                = ""
    PUBLIC_HEALTH            = ""
    SMOKE                    = ""
    SECURITY_CRITICAL        = ""
    DEPLOY_EXIT_CODE         = ""
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
        "BYS360 CANDIDATE CUTOVER -- FAILURE RECEIPT"
        "================================================================"
        "Phase          : $Phase"
        "Timestamp      : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        "Reason         : $Reason"
        "Log path       : $($Script:LogFile)"
        "Deploy log dir : $($Script:DeployLogDir)"
        ""
        "DB backup (if taken this run) : $($Script:Receipt.DB_BACKUP_PATH)"
        "Previous app tree (if moved)  : $($Script:Receipt.PREVIOUS_DIR)"
        ""
        "No automatic rollback was attempted. The live application/database"
        "state as of this failure must be assessed manually -- see"
        "rollback_bys360_candidate.ps1 for the app-tree-only rollback path,"
        "and its header for why an automatic Alembic downgrade is never run."
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
    <# Ported/adapted from V4's Assert-SafeDeletionTarget -- used here for
       BOTH move-out-of-place and move-into-place targets, since a
       mis-resolved path is just as dangerous for Move-Item as for
       Remove-Item. #>
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

# =====================================================================
# PostgreSQL DATABASE_URL parsing -- ported verbatim from V4 / prepare.
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
    Write-DeployLog "Resolved production DB connection: host=$($parsed.HostName) port=$($parsed.Port) db=$($parsed.Database) user=$($parsed.User) (password withheld)"
    return $parsed
}

function Test-LogForRealErrors {
    <# NOTE (found via direct testing, not guessed): a plain
       [Parameter(Mandatory)][string]$LogText rejects an EMPTY string, not
       only $null ("Cannot bind argument to parameter 'LogText' because it
       is an empty string") -- confirmed directly when a freshly-started
       process had produced zero bytes of new log output yet.
       [AllowEmptyString()] fixes this; an empty string still correctly
       matches zero patterns. #>
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
    return ,$hits
}

function Get-ListeningProcessOnPort {
    <# BYS360 DEFECT Z: resolves the PID owning $Port (if any) to its real
       executable path / command line / start time via Win32_Process --
       Get-NetTCPConnection alone only proves "something is listening",
       never WHICH process or whether it is fresh. #>
    param([Parameter(Mandatory)][int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $conn) { return $null }
    $ownerPid = $conn.OwningProcess
    $proc = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId=$ownerPid" -ErrorAction SilentlyContinue
    if (-not $proc) {
        return [PSCustomObject]@{ Pid = $ownerPid; ExecutablePath = $null; CommandLine = $null; CreationDate = $null }
    }
    return [PSCustomObject]@{
        Pid            = $ownerPid
        ExecutablePath = $proc.ExecutablePath
        CommandLine    = $proc.CommandLine
        CreationDate   = $proc.CreationDate
    }
}

function Get-CandidateVenvBaseExecutable {
    <# BYS360 DEFECT Z HOTFIX: Windows venv redirector semantics mean the
       OS-observed Win32_Process.ExecutablePath for a process launched via
       <venv>\Scripts\python.exe is the BASE interpreter that venv was
       created from, not the venv's own launcher path -- confirmed directly
       against a real production cutover failure (EXECUTABLE_PATH_MISMATCH:
       Win32_Process reported the base Python312 install under
       C:\Users\Administrator\...\Python312\python.exe; sys.executable
       inside the running app correctly showed the venv's own
       .venv\Scripts\python.exe; sys._base_executable matched the
       Win32_Process value exactly). Reads the candidate venv's own
       pyvenv.cfg 'executable' entry -- written once by Python's own venv
       module at venv-creation time, the same source CPython itself uses to
       resolve sys._base_executable -- as the ONLY additional trusted path.
       Never a PATH search, never any other Program Files/AppData
       python.exe: this is deterministically scoped to THIS SPECIFIC
       candidate's own venv metadata, shipped as part of the candidate
       itself. Returns $null (not a guess) if pyvenv.cfg is missing or has
       no readable 'executable = ' line -- the caller must fail closed on
       $null, never silently fall back to trusting only the venv launcher
       path when this signal is unavailable. #>
    param([Parameter(Mandatory)][string]$VenvRoot)
    $cfgPath = Join-Path $VenvRoot "pyvenv.cfg"
    if (-not (Test-Path -LiteralPath $cfgPath)) { return $null }
    $match = Get-Content -LiteralPath $cfgPath -ErrorAction SilentlyContinue |
        Select-String -Pattern '^\s*executable\s*=\s*(.+?)\s*$' |
        Select-Object -First 1
    if (-not $match) { return $null }
    return $match.Matches[0].Groups[1].Value
}

function Test-ProcessBinding {
    <# BYS360 DEFECT Z: proves the process currently listening on $Port is
       (a) our own venv python.exe under the just-promoted $ProjectRoot,
       (b) running run_server.py, and (c) genuinely fresh -- started AFTER
       $NotBeforeUtc (this run's own Start-ScheduledTask invocation, or the
       Stop-LiveService check timestamp) -- not a stale/leftover process
       from before cutover. Does NOT and cannot prove WHICH release's code
       is loaded (every promoted version shares the identical path); that
       is Test-ReleaseIdentityBinding's job.

       BYS360 DEFECT Z HOTFIX: -ExpectedExecutablePath accepts one or more
       candidate paths (Windows venv redirector semantics mean the genuine
       process may legitimately show either the venv's own launcher path
       or that venv's own recorded base interpreter -- see
       Get-CandidateVenvBaseExecutable -- never a generic python.exe
       allowlist or PATH-based search). A single string still binds
       correctly here (PowerShell wraps a scalar into a one-element
       [string[]] automatically), so this widening is source-compatible
       with every pre-existing caller. #>
    param(
        [Parameter(Mandatory)][int]$Port,
        [Parameter(Mandatory)][string[]]$ExpectedExecutablePath,
        [Parameter(Mandatory)][string]$ExpectedCommandLineFragment,
        [datetime]$NotBeforeUtc
    )
    $binding = Get-ListeningProcessOnPort -Port $Port
    if (-not $binding) {
        return [PSCustomObject]@{ Ok = $false; Reason = "NO_LISTENER"; Binding = $null }
    }
    if (-not $binding.ExecutablePath) {
        return [PSCustomObject]@{ Ok = $false; Reason = "EXECUTABLE_PATH_UNRESOLVED"; Binding = $binding }
    }
    $expectedExeFullSet = $ExpectedExecutablePath | Where-Object { $_ } | ForEach-Object { [System.IO.Path]::GetFullPath($_) }
    $actualExeFull = [System.IO.Path]::GetFullPath($binding.ExecutablePath)
    if ($expectedExeFullSet -notcontains $actualExeFull) {
        return [PSCustomObject]@{ Ok = $false; Reason = "EXECUTABLE_PATH_MISMATCH"; Binding = $binding }
    }
    if (-not $binding.CommandLine -or ($binding.CommandLine -notlike "*$ExpectedCommandLineFragment*")) {
        return [PSCustomObject]@{ Ok = $false; Reason = "COMMAND_LINE_MISMATCH"; Binding = $binding }
    }
    if ($NotBeforeUtc -and $binding.CreationDate) {
        $creationUtc = ([datetime]$binding.CreationDate).ToUniversalTime()
        if ($creationUtc -lt $NotBeforeUtc.AddSeconds(-2)) {
            return [PSCustomObject]@{ Ok = $false; Reason = "STALE_PROCESS_PREDATES_START"; Binding = $binding }
        }
    }
    return [PSCustomObject]@{ Ok = $true; Reason = "OK"; Binding = $binding }
}

function Test-ReleaseIdentityBinding {
    <# BYS360 DEFECT Z: calls the now-extended GET /versionz (see
       app/routes.py::_bys360_release_identity) and requires its
       source_sha/migration_head to exactly match the candidate this run
       intended to promote. Reuses the exact same curl.exe + Host-header
       pattern as Test-LocalHealth (Invoke-WebRequest's -Headers @{"Host"=}
       does not actually change the wire-level Host header under Windows
       PowerShell 5.1 -- see that function's own note). #>
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$HostHeader,
        [Parameter(Mandatory)][string]$ExpectedSourceSha,
        [Parameter(Mandatory)][string]$ExpectedMigrationHead,
        [int]$TimeoutSec = 15
    )
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) {
        return [PSCustomObject]@{ Ok = $false; Reason = "CURL_NOT_FOUND"; Body = $null }
    }
    $bodyText = (Invoke-Native { & curl.exe -s --max-time $TimeoutSec -H "Host: $HostHeader" -H "X-Forwarded-Proto: https" "$BaseUrl/versionz" 2>&1 } | Out-String)
    try {
        $parsed = $bodyText | ConvertFrom-Json
    } catch {
        return [PSCustomObject]@{ Ok = $false; Reason = "INVALID_JSON"; Body = $bodyText }
    }
    if ([string]$parsed.source_sha -ne $ExpectedSourceSha) {
        return [PSCustomObject]@{ Ok = $false; Reason = "SOURCE_SHA_MISMATCH"; Body = $parsed }
    }
    if ([string]$parsed.migration_head -ne $ExpectedMigrationHead) {
        return [PSCustomObject]@{ Ok = $false; Reason = "MIGRATION_HEAD_MISMATCH"; Body = $parsed }
    }
    return [PSCustomObject]@{ Ok = $true; Reason = "OK"; Body = $parsed }
}

function Test-ReadinessGate {
    <# BYS360 DEFECT Z: calls GET /readyz and requires BOTH HTTP 200 AND
       body status=="ready" -- previously never called anywhere in this
       script. A readiness failure must block SUCCESS, not merely be
       observed. #>
    param(
        [Parameter(Mandatory)][string]$BaseUrl,
        [Parameter(Mandatory)][string]$HostHeader,
        [int]$TimeoutSec = 15
    )
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) {
        return [PSCustomObject]@{ Ok = $false; Reason = "CURL_NOT_FOUND"; StatusCode = $null; Body = $null }
    }
    $raw = (Invoke-Native { & curl.exe -s --max-time $TimeoutSec -w "`n___HTTP_CODE___%{http_code}" -H "Host: $HostHeader" -H "X-Forwarded-Proto: https" "$BaseUrl/readyz" 2>&1 } | Out-String)
    $parts = $raw -split "___HTTP_CODE___"
    $bodyText = $parts[0]
    $code = if ($parts.Count -gt 1) { $parts[1].Trim() } else { "" }
    try {
        $parsed = $bodyText | ConvertFrom-Json
    } catch {
        return [PSCustomObject]@{ Ok = $false; Reason = "INVALID_JSON"; StatusCode = $code; Body = $bodyText }
    }
    if ($code -ne "200") {
        return [PSCustomObject]@{ Ok = $false; Reason = "HTTP_$code"; StatusCode = $code; Body = $parsed }
    }
    if ([string]$parsed.status -ne "ready") {
        return [PSCustomObject]@{ Ok = $false; Reason = "STATUS_NOT_READY"; StatusCode = $code; Body = $parsed }
    }
    return [PSCustomObject]@{ Ok = $true; Reason = "OK"; StatusCode = $code; Body = $parsed }
}

function Get-WheelhouseIdentitySha256 {
    <# Duplicated from prepare_bys360_candidate.ps1 (matches this codebase's
       existing sibling-script convention -- ConvertFrom-DatabaseUrl and
       Test-LogForRealErrors above are duplicated the same way rather than
       factored into a shared module). Must byte-for-byte match
       scripts\release\build_bys360_wheelhouse.py's wheelhouse_identity():
       sha256 over a UTF-8 text blob of sorted "filename:sha256\n" lines
       (case-insensitive filename sort), one line per wheel, trailing
       newline included.

       Sort MUST use ordinal (codepoint) comparison, not PowerShell's
       default culture-aware `Sort-Object` -- see prepare_bys360_candidate.ps1's
       copy of this function for the real repro (confirmed on a
       Turkish-locale host: Python's ordinal sort and plain `Sort-Object`
       ordered the same 59 real wheel filenames differently, changing the
       final hash with zero actual file content difference). #>
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

# =====================================================================
# Phase 1: verify the candidate receipt -- THE hard gate. Refuses to run
# before touching anything unless every bound value is recomputed from the
# real on-disk candidate tree and matches, not merely "the JSON file
# exists".
# =====================================================================

function Assert-ValidCandidateReceipt {
    param([Parameter(Mandatory)][string]$CandidateDir)

    Write-DeployLog "Phase 1/20: verify CANDIDATE_READY.json and its binding to the on-disk candidate tree"

    $receiptPath = Join-Path $CandidateDir "CANDIDATE_READY.json"
    if (-not (Test-Path $CandidateDir)) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Candidate directory does not exist: $CandidateDir"
    }
    if (-not (Test-Path $receiptPath)) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "CANDIDATE_READY.json not found in candidate directory: $receiptPath. Run prepare_bys360_candidate.ps1 first; cutover refuses to build/verify anything itself."
    }

    try {
        $receipt = Get-Content -Path $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "CANDIDATE_READY.json is not valid JSON: $($_.Exception.Message)"
    }

    if ($receipt.CANDIDATE_READY -ne "YES") {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "CANDIDATE_READY.json CANDIDATE_READY field is '$($receipt.CANDIDATE_READY)', expected 'YES' -- this looks like a partial/failed preparation run's leftover receipt."
    }
    if ($receipt.SOURCE_SHA -ne $CandidateSourceSha) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt SOURCE_SHA '$($receipt.SOURCE_SHA)' != requested -CandidateSourceSha '$CandidateSourceSha'."
    }
    $expectedCandidateDirFull = [System.IO.Path]::GetFullPath($CandidateDir)
    $receiptCandidateDirFull = [System.IO.Path]::GetFullPath([string]$receipt.CANDIDATE_DIR)
    if ($receiptCandidateDirFull -ne $expectedCandidateDirFull) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt CANDIDATE_DIR '$($receipt.CANDIDATE_DIR)' does not resolve to the candidate directory being cut over '$CandidateDir' -- this receipt may have been copied from a different candidate."
    }

    foreach ($gate in @("PIP_CHECK", "IMPORT_GATES", "APP_FACTORY_CHECK", "SHADOW_REHEARSAL_RESULT")) {
        $value = $receipt.$gate
        if ($value -ne "PASS") {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt gate '$gate' = '$value', expected 'PASS'."
        }
    }
    if ($receipt.HEALTH_CHECK_RESULT -ne "200") {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt HEALTH_CHECK_RESULT = '$($receipt.HEALTH_CHECK_RESULT)', expected '200'."
    }
    # Coordinator fix (2026-08-25, schema-contract-drift wave, real-worktree
    # tamper-test audit): a tampered/corrupted SCHEMA_CONTRACT_CHECK or
    # FILE_CENTER_TABLES value in CANDIDATE_READY.json previously passed
    # Phase 1 completely unchecked (confirmed by direct reproduction: both
    # fields could be set to an obviously-failed value and Assert-
    # ValidCandidateReceipt raised no objection at all). FILE_CENTER_TABLES
    # is still independently re-verified for real against the LIVE database
    # later in Invoke-LiveMigration, but that is no reason to skip an early,
    # cheap fail-fast check here too -- catching an already-known-bad claim
    # at Phase 1 avoids unnecessarily stopping the live service only to
    # fail much later. SCHEMA_CONTRACT_CHECK previously had NO live
    # re-verification anywhere in this script at all (unlike File Center);
    # see Test-LiveSchemaContract below for the deeper fix.
    if ($receipt.SCHEMA_CONTRACT_CHECK -ne "PASS") {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt SCHEMA_CONTRACT_CHECK = '$($receipt.SCHEMA_CONTRACT_CHECK)', expected 'PASS'."
    }
    if ($receipt.FILE_CENTER_TABLES -and $receipt.FILE_CENTER_TABLES -ne "SKIPPED") {
        $fcParts = ([string]$receipt.FILE_CENTER_TABLES) -split "/"
        if ($fcParts.Count -ne 2 -or $fcParts[0] -ne $fcParts[1]) {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt FILE_CENTER_TABLES = '$($receipt.FILE_CENTER_TABLES)' does not show a complete table set (expected 'N/N', e.g. '19/19')."
        }
    }

    if ($ExpectedPackageSha256) {
        if (([string]$receipt.PACKAGE_SHA256).ToLowerInvariant() -ne $ExpectedPackageSha256.ToLowerInvariant()) {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt PACKAGE_SHA256 '$($receipt.PACKAGE_SHA256)' != -ExpectedPackageSha256 '$ExpectedPackageSha256'."
        }
    } else {
        Write-DeployLog -Level "WARN" "-ExpectedPackageSha256 not supplied -- trusting the receipt's own recorded PACKAGE_SHA256 without an independent cross-check against the original release ZIP (which may no longer be present on this host). Supply it for maximum assurance."
    }

    # Recompute the on-disk dependency-lock hash and cross-check -- proves
    # nothing under the candidate directory was modified after prepare
    # signed off on it.
    $lockFileName = [string]$receipt.DEPENDENCY_LOCK_FILE
    if (-not $lockFileName) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt does not record DEPENDENCY_LOCK_FILE."
    }
    $lockFilePath = Join-Path $CandidateDir $lockFileName
    if (-not (Test-Path $lockFilePath)) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Recorded dependency-lock file no longer exists on disk: $lockFilePath"
    }
    $actualLockHash = (Get-FileHash -Path $lockFilePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualLockHash -ne ([string]$receipt.DEPENDENCY_LOCK_SHA256).ToLowerInvariant()) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Dependency-lock file '$lockFileName' hash drift detected: receipt=$($receipt.DEPENDENCY_LOCK_SHA256) actual=$actualLockHash. The candidate tree may have been modified after preparation signed off on it."
    }
    if ($receipt.DEPENDENCY_LOCK_MODE -eq "NETWORK_FALLBACK_TEST_ONLY") {
        Write-DeployLog -Level "WARN" "Receipt DEPENDENCY_LOCK_MODE = NETWORK_FALLBACK_TEST_ONLY -- this candidate's venv was NOT built offline from requirements.lock+wheelhouse. This must never be true for a real production cutover."
    }

    # Recompute the on-disk wheelhouse identity and cross-check -- proves
    # the candidate's bundled wheelhouse\ was not modified after prepare
    # signed off on it (same "recompute fresh, never trust the receipt
    # alone" pattern used above for the dependency-lock hash and below for
    # the Alembic head).
    if ($receipt.WHEELHOUSE_IDENTITY_SHA256) {
        $wheelhouseDirPath = Join-Path $CandidateDir "wheelhouse"
        $actualWheelhouseIdentity = Get-WheelhouseIdentitySha256 -WheelhouseDir $wheelhouseDirPath
        if (-not $actualWheelhouseIdentity) {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Receipt records WHEELHOUSE_IDENTITY_SHA256 but the candidate's wheelhouse directory is missing or empty: $wheelhouseDirPath"
        }
        if ($actualWheelhouseIdentity -ne ([string]$receipt.WHEELHOUSE_IDENTITY_SHA256).ToLowerInvariant()) {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Wheelhouse identity drift detected: receipt=$($receipt.WHEELHOUSE_IDENTITY_SHA256) actual=$actualWheelhouseIdentity. The candidate's wheelhouse\ may have been modified after preparation signed off on it."
        }
        Write-DeployLog "Wheelhouse identity cross-check OK: $actualWheelhouseIdentity"
    } else {
        Write-DeployLog -Level "WARN" "Receipt has no WHEELHOUSE_IDENTITY_SHA256 (legacy candidate prepared before this binding existed, or a non-wheelhouse network-fallback build) -- wheelhouse identity cross-check skipped."
    }

    $venvPython = Join-Path $CandidateDir ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Candidate venv python.exe not found: $venvPython"
    }

    # Recompute the candidate's Alembic head fresh, using its OWN venv --
    # proves migrations\ wasn't tampered with after preparation signed off.
    Push-Location $CandidateDir
    try {
        $headCheck = Invoke-Native { & $venvPython -c "from alembic.config import Config; from alembic.script import ScriptDirectory; c=Config('migrations/alembic.ini'); c.set_main_option('script_location','migrations'); s=ScriptDirectory.from_config(c); h=s.get_heads(); print(len(h)); print(h[0] if h else '')" 2>&1 }
        Assert-NativeSuccess -Phase "RECEIPT_INVALID" -CommandDescription "candidate Alembic head recomputation"
        $headLines = $headCheck -split "`r?`n" | Where-Object { $_ -ne "" }
        if ($headLines.Count -lt 2 -or $headLines[0] -ne "1") {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Candidate migrations\ no longer has exactly one Alembic head: $($headLines -join ' / ')"
        }
        if ($headLines[1] -ne [string]$receipt.MIGRATION_HEAD) {
            Invoke-FailClosed -Phase "RECEIPT_INVALID" -Reason "Recomputed Alembic head '$($headLines[1])' != receipt MIGRATION_HEAD '$($receipt.MIGRATION_HEAD)'. The candidate's migrations\ tree may have been modified after preparation signed off on it."
        }
    } finally {
        Pop-Location
    }

    Write-DeployLog "Candidate receipt verified and bound to on-disk tree: SOURCE_SHA=$($receipt.SOURCE_SHA) MIGRATION_HEAD=$($receipt.MIGRATION_HEAD) DEPENDENCY_LOCK_MODE=$($receipt.DEPENDENCY_LOCK_MODE)"
    Write-DeployLog "CANDIDATE RECEIPT VALID."
    return $receipt
}

# =====================================================================
# Phase 2: host prerequisites + current live identity (informational)
# =====================================================================

function Test-HostPrerequisites {
    Write-DeployLog "Phase 2/20: PRECHECK -- host prerequisites"

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

    foreach ($exe in @("pg_dump.exe", "psql.exe")) {
        if (-not (Test-Path (Join-Path $PgBinPath $exe))) {
            Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "$exe not found at expected path: $PgBinPath"
        }
    }

    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $existingTask) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "Scheduled Task '$TaskName' does not exist. This script only cuts over an EXISTING task; it does not create one."
    }
    Write-DeployLog "Existing Scheduled Task '$TaskName' found, current state: $($existingTask.State)"

    if (-not $ProductionDbName) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "-ProductionDbName was not supplied and has no default, by design."
    }
    if (-not (Test-Path $ProjectRoot)) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "ProjectRoot does not exist: $ProjectRoot (expected an existing live tree to cut over FROM)."
    }

    foreach ($dir in @($PreviousRoot, $BackupRoot)) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
        }
    }

    Write-DeployLog "HOST PREREQUISITES PASSED."
}

function Get-CurrentLiveIdentity {
    <# Informational, not a hard gate by itself: reads the CURRENT live
       tree's own CANDIDATE_READY.json if present (it travels WITH a
       candidate when a prior cutover promotes it -- see Move-ApplicationTreeIntoPlace).
       Absent for the very first cutover ever run under this architecture
       (a tree built by the old deploy_bys360_ec4e56b_production_v*.ps1
       scripts has no such marker) -- that is expected and NOT fatal. #>
    Write-DeployLog "Phase 3/20: current live identity (informational)"
    $liveReceiptPath = Join-Path $ProjectRoot "CANDIDATE_READY.json"
    $currentSha = "UNKNOWN"
    if (Test-Path $liveReceiptPath) {
        try {
            $liveReceipt = Get-Content -Path $liveReceiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $currentSha = [string]$liveReceipt.SOURCE_SHA
            Write-DeployLog "Current live tree identity (from its own CANDIDATE_READY.json): SOURCE_SHA=$currentSha"
        } catch {
            Write-DeployLog -Level "WARN" "Current live tree has a CANDIDATE_READY.json but it could not be parsed: $($_.Exception.Message)"
        }
    } else {
        Write-DeployLog -Level "WARN" "Current live tree has no CANDIDATE_READY.json (expected for the first cutover under this architecture, or for a tree built by an older deploy_bys360_ec4e56b_production_v*.ps1 script). SOURCE_SHA recorded as UNKNOWN."
    }
    if ($currentSha -eq $CandidateSourceSha) {
        if ($AllowSameSourceSha) {
            Write-DeployLog -Level "WARN" "Candidate SOURCE_SHA equals the current live SOURCE_SHA, but -AllowSameSourceSha was supplied -- continuing (recovery/rerun mode)."
        } else {
            Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "Candidate SOURCE_SHA '$CandidateSourceSha' equals the CURRENT live SOURCE_SHA -- this cuts over onto an identical version, almost certainly an operator mistake. Pass -AllowSameSourceSha only if this is a deliberate recovery/rerun."
        }
    }
    $Script:Receipt.PREVIOUS_SOURCE_SHA = $currentSha
    return $currentSha
}

# =====================================================================
# Phase 4: current DB revision (read-only)
# =====================================================================

function Get-CurrentDbRevision {
    param([Parameter(Mandatory)][hashtable]$DbConn)
    Write-DeployLog "Phase 4/20: current DB revision"
    $psql = Join-Path $PgBinPath "psql.exe"
    $env:PGPASSWORD = $DbConn.Password
    try {
        $revRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $DbConn.Database -t -A -c "SELECT version_num FROM alembic_version;" 2>&1 }
        Assert-NativeSuccess -Phase "PRECHECK_FAILED" -CommandDescription "psql alembic_version query"
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }
    $rev = ($revRaw | Out-String).Trim()
    $Script:Receipt.DB_REVISION_BEFORE = $rev
    Write-DeployLog "Current DB revision: $rev"
    return $rev
}

# =====================================================================
# Phase 5: final pre-cutover DB backup
# =====================================================================

function Backup-LiveDatabase {
    param([Parameter(Mandatory)][hashtable]$DbConn)
    Write-DeployLog "Phase 5/20: final pre-cutover PostgreSQL backup"
    $backupDir = Join-Path $BackupRoot "predeploy_cutover_$($Script:DeployId)"
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
# Phase 6: preserve current .env / instance\ (ported from V4's
# Protect-PersistentState)
# =====================================================================

function Protect-PersistentState {
    Write-DeployLog "Phase 6/20: preserve .env and instance\"
    $preserveDir = Join-Path $BackupRoot "cutover_state_$($Script:DeployId)"
    New-Item -ItemType Directory -Force -Path $preserveDir | Out-Null

    $envSrc = Join-Path $ProjectRoot ".env"
    $envDst = Join-Path $preserveDir ".env"
    if (-not (Test-Path $envSrc)) {
        Invoke-FailClosed -Phase "STATE_PRESERVE_FAILED" -Reason "Current live .env not found: $envSrc"
    }
    Copy-Item -Path $envSrc -Destination $envDst -Force
    if (-not (Test-Path $envDst)) {
        Invoke-FailClosed -Phase "STATE_PRESERVE_FAILED" -Reason "Failed to preserve .env to $envDst"
    }

    $instanceSrc = Join-Path $ProjectRoot "instance"
    if (Test-Path $instanceSrc) {
        $instanceDst = Join-Path $preserveDir "instance"
        Copy-Item -Path $instanceSrc -Destination $instanceDst -Recurse -Force
        if (-not (Test-Path $instanceDst)) {
            Invoke-FailClosed -Phase "STATE_PRESERVE_FAILED" -Reason "Failed to preserve instance\ to $instanceDst"
        }
    } else {
        Write-DeployLog -Level "WARN" "No instance\ directory found under $ProjectRoot to preserve."
    }

    Write-DeployLog "Persistent state preserved to: $preserveDir"
    Write-DeployLog "($StorageRoot and $LocalStorageRoot are NOT copied -- they remain external and untouched in place.)"
    Write-DeployLog "STATE PRESERVATION PASSED."
    return $preserveDir
}

# =====================================================================
# Phase 7-8: stop live service + confirm port stopped listening (ported
# from V4's Stop-LiveService)
# =====================================================================

function Stop-LiveService {
    Write-DeployLog "Phase 7/20: stop live Scheduled Task"
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

    Write-DeployLog "Phase 8/20: confirm port $AppPort stopped listening"
    # BYS360 DEFECT Z: this was previously a WARN-only check -- a stale
    # process that Stop-ScheduledTask failed to actually terminate (e.g. an
    # orphaned python.exe no longer tracked by Task Scheduler) could keep
    # holding $AppPort right through promotion and the live migration, then
    # get silently accepted as "the new candidate is up" by Start-
    # LiveService's port-listening check alone. Failing closed here, before
    # the application tree is even touched, is the single most direct way
    # to guarantee a stale process can never masquerade as the freshly
    # promoted one.
    $stalePortBinding = Get-ListeningProcessOnPort -Port $AppPort
    if ($stalePortBinding) {
        Invoke-FailClosed -Phase "SERVICE_STOP_FAILED" -Reason "Port $AppPort is still listening after Stop-ScheduledTask (pid=$($stalePortBinding.Pid) exe='$($stalePortBinding.ExecutablePath)' cmd='$($stalePortBinding.CommandLine)'). Refusing to proceed while a stale process may still be serving traffic -- investigate and terminate it manually before re-running cutover."
    }
    Write-DeployLog "Confirmed: nothing listening on port $AppPort."
    Write-DeployLog "SERVICE STOP PASSED."
}

# =====================================================================
# Phase 9-11: move old tree to previous\, promote candidate to project\,
# restore .env/instance\, verify promoted identity. See script header for
# the two-step-promotion safety net.
# =====================================================================

function Move-ApplicationTreeIntoPlace {
    param(
        [Parameter(Mandatory)][string]$CandidateDir,
        [Parameter(Mandatory)][string]$PreviousSourceSha
    )
    Write-DeployLog "Phase 9/20: move current tree to previous\, promote candidate to project\"

    $shaForPreviousDir = if ($PreviousSourceSha -and $PreviousSourceSha -ne "UNKNOWN") { $PreviousSourceSha } else { "unknown" }
    $previousDir = Join-Path $PreviousRoot "$($Script:DeployId)_$shaForPreviousDir"

    Assert-SafeMutationTarget -Path $ProjectRoot -ExpectedExact $ProjectRoot -Phase "PROMOTION_FAILED" -RequiredSuffixRegex ([regex]::Escape("\bys360\project"))
    Assert-SafeMutationTarget -Path $previousDir -ExpectedExact $previousDir -Phase "PROMOTION_FAILED" -RequiredSuffixRegex ([regex]::Escape("\bys360\previous\"))
    Assert-SafeMutationTarget -Path $CandidateDir -ExpectedExact $CandidateDir -Phase "PROMOTION_FAILED" -RequiredSuffixRegex ([regex]::Escape("\bys360\candidate\"))

    if (Test-Path $previousDir) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Computed previous-tree destination already exists unexpectedly: $previousDir"
    }
    if (-not (Test-Path $PreviousRoot)) {
        New-Item -ItemType Directory -Force -Path $PreviousRoot | Out-Null
    }

    $movedOldOut = $false
    try {
        Move-Item -Path $ProjectRoot -Destination $previousDir -Force
        $movedOldOut = $true
        Write-DeployLog "Moved current tree: $ProjectRoot -> $previousDir"

        Move-Item -Path $CandidateDir -Destination $ProjectRoot -Force
        Write-DeployLog "Promoted candidate tree: $CandidateDir -> $ProjectRoot"
    } catch {
        if ($movedOldOut -and -not (Test-Path $ProjectRoot)) {
            Write-DeployLog -Level "FATAL" "Candidate promotion failed AFTER the old tree was moved out -- attempting best-effort safety-net restore of the old tree to $ProjectRoot."
            try {
                Move-Item -Path $previousDir -Destination $ProjectRoot -Force
                Write-DeployLog -Level "WARN" "Safety-net restore succeeded: $ProjectRoot now contains the PREVIOUS (pre-cutover) tree again."
            } catch {
                Write-DeployLog -Level "FATAL" "SAFETY-NET RESTORE ALSO FAILED. $ProjectRoot may not exist. Manual operator intervention required immediately. Old tree may still be at: $previousDir. Underlying error: $($_.Exception.Message)"
            }
        }
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Application tree promotion failed: $($_.Exception.Message)"
    }

    $Script:Receipt.PREVIOUS_DIR = $previousDir
    Write-DeployLog "APPLICATION TREE PROMOTION PASSED."
    return $previousDir
}

function Restore-PersistentState {
    param([Parameter(Mandatory)][string]$PreserveDir)
    Write-DeployLog "Phase 10/20: restore .env and instance\ into the newly-promoted tree"

    $restoredEnv = Join-Path $ProjectRoot ".env"
    Copy-Item -Path (Join-Path $PreserveDir ".env") -Destination $restoredEnv -Force
    if (-not (Test-Path $restoredEnv)) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Failed to restore preserved .env into promoted tree."
    }

    $preservedInstance = Join-Path $PreserveDir "instance"
    if (Test-Path $preservedInstance) {
        Copy-Item -Path $preservedInstance -Destination (Join-Path $ProjectRoot "instance") -Recurse -Force
    }

    Write-DeployLog "PERSISTENT STATE RESTORE PASSED."
}

function Test-PromotedTreeIdentity {
    param([Parameter(Mandatory)][string]$ExpectedSourceSha, [Parameter(Mandatory)][string]$ExpectedMigrationHead)
    Write-DeployLog "Phase 11/20: verify promoted tree runtime identity"

    $receiptPath = Join-Path $ProjectRoot "CANDIDATE_READY.json"
    if (-not (Test-Path $receiptPath)) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Promoted tree is missing CANDIDATE_READY.json at $receiptPath -- the move may not have carried the candidate's own receipt correctly."
    }
    $receipt = Get-Content -Path $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($receipt.SOURCE_SHA -ne $ExpectedSourceSha) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Promoted tree CANDIDATE_READY.json SOURCE_SHA '$($receipt.SOURCE_SHA)' != expected '$ExpectedSourceSha'."
    }
    if ($receipt.MIGRATION_HEAD -ne $ExpectedMigrationHead) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Promoted tree CANDIDATE_READY.json MIGRATION_HEAD '$($receipt.MIGRATION_HEAD)' != expected '$ExpectedMigrationHead'."
    }
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Promoted tree venv python.exe not found: $venvPython"
    }
    if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
        Invoke-FailClosed -Phase "PROMOTION_FAILED" -Reason "Promoted tree .env not found after restore."
    }
    Write-DeployLog "Promoted tree identity confirmed: SOURCE_SHA=$($receipt.SOURCE_SHA) MIGRATION_HEAD=$($receipt.MIGRATION_HEAD)"
    Write-DeployLog "PROMOTED TREE IDENTITY VERIFICATION PASSED."
    return $venvPython
}

# =====================================================================
# Phase 12-14: LIVE migration + post-migration verification. Unlike the
# shadow rehearsal in prepare_bys360_candidate.ps1, no environment
# injection is used here -- by this point .env has been physically
# restored next to the promoted tree's own config.py (Phase 10), so
# config.py's own load_dotenv(DOTENV_PATH) mechanism works exactly as it
# does for the real live application. This matches V4's Invoke-LiveMigration
# exactly.
# =====================================================================

function Test-LiveSchemaContract {
    <# Coordinator addition (2026-08-25, schema-contract-drift wave, real-
       worktree tamper-test audit): closes a real, independently-discovered
       gap -- unlike File Center (re-verified for real against the LIVE
       database in Invoke-LiveMigration below), this script previously had
       NO live re-verification of app.bootstrap.schema_contract /
       schema_validation at all; it was only ever checked once against a
       DISPOSABLE SHADOW database during candidate preparation
       (prepare_bys360_candidate.ps1's Test-ShadowSchemaContract). A stale
       backup, a live DB that drifted between candidate prep and cutover,
       or simply trusting a receipt claim, could let a real schema gap
       reach production undetected. Mirrors Test-ShadowSchemaContract's
       probe exactly, but against the just-migrated LIVE database, using
       the promoted tree's own venv and its own restored .env (no
       DATABASE_URL override needed -- by this point in the pipeline the
       promoted tree's config.py resolves the real live DATABASE_URL on
       its own, exactly as the real running application would). #>
    param([Parameter(Mandatory)][string]$VenvPython)

    Write-DeployLog "Phase 13a/20: LIVE schema-contract verification (real app.bootstrap.schema_contract / schema_validation, against the just-migrated live database)"

    $probeLines = @(
        "import sys",
        "sys.path.insert(0, r'$ProjectRoot')",
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
    $tmpProbe = Join-Path $env:TEMP "bys360_live_schema_contract_probe_$($Script:DeployId).py"
    Set-Content -Path $tmpProbe -Value $probeLines -Encoding UTF8

    Push-Location $ProjectRoot
    try {
        $env:FLASK_APP = "wsgi.py"
        $env:FLASK_SKIP_SCHEMA_VALIDATION = "1"
        $env:AUTO_REPAIR_SCHEMA = "false"
        try {
            $contractOutput = Invoke-Native { & $VenvPython $tmpProbe 2>&1 }
            $contractExit = $LASTEXITCODE
        } finally {
            Remove-Item Env:\FLASK_APP -ErrorAction SilentlyContinue
            Remove-Item Env:\FLASK_SKIP_SCHEMA_VALIDATION -ErrorAction SilentlyContinue
            Remove-Item Env:\AUTO_REPAIR_SCHEMA -ErrorAction SilentlyContinue
        }
    } finally {
        Pop-Location
        Remove-Item -Path $tmpProbe -ErrorAction SilentlyContinue
    }

    $contractText = ($contractOutput | Out-String)
    $contractText.Split("`n") | ForEach-Object { if ($_.Trim()) { Write-DeployLog "live schema-contract: $($_.Trim())" } }
    if ($contractExit -ne 0 -or $contractText -notmatch "SCHEMA_CONTRACT_ERROR_COUNT=0") {
        $Script:Receipt.MIGRATION_RESULT = "FAIL"
        Invoke-FailClosed -Phase "LIVE_MIGRATION_FAILED" -Reason "LIVE database does not satisfy app.bootstrap.schema_contract's expected schema after migration -- see live schema-contract log lines above for exact missing table/column names. Scheduled Task NOT started. Pre-migration backup preserved."
    }
    Write-DeployLog "LIVE SCHEMA CONTRACT VERIFICATION PASSED (zero missing required tables/columns)."
}

function Invoke-LiveMigration {
    param([Parameter(Mandatory)][hashtable]$DbConn, [Parameter(Mandatory)][string]$VenvPython)

    Write-DeployLog "Phase 12/20: LIVE database migration"
    Write-DeployLog "About to run against the LIVE production database. A fresh backup was taken this run (Phase 5)."

    Push-Location $ProjectRoot
    try {
        $env:FLASK_APP = "wsgi.py"
        $env:APP_ENV = "production"
        try {
            $upgradeOutput = Invoke-Native { & $VenvPython -m flask db upgrade 2>&1 }
            $upgradeExit = $LASTEXITCODE
        } finally {
            Remove-Item Env:\FLASK_APP -ErrorAction SilentlyContinue
            Remove-Item Env:\APP_ENV -ErrorAction SilentlyContinue
        }
    } finally {
        Pop-Location
    }
    ($upgradeOutput | Out-String).Split("`n") | ForEach-Object { if ($_.Trim()) { Write-DeployLog "flask db upgrade (LIVE): $($_.Trim())" } }

    if ($upgradeExit -ne 0) {
        $Script:Receipt.MIGRATION_RESULT = "FAIL"
        Invoke-FailClosed -Phase "LIVE_MIGRATION_FAILED" -Reason "`flask db upgrade` against LIVE database failed, exit_code=$upgradeExit. Pre-migration backup preserved at $($Script:Receipt.DB_BACKUP_PATH). NO automatic downgrade was attempted. The Scheduled Task was NOT started."
    }

    Write-DeployLog "Phase 13/20: live DB post-migration verification (revision + File Center)"
    $psql = Join-Path $PgBinPath "psql.exe"
    $env:PGPASSWORD = $DbConn.Password
    try {
        $revRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $DbConn.Database -t -A -c "SELECT version_num FROM alembic_version;" 2>&1 }
        Assert-NativeSuccess -Phase "LIVE_MIGRATION_FAILED" -CommandDescription "post-migration alembic_version query"
        $rev = ($revRaw | Out-String).Trim()

        if (-not $SkipFileCenterTableCheck) {
            $fcTables = @(
                'file_storage_folders','file_storage_items','file_transfers','file_transfer_items',
                'file_transfer_recipients','file_share_links','file_requests','file_request_uploads',
                'file_download_logs','file_access_logs','file_quota_usage','file_security_scans',
                'file_audit_logs','file_quota_policies','file_upload_sessions','file_upload_chunks',
                'file_center_mail_logs','file_center_role_permissions','file_center_settings'
            )
            $inClause = ($fcTables | ForEach-Object { "'$_'" }) -join ","
            $fcCountRaw = Invoke-Native { & $psql -h $DbConn.HostName -p $DbConn.Port -U $DbConn.User -d $DbConn.Database -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ($inClause);" 2>&1 }
            Assert-NativeSuccess -Phase "LIVE_MIGRATION_FAILED" -CommandDescription "post-migration File Center table count query"
            $fcCount = [int](($fcCountRaw | Out-String).Trim())
            $Script:Receipt.FILE_CENTER_TABLES = "$fcCount/19"
            if ($fcCount -ne 19) {
                $Script:Receipt.MIGRATION_RESULT = "FAIL"
                Invoke-FailClosed -Phase "LIVE_MIGRATION_FAILED" -Reason "Post-migration File Center table count = $fcCount, expected 19. Scheduled Task NOT started. Pass -SkipFileCenterTableCheck only for a release whose migration chain does not touch File Center."
            }
        } else {
            $Script:Receipt.FILE_CENTER_TABLES = "SKIPPED"
        }
    } finally {
        Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    }

    Test-LiveSchemaContract -VenvPython $VenvPython
    $Script:Receipt.SCHEMA_CONTRACT_CHECK = "PASS"

    $Script:Receipt.DB_REVISION_AFTER = $rev
    $Script:Receipt.MIGRATION_RESULT = "PASS"
    Write-DeployLog "LIVE MIGRATION PASSED: revision=$rev File Center=$($Script:Receipt.FILE_CENTER_TABLES)"
    return $rev
}

# =====================================================================
# Phase 15-16: start service + health checks (ported from V4)
# =====================================================================

function Start-LiveService {
    Write-DeployLog "Phase 15/20: start live Scheduled Task"
    if (Test-Path $LogPath) { $preStartSize = (Get-Item $LogPath).Length } else { $preStartSize = 0 }

    # BYS360 DEFECT Z: captured immediately before Start-ScheduledTask so
    # Test-ProcessBinding below can prove the eventually-listening process
    # is genuinely FRESH (started by this exact invocation), not a stale
    # leftover that slipped past the now-fail-closed Stop-LiveService check.
    $startInvokeUtc = (Get-Date).ToUniversalTime()

    Start-ScheduledTask -TaskName $TaskName
    $started = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Seconds 2
        $listening = Get-NetTCPConnection -LocalPort $AppPort -State Listen -ErrorAction SilentlyContinue
        if ($listening) { $started = $true; break }
    }
    if (-not $started) {
        $Script:Receipt.SERVICE_RESULT = "FAIL"
        Invoke-FailClosed -Phase "SERVICE_START_FAILED" -Reason "Nothing is listening on port $AppPort after 40 seconds of waiting post Start-ScheduledTask. Check $LogPath."
    }
    Write-DeployLog "Confirmed listening on port $AppPort."

    # BYS360 DEFECT Z: "something is listening" alone is not proof it is
    # OUR freshly-started process serving the just-promoted tree -- bind the
    # actual owning PID's executable path / command line / start time.
    $expectedExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    # BYS360 DEFECT Z HOTFIX: also accept the candidate venv's own recorded
    # base interpreter (see Get-CandidateVenvBaseExecutable) -- Windows venv
    # redirector semantics mean Win32_Process.ExecutablePath legitimately
    # reports that path, not the venv launcher, for the real promoted
    # process. Fails closed (not a silent single-path fallback) if the
    # candidate's own pyvenv.cfg cannot be read.
    $candidateVenvBaseExe = Get-CandidateVenvBaseExecutable -VenvRoot (Join-Path $ProjectRoot ".venv")
    if (-not $candidateVenvBaseExe) {
        $Script:Receipt.SERVICE_RESULT = "FAIL"
        Invoke-FailClosed -Phase "SERVICE_START_FAILED" -Reason "Could not resolve the candidate venv's own base interpreter from '$(Join-Path $ProjectRoot ".venv\pyvenv.cfg")' (missing file or no 'executable = ' entry). Process binding cannot be safely evaluated without it."
    }
    $expectedRunServerPath = Join-Path $ProjectRoot "run_server.py"
    $processBinding = Test-ProcessBinding -Port $AppPort -ExpectedExecutablePath @($expectedExe, $candidateVenvBaseExe) -ExpectedCommandLineFragment $expectedRunServerPath -NotBeforeUtc $startInvokeUtc
    if (-not $processBinding.Ok) {
        $Script:Receipt.SERVICE_RESULT = "FAIL"
        $Script:Receipt.PROCESS_BINDING = "FAIL:$($processBinding.Reason)"
        $bindingDetail = if ($processBinding.Binding) { "pid=$($processBinding.Binding.Pid) exe='$($processBinding.Binding.ExecutablePath)' cmd='$($processBinding.Binding.CommandLine)' created='$($processBinding.Binding.CreationDate)'" } else { "(no binding resolved)" }
        Invoke-FailClosed -Phase "SERVICE_START_FAILED" -Reason "Process binding check failed: $($processBinding.Reason). $bindingDetail. The listener on port $AppPort could not be proven to be a genuinely fresh process running the just-promoted candidate's own run_server.py."
    }
    $Script:Receipt.PROCESS_BINDING = "PASS:pid=$($processBinding.Binding.Pid)"
    Write-DeployLog "Process binding confirmed: pid=$($processBinding.Binding.Pid) exe='$($processBinding.Binding.ExecutablePath)'"

    Start-Sleep -Seconds 3
    $freshLogText = ""
    if (Test-Path $LogPath) {
        $stream = [System.IO.File]::Open($LogPath, 'Open', 'Read', 'ReadWrite')
        try {
            $stream.Seek($preStartSize, 'Begin') | Out-Null
            $reader = New-Object System.IO.StreamReader($stream, [System.Text.Encoding]::UTF8)
            $freshLogText = $reader.ReadToEnd()
        } finally {
            $stream.Dispose()
        }
    }
    $Script:StartupLogText = $freshLogText

    $errorHits = Test-LogForRealErrors -LogText $freshLogText
    if ($errorHits.Count -gt 0) {
        $Script:Receipt.SERVICE_RESULT = "FAIL"
        Invoke-FailClosed -Phase "SERVICE_START_FAILED" -Reason "Fresh startup log contains error-like patterns: $($errorHits -join '; '). See $LogPath."
    }
    $Script:Receipt.SERVICE_RESULT = "PASS"
    Write-DeployLog "SERVICE START PASSED. Fresh startup log clean."
}

function Test-LocalHealth {
    <# NOTE (found via direct testing while developing/testing
       prepare_bys360_candidate.ps1's equivalent check): Invoke-WebRequest's
       `-Headers @{"Host"=...}` does NOT actually change the wire-level Host
       header under Windows PowerShell 5.1 -- confirmed directly: the
       request still 400s ("Host '...' is not trusted", from config.py's
       TRUSTED_HOSTS validation) even when -Headers @{"Host"=$PublicHostName}
       is supplied, because .NET's HttpWebRequest treats Host as a
       restricted header with its own dedicated property and silently
       ignores a same-named entry in the generic Headers collection. This
       is exactly why V4's own Test-LocalHealth uses curl.exe instead of
       Invoke-WebRequest -- curl.exe, as a separate native process, has no
       such restriction. This function follows that same pattern. #>
    Write-DeployLog "Phase 16/20: local health check"
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
        Invoke-FailClosed -Phase "LOCAL_HEALTH_FAILED" -Reason "Local /healthz request failed: $($_.Exception.Message)"
    }
    if ($code -ne "200") {
        $Script:Receipt.LOCAL_HEALTH = "$code"
        Invoke-FailClosed -Phase "LOCAL_HEALTH_FAILED" -Reason "Local /healthz returned HTTP $code, expected 200."
    }
    $Script:Receipt.LOCAL_HEALTH = "200"
    Write-DeployLog "LOCAL HEALTH PASSED (HTTP 200)."
}

function Invoke-ReleaseIdentityCheck {
    param([Parameter(Mandatory)][string]$ExpectedSourceSha, [Parameter(Mandatory)][string]$ExpectedMigrationHead)
    Write-DeployLog "Phase 16a/20: release identity binding (GET /versionz)"
    $result = Test-ReleaseIdentityBinding -BaseUrl "http://127.0.0.1:$AppPort" -HostHeader $PublicHostName -ExpectedSourceSha $ExpectedSourceSha -ExpectedMigrationHead $ExpectedMigrationHead
    if (-not $result.Ok) {
        $Script:Receipt.RELEASE_IDENTITY = "FAIL:$($result.Reason)"
        Invoke-FailClosed -Phase "RELEASE_IDENTITY_FAILED" -Reason "/versionz release identity check failed: $($result.Reason). Expected source_sha=$ExpectedSourceSha migration_head=$ExpectedMigrationHead, response body: $($result.Body | ConvertTo-Json -Compress -Depth 4)"
    }
    $Script:Receipt.RELEASE_IDENTITY = "PASS"
    Write-DeployLog "RELEASE IDENTITY BINDING PASSED: source_sha=$ExpectedSourceSha migration_head=$ExpectedMigrationHead"
}

function Invoke-ReadinessCheck {
    Write-DeployLog "Phase 16b/20: readiness gate (GET /readyz)"
    $result = Test-ReadinessGate -BaseUrl "http://127.0.0.1:$AppPort" -HostHeader $PublicHostName
    if (-not $result.Ok) {
        $Script:Receipt.READINESS = "FAIL:$($result.Reason)"
        Invoke-FailClosed -Phase "READINESS_FAILED" -Reason "/readyz readiness gate failed: $($result.Reason) (http_code=$($result.StatusCode)). Response body: $($result.Body | ConvertTo-Json -Compress -Depth 4)"
    }
    $Script:Receipt.READINESS = "PASS"
    Write-DeployLog "READINESS GATE PASSED."
}

function Test-PublicHealth {
    Write-DeployLog "Phase 17/20: public health check"
    if ($SkipPublicHealthCheck) {
        $Script:Receipt.PUBLIC_HEALTH = "SKIPPED"
        Write-DeployLog -Level "WARN" "Public health check skipped via -SkipPublicHealthCheck."
        return
    }
    try {
        $response = Invoke-WebRequest -Uri "https://$PublicHostName/healthz" -UseBasicParsing -TimeoutSec 15
        $code = [int]$response.StatusCode
    } catch {
        $Script:Receipt.PUBLIC_HEALTH = "NETWORK_ERROR"
        Invoke-FailClosed -Phase "PUBLIC_HEALTH_FAILED" -Reason "Public health check raised a network-layer exception (LB/network failure, not necessarily an app failure): $($_.Exception.Message). Re-run with -SkipPublicHealthCheck if this host cannot reach its own public endpoint by design."
    }
    if ($code -ne 200) {
        $Script:Receipt.PUBLIC_HEALTH = "$code"
        Invoke-FailClosed -Phase "PUBLIC_HEALTH_FAILED" -Reason "Public https://$PublicHostName/healthz returned HTTP $code, expected 200."
    }
    $Script:Receipt.PUBLIC_HEALTH = "200"
    Write-DeployLog "PUBLIC HEALTH PASSED (HTTP 200)."
}

# =====================================================================
# Phase 18-19: safe smoke checks + post-deploy security log scan (ported
# from V4's Test-FileCenterAndPortalSmoke / Test-PostDeploySecurity)
# =====================================================================

function Test-SmokeChecks {
    param([Parameter(Mandatory)][string]$VenvPython)
    Write-DeployLog "Phase 18/20: smoke checks (read-only route registration + storage probe)"

    Push-Location $ProjectRoot
    try {
        $env:FLASK_APP = "wsgi.py"
        $env:APP_ENV = "production"
        # NOTE (found via direct testing while developing/testing
        # prepare_bys360_candidate.ps1's equivalent probe): `python
        # <script.py>` puts the SCRIPT's OWN directory on sys.path[0], NOT
        # the process's current working directory -- Push-Location
        # $ProjectRoot above does not, by itself, make `from app import
        # create_app` resolvable when the probe script physically lives
        # under $env:TEMP. sys.path.insert(0, ...) fixes this regardless of
        # where the temp script file itself is written.
        # NOTE (found via direct testing, not guessed): V4's original probe
        # checked `r.endpoint.startswith("file_center.")` / `"file_center"
        # in app.blueprints` -- confirmed directly this wave that this is
        # WRONG for this codebase's actual architecture: reading
        # app\bootstrap\route_bootstrap.py directly shows only 5 top-level
        # blueprints are ever registered ("main", "health",
        # "strategic_performance", "ai_agent", plus whatever
        # configure_route_bootstrap adds) -- File Center and Portal routes
        # are decorated directly onto the SAME shared `main_bp` (confirmed
        # in app\file_center\routes.py: `@main_bp.get("/file-center")`, and
        # app\portal\routes.py: `@main_bp.get("/portal")`), so their real
        # endpoint names are "main.file_center_..." / "main.portal_...",
        # never a separate "file_center."/"portal." blueprint prefix, and
        # "file_center"/"portal" never appear as keys in app.blueprints at
        # all. A real end-to-end run of V4's original check would have
        # always reported FC_BLUEPRINT_REGISTERED=False /
        # PORTAL_BLUEPRINT_REGISTERED=False -- V4 was never run end-to-end
        # (see its own header) so this was never caught. This probe checks
        # the real, confirmed endpoint-name substring instead.
        $probeLines = @(
            'import sys',
            "sys.path.insert(0, r'$ProjectRoot')",
            'from app import create_app',
            'app = create_app()',
            'all_rules = list(app.url_map.iter_rules())',
            'fc_rules = [r for r in all_rules if "file_center" in r.endpoint]',
            'portal_rules = [r for r in all_rules if "portal" in r.endpoint]',
            'guest_endpoints = [r.endpoint for r in fc_rules if "guest" in r.endpoint]',
            'chunk_endpoints = [r.endpoint for r in fc_rules if "chunk" in r.endpoint]',
            'print("FC_ROUTE_COUNT", len(fc_rules))',
            'print("PORTAL_ROUTE_COUNT", len(portal_rules))',
            'print("FC_GUEST_ENDPOINTS", len(guest_endpoints))',
            'print("FC_CHUNK_ENDPOINTS", len(chunk_endpoints))',
            'print("ROUTE_COUNT", len(all_rules))',
            'print("SMOKE_OK")'
        )
        $tmpProbe = Join-Path $env:TEMP "bys360_cutover_smoke_$($Script:DeployId).py"
        Set-Content -Path $tmpProbe -Value $probeLines -Encoding UTF8
        try {
            $probeOutput = Invoke-Native { & $VenvPython $tmpProbe 2>&1 }
        } finally {
            Remove-Item -Path $tmpProbe -ErrorAction SilentlyContinue
        }
        Assert-NativeSuccess -Phase "SMOKE_FAILED" -CommandDescription "route-registration smoke probe"
        $probeText = ($probeOutput | Out-String)
        Write-DeployLog "Smoke probe output: $probeText"
        if ($probeText -notmatch "SMOKE_OK") {
            Invoke-FailClosed -Phase "SMOKE_FAILED" -Reason "Route-registration smoke probe did not complete: $probeText"
        }
        if ($probeText -match "FC_ROUTE_COUNT 0") {
            Invoke-FailClosed -Phase "SMOKE_FAILED" -Reason "No File Center routes found in the promoted application's url_map."
        }
        if ($probeText -match "PORTAL_ROUTE_COUNT 0") {
            Invoke-FailClosed -Phase "SMOKE_FAILED" -Reason "No Portal routes found in the promoted application's url_map."
        }
        if ($probeText -match "FC_GUEST_ENDPOINTS 0" -or $probeText -match "FC_CHUNK_ENDPOINTS 0") {
            Invoke-FailClosed -Phase "SMOKE_FAILED" -Reason "File Center guest or chunk endpoints not found in url_map."
        }
    } finally {
        Remove-Item Env:\FLASK_APP -ErrorAction SilentlyContinue
        Remove-Item Env:\APP_ENV -ErrorAction SilentlyContinue
        Pop-Location
    }

    if (Test-Path $StorageRoot) {
        $probeFile = Join-Path $StorageRoot ("_bys360_cutover_probe_$($Script:DeployId).tmp")
        try {
            Set-Content -Path $probeFile -Value "cutover-probe" -Encoding UTF8 -ErrorAction Stop
            Remove-Item -Path $probeFile -ErrorAction Stop
            Write-DeployLog "Storage root write/delete probe OK: $StorageRoot"
        } catch {
            Write-DeployLog -Level "WARN" "Storage root write probe failed (non-fatal, investigate manually): $($_.Exception.Message)"
        }
    } else {
        Write-DeployLog -Level "WARN" "Storage root $StorageRoot does not exist -- skipping write probe."
    }

    $Script:Receipt.SMOKE = "PASS"
    Write-DeployLog "SMOKE CHECKS PASSED."
}

function Test-PostDeploySecurity {
    Write-DeployLog "Phase 19/20: post-deploy security/log gate"
    $logText = if ($Script:StartupLogText) { $Script:StartupLogText } else { "" }
    $errorHits = Test-LogForRealErrors -LogText $logText
    if ($errorHits.Count -gt 0) {
        $Script:Receipt.SECURITY_CRITICAL = "$($errorHits.Count)"
        Invoke-FailClosed -Phase "POST_DEPLOY_SECURITY_FAILED" -Reason "Post-deploy log scan found $($errorHits.Count) real error/critical pattern(s): $($errorHits -join '; ')"
    }
    $Script:Receipt.SECURITY_CRITICAL = "0"
    Write-DeployLog "POST-DEPLOY SECURITY GATE PASSED (security_critical=0)."
}

# =====================================================================
# Phase 20: DEPLOYMENT_RECEIPT.txt
# =====================================================================

function Write-SuccessReceipt {
    Write-DeployLog "Phase 20/20: write deployment receipt"
    $Script:Receipt.DEPLOY_EXIT_CODE = "0"
    $receiptPath = Join-Path $Script:DeployLogDir "DEPLOYMENT_RECEIPT.txt"
    $lines = @("BYS360 CANDIDATE CUTOVER -- DEPLOYMENT RECEIPT", "================================================================", "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')", "")
    foreach ($key in $Script:Receipt.Keys) {
        $lines += "{0,-24}: {1}" -f $key, $Script:Receipt[$key]
    }
    Set-Content -Path $receiptPath -Value $lines -Encoding UTF8
    Write-DeployLog "SUCCESS RECEIPT WRITTEN: $receiptPath"
    return $receiptPath
}

# =====================================================================
# MAIN
# =====================================================================

function Main {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"

    New-Item -ItemType Directory -Force -Path $Script:DeployLogDir | Out-Null
    $Script:LogFile = Join-Path $Script:DeployLogDir "cutover.log"
    Write-DeployLog "================================================================"
    Write-DeployLog "BYS360 CANDIDATE CUTOVER -- START (DeployId=$($Script:DeployId))"
    Write-DeployLog "================================================================"
    Write-DeployLog "  CandidateSourceSha = $CandidateSourceSha"
    Write-DeployLog "  ProjectRoot        = $ProjectRoot"
    Write-DeployLog "  PreviousRoot       = $PreviousRoot"
    Write-DeployLog "  ProductionDbName   = $ProductionDbName"
    Write-DeployLog "  TaskName           = $TaskName"
    Write-DeployLog "  SkipPublicHealthCheck = $($SkipPublicHealthCheck.IsPresent)"
    Write-DeployLog "(DATABASE_URL / passwords / secret keys are never printed or logged.)"

    $candidateDir = Join-Path $CandidateRoot $CandidateSourceSha
    $receipt = Assert-ValidCandidateReceipt -CandidateDir $candidateDir

    Test-HostPrerequisites
    $previousSha = Get-CurrentLiveIdentity

    if (-not $EnvFilePath) { $EnvFilePath = Join-Path $ProjectRoot ".env" }
    $dbConn = Get-ProductionDbConnection -EnvPath $EnvFilePath
    if ($dbConn.Database -ne $ProductionDbName) {
        Invoke-FailClosed -Phase "PRECHECK_FAILED" -Reason "-ProductionDbName '$ProductionDbName' does not match the database name parsed from DATABASE_URL ('$($dbConn.Database)')."
    }
    $dbRevBefore = Get-CurrentDbRevision -DbConn $dbConn
    if ($dbRevBefore -ne [string]$receipt.MIGRATION_HEAD -and -not $AllowDbRevisionMismatch) {
        Write-DeployLog "Current DB revision ($dbRevBefore) differs from candidate's migration head ($($receipt.MIGRATION_HEAD)) -- migration IS expected to do real work."
    }

    Backup-LiveDatabase -DbConn $dbConn | Out-Null
    $preserveDir = Protect-PersistentState
    Stop-LiveService

    Move-ApplicationTreeIntoPlace -CandidateDir $candidateDir -PreviousSourceSha $previousSha | Out-Null
    Restore-PersistentState -PreserveDir $preserveDir
    $venvPython = Test-PromotedTreeIdentity -ExpectedSourceSha $CandidateSourceSha -ExpectedMigrationHead ([string]$receipt.MIGRATION_HEAD)

    Invoke-LiveMigration -DbConn $dbConn -VenvPython $venvPython | Out-Null

    Start-LiveService
    Test-LocalHealth
    Invoke-ReleaseIdentityCheck -ExpectedSourceSha $CandidateSourceSha -ExpectedMigrationHead ([string]$receipt.MIGRATION_HEAD)
    Invoke-ReadinessCheck
    Test-PublicHealth
    Test-SmokeChecks -VenvPython $venvPython
    Test-PostDeploySecurity

    $receiptPath = Write-SuccessReceipt
    Write-DeployLog "================================================================"
    Write-DeployLog "CUTOVER SUCCEEDED. Receipt: $receiptPath"
    Write-DeployLog "ACTIVE_SOURCE_SHA=$CandidateSourceSha DB_REVISION=$($Script:Receipt.DB_REVISION_AFTER) PREVIOUS_TREE=$($Script:Receipt.PREVIOUS_DIR)"
    Write-DeployLog "================================================================"
}

# BYS360 DEFECT Z (testability, zero behavioral change to real invocation):
# $MyInvocation.InvocationName is '.' only when this script is DOT-SOURCED
# (". .\cutover_bys360_candidate.ps1"), never when run directly (-File or
# &) -- the only way this script is ever actually invoked for a real
# cutover. Dot-sourcing loads every function definition above (Test-
# ProcessBinding, Test-ReleaseIdentityBinding, Test-ReadinessGate, etc.)
# without running Main() or calling `exit` (which would terminate the
# CALLING session too), so a test harness can call these pure, parameterized
# functions in isolation against real local disposable resources -- no real
# Scheduled Task, no real port 80, no real PostgreSQL, no real C:\bys360\project.
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Main
        exit 0
    } catch {
        $Script:Receipt.DEPLOY_EXIT_CODE = "1"
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
