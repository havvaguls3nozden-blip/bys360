"""Regression tests for rollback_bys360_candidate.ps1's Phase 3a
"ACTIVE-DEPLOYMENT RECEIPT BINDING" gate (Assert-ActiveDeploymentBinding).

That gate is the coordinator's 2026-08-26 fix closing a real safety gap:
Phase 3 used to only RECORD the active tree's own SOURCE_SHA, never compare
it against anything independently sourced, so rollback could restore
-PreviousDir onto whatever tree happened to be sitting in ProjectRoot,
right or wrong. Phase 3a now requires a mandatory -ActiveDeploymentReceiptPath
pointing at the specific cutover's DEPLOYMENT_RECEIPT.txt, parses it
deterministically (Turkish-locale-safe via -cmatch/-cnotmatch -- see below),
and binds it to both ProjectRoot's own SOURCE_SHA and the supplied
-PreviousDir before anything else is checked.

This file exercises the REAL, unmodified Assert-ActiveDeploymentBinding
function from scripts/windows/rollback_bys360_candidate.ps1 directly --
not a hand-copied reimplementation of its parsing logic -- so a future
regression in the actual function is caught here, not just in a duplicate.

Technique: rollback_bys360_candidate.ps1 ends with a top-level
`try { Main; exit 0 } catch { ...; exit 1 }` that auto-runs on any
dot-source or invocation. Running Main() for real would (per the script's
own design) eventually stop/start the "BYS360 Live Waitress 80" Scheduled
Task, mutate C:\\bys360\\project / C:\\bys360\\previous, and query a real
Postgres DB -- none of which this test may do, and none of which is needed
to test Phase 3a in isolation. So each test extracts a byte-identical COPY
of the script truncated immediately before that trailing auto-invocation
block (a pure text split at a unique, stable marker -- the production
script on disk is never touched), dot-sources ONLY that function-definition
slice into an isolated child PowerShell process, wires up the same minimal
$Script:Receipt / $Script:DeployLogDir / $Script:LogFile state
Write-DeployLog/Write-FailureReceipt/Invoke-FailClosed depend on, then
calls the real Assert-ActiveDeploymentBinding against a fixture
DEPLOYMENT_RECEIPT.txt. No Scheduled Task, DB, port, or C:\\bys360\\*
application tree is ever touched by any scenario in this file; every
receipt/tree path is confined to a per-test tmp_path sandbox.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
PS_EXE = shutil.which("pwsh") or shutil.which("powershell")

ROLLBACK_SCRIPT = ROOT / "scripts" / "windows" / "rollback_bys360_candidate.ps1"

# The exact, stable text immediately preceding the script's trailing
# auto-invocation block (see module docstring). Truncating here yields the
# parameter block + every function DEFINITION (including Main's own body,
# which is harmless to define but is never called) with nothing left that
# executes automatically.
AUTO_INVOKE_MARKER = "try {\n    Main\n    exit 0\n} catch {"

CANDIDATE_SHA = "a" * 40
PREVIOUS_SHA = "b" * 40


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:  # noqa: F811 - deliberately shadows pytest's built-in tmp_path.
    """pytest's built-in `tmp_path` fixture cannot scan
    `AppData\\Local\\Temp\\pytest-of-...` on this machine because of the
    Turkish characters in the Windows username ('Havva Gulsen OZDEN') --
    PermissionError, an environment issue unrelated to this file's logic.
    Same workaround already used by
    tests/quality/test_rollback_live_release_contract_v1.py and
    tests/quality/test_installer_launcher_overwrite_guard_v1.py:
    `tempfile.mkdtemp()` (which uses an 8.3 short path) instead."""
    d = Path(tempfile.mkdtemp(prefix="bys360_rollback_binding_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _require_ps() -> str:
    if not PS_EXE:
        pytest.skip("PowerShell CLI not found; rollback binding-gate isolation test skipped.")
    return PS_EXE


def _ps_single_quote(value: str) -> str:
    """Python string -> safe PowerShell single-quoted literal. Not
    json.dumps: PowerShell's single-quote escaping rules differ from
    JSON's and would mangle Windows backslashes (same helper as the other
    rollback contract test file)."""
    return "'" + str(value).replace("'", "''") + "'"


def _function_defs_only(tmp_path: Path) -> Path:
    """Write a COPY of rollback_bys360_candidate.ps1, truncated immediately
    before its trailing `try { Main; exit 0 } catch {...}` block, into
    tmp_path. See module docstring for why. The real file on disk is only
    ever read, never modified."""
    text = ROLLBACK_SCRIPT.read_text(encoding="utf-8")
    idx = text.index(AUTO_INVOKE_MARKER)
    defs_only = text[:idx]
    assert "function Assert-ActiveDeploymentBinding" in defs_only, (
        "Assert-ActiveDeploymentBinding definition not found before the "
        "auto-invocation marker -- extraction slice is wrong."
    )
    out_path = tmp_path / "rollback_candidate_defs_only.ps1"
    out_path.write_text(defs_only, encoding="utf-8")
    return out_path


def _receipt_text(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def _control_receipt_lines(
    *,
    candidate_sha: str = CANDIDATE_SHA,
    previous_sha: str = PREVIOUS_SHA,
    previous_dir: str,
    deploy_exit_code: str = "0",
) -> list[str]:
    return [
        f"CANDIDATE_SOURCE_SHA: {candidate_sha}",
        f"PREVIOUS_SOURCE_SHA: {previous_sha}",
        f"PREVIOUS_DIR: {previous_dir}",
        f"DEPLOY_EXIT_CODE: {deploy_exit_code}",
    ]


def _run_binding_gate(
    *,
    tmp_path: Path,
    receipt_lines: list[str],
    current_sha: str,
    previous_identity_sha: str,
    supplied_previous_dir: str,
    culture: str | None = None,
) -> dict:
    """Dot-source the function-definitions-only slice, then call the real
    Assert-ActiveDeploymentBinding against a fixture receipt. Returns
    {"success": bool, "error": str|None, "deployment_binding": str}.
    """
    exe = _require_ps()
    defs_path = _function_defs_only(tmp_path)

    receipt_path = tmp_path / "DEPLOYMENT_RECEIPT.txt"
    receipt_path.write_text(_receipt_text(receipt_lines), encoding="utf-8")

    log_dir = tmp_path / "deploy_log"
    log_dir.mkdir(parents=True, exist_ok=True)
    out_json = tmp_path / "result.json"

    culture_prefix = ""
    if culture:
        # Reproduces the exact class of bug the -cmatch/-cnotmatch fix
        # guards against: under a culture such as tr-TR, .NET's
        # culture-aware case folding breaks [A-Za-z]-style character-class
        # ranges for strings containing the letter "I" (the well-known
        # "Turkish I" bug) -- which "CANDIDATE_SOURCE_SHA" contains. A
        # plain (non-'c') -match/-notmatch would silently fail to parse
        # that key under this culture.
        culture_prefix = (
            f"$__culture = New-Object System.Globalization.CultureInfo({_ps_single_quote(culture)})\n"
            "[System.Threading.Thread]::CurrentThread.CurrentCulture = $__culture\n"
            "[System.Threading.Thread]::CurrentThread.CurrentUICulture = $__culture\n"
        )

    harness = f"""
$ErrorActionPreference = 'Stop'
{culture_prefix}
. {_ps_single_quote(str(defs_path))} -PreviousDir {_ps_single_quote(supplied_previous_dir)} -ActiveDeploymentReceiptPath {_ps_single_quote(str(receipt_path))}

$Script:DeployLogDir = {_ps_single_quote(str(log_dir))}
$Script:LogFile = $null
$Script:Receipt = [ordered]@{{ QUARANTINE_DIR = ''; DEPLOYMENT_BINDING = '' }}

$currentIdentity = @{{ SourceSha = {_ps_single_quote(current_sha)} }}
$previousIdentity = @{{ SourceSha = {_ps_single_quote(previous_identity_sha)} }}

$success = $true
$errMsg = $null
try {{
    Assert-ActiveDeploymentBinding -CurrentIdentity $currentIdentity -PreviousIdentity $previousIdentity
}} catch {{
    $success = $false
    $errMsg = $_.Exception.Message
}}

$output = [PSCustomObject]@{{
    Success = $success
    Error = $errMsg
    DeploymentBinding = $Script:Receipt.DEPLOYMENT_BINDING
}}
$output | ConvertTo-Json -Depth 5 | Set-Content -Path {_ps_single_quote(str(out_json))} -Encoding UTF8
"""
    harness_path = tmp_path / "harness.ps1"
    harness_path.write_text(harness, encoding="utf-8")

    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(harness_path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"Test harness itself failed (not the function under test): "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert out_json.exists(), f"Harness produced no result JSON: stdout={result.stdout!r} stderr={result.stderr!r}"

    raw = json.loads(out_json.read_text(encoding="utf-8-sig"))
    return {
        "success": raw["Success"],
        "error": raw.get("Error"),
        "deployment_binding": raw.get("DeploymentBinding") or "",
    }


def _phase(error: str | None) -> str:
    m = re.match(r"^\[([A-Z_]+)\]", error or "")
    assert m, f"Failure message did not start with a [PHASE] tag: {error!r}"
    return m.group(1)


# ---------------------------------------------------------------------------
# 0) Static guard: the auto-invocation marker this file depends on must
#    still exist verbatim in the real script (fails loudly, not silently,
#    if the script's structure ever changes).
# ---------------------------------------------------------------------------


def test_auto_invoke_marker_present_in_real_script() -> None:
    text = ROLLBACK_SCRIPT.read_text(encoding="utf-8")
    assert AUTO_INVOKE_MARKER in text, (
        "rollback_bys360_candidate.ps1's trailing auto-invocation block no "
        "longer matches AUTO_INVOKE_MARKER -- update the marker in this "
        "test file so the function-extraction technique keeps working."
    )


# ---------------------------------------------------------------------------
# 1) CONTROL: a fully consistent receipt must pass the binding gate.
# ---------------------------------------------------------------------------


def test_control_matching_receipt_passes_binding_gate(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=previous_dir),
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is True, f"Control scenario unexpectedly failed: {result['error']}"
    assert result["deployment_binding"].startswith("PASS"), result["deployment_binding"]


# ---------------------------------------------------------------------------
# 2) NEGATIVE 1: active ProjectRoot SOURCE_SHA does not match the receipt's
#    CANDIDATE_SOURCE_SHA.
# ---------------------------------------------------------------------------


def test_candidate_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=previous_dir),
        current_sha="c" * 40,  # does not match receipt's CANDIDATE_SOURCE_SHA
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "ACTIVE_DEPLOYMENT_IDENTITY_MISMATCH"


# ---------------------------------------------------------------------------
# 3) NEGATIVE 2: the supplied -PreviousDir does not match the receipt's
#    PREVIOUS_DIR (canonical path comparison).
# ---------------------------------------------------------------------------


def test_previous_dir_mismatch_fails_closed(tmp_path: Path) -> None:
    receipt_previous_dir = str(tmp_path / "previous_tree_A")
    supplied_previous_dir = str(tmp_path / "previous_tree_B")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=receipt_previous_dir),
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=supplied_previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "PREVIOUS_DIR_DEPLOYMENT_MISMATCH"


# ---------------------------------------------------------------------------
# 4) NEGATIVE 3: -PreviousDir's own SOURCE_SHA does not match the receipt's
#    PREVIOUS_SOURCE_SHA.
# ---------------------------------------------------------------------------


def test_previous_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=previous_dir),
        current_sha=CANDIDATE_SHA,
        previous_identity_sha="d" * 40,  # does not match receipt's PREVIOUS_SOURCE_SHA
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "PREVIOUS_SHA_DEPLOYMENT_MISMATCH"


# ---------------------------------------------------------------------------
# 5) NEGATIVE 4-7: structurally invalid receipts -- all DEPLOYMENT_RECEIPT_INVALID.
# ---------------------------------------------------------------------------


def test_nonzero_deploy_exit_code_fails_closed(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=previous_dir, deploy_exit_code="1"),
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "DEPLOYMENT_RECEIPT_INVALID"


def test_missing_required_field_fails_closed(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    lines = [
        f"CANDIDATE_SOURCE_SHA: {CANDIDATE_SHA}",
        f"PREVIOUS_SOURCE_SHA: {PREVIOUS_SHA}",
        # PREVIOUS_DIR deliberately omitted.
        "DEPLOY_EXIT_CODE: 0",
    ]
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=lines,
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "DEPLOYMENT_RECEIPT_INVALID"


def test_duplicate_required_field_fails_closed(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    lines = _control_receipt_lines(previous_dir=previous_dir) + [
        f"CANDIDATE_SOURCE_SHA: {CANDIDATE_SHA}",  # duplicate of the first line
    ]
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=lines,
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "DEPLOYMENT_RECEIPT_INVALID"


def test_malformed_sha_fails_closed(tmp_path: Path) -> None:
    previous_dir = str(tmp_path / "previous_tree")
    lines = [
        "CANDIDATE_SOURCE_SHA: not-a-real-sha-value",
        f"PREVIOUS_SOURCE_SHA: {PREVIOUS_SHA}",
        f"PREVIOUS_DIR: {previous_dir}",
        "DEPLOY_EXIT_CODE: 0",
    ]
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=lines,
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "DEPLOYMENT_RECEIPT_INVALID"


# ---------------------------------------------------------------------------
# 6) Turkish-locale (tr-TR) regression guard for the -cmatch/-cnotmatch fix.
# ---------------------------------------------------------------------------


def test_control_receipt_parses_correctly_under_tr_tr_culture(tmp_path: Path) -> None:
    """Runs the exact CONTROL scenario under tr-TR culture. Before the
    -cmatch/-cnotmatch fix, the key-parsing regex used plain (culture-aware)
    -match, which fails to match 'CANDIDATE_SOURCE_SHA' under tr-TR (the
    "Turkish I" bug) -- the key would never be recognized, so even a
    perfectly valid, fully-matching receipt would incorrectly fail closed
    with DEPLOYMENT_RECEIPT_INVALID ("missing required field") under this
    culture. Asserting success here is a real regression guard: reverting
    -cmatch back to -match would turn this test red on any tr-TR-locale
    host (e.g. this project's own production host)."""
    previous_dir = str(tmp_path / "previous_tree")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=previous_dir),
        current_sha=CANDIDATE_SHA,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
        culture="tr-TR",
    )
    assert result["success"] is True, f"Control scenario failed under tr-TR culture: {result['error']}"
    assert result["deployment_binding"].startswith("PASS"), result["deployment_binding"]


def test_candidate_sha_mismatch_detected_under_tr_tr_culture(tmp_path: Path) -> None:
    """Companion to the success case above: proves the mismatch path is
    ALSO still correctly detected under tr-TR (i.e. the fix doesn't just
    make everything pass -- it parses the real value and compares it)."""
    previous_dir = str(tmp_path / "previous_tree")
    result = _run_binding_gate(
        tmp_path=tmp_path,
        receipt_lines=_control_receipt_lines(previous_dir=previous_dir),
        current_sha="c" * 40,
        previous_identity_sha=PREVIOUS_SHA,
        supplied_previous_dir=previous_dir,
        culture="tr-TR",
    )
    assert result["success"] is False
    assert _phase(result["error"]) == "ACTIVE_DEPLOYMENT_IDENTITY_MISMATCH"
