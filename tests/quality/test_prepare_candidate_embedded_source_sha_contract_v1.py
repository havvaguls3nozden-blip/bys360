"""BYS360_DEFECT_AH_EMBEDDED_SOURCE_SHA_PREPARE_SIDE_CONTRACT

Regression contract for the PREPARE-side half of Defect AH's selected
remediation (embed the authoritative release source SHA INSIDE the release
package before integrity hashes are finalized). The BUILD-side half
(scripts/release/build_bys360_safe_release.py: EMBEDDED_SOURCE_SHA_FILENAME,
write_embedded_source_sha(), verify_package()'s embedded/sidecar
cross-check) is proven in tests/release/test_build_bys360_safe_release.py.

This file proves scripts/windows/prepare_bys360_candidate.ps1's new
Test-EmbeddedSourceSha (Phase 4b, runs immediately after extraction, before
the extracted-candidate secret re-scan):

  1. reads the real, on-disk RELEASE_SOURCE_SHA.txt from an extracted
     candidate tree (not a mock, not a source-text assertion)
  2. fails closed (Phase SOURCE_SHA_FAILED) when that file is missing
  3. fails closed when its content is not a valid 40-hex-character SHA
  4. fails closed when it disagrees with the sidecar manifest's claimed
     source_sha ($Script:Receipt.SOURCE_SHA, as Test-PackageManifest would
     have set it) -- the exact gap this defect closes: before this fix,
     nothing on the prepare side ever compared the sidecar against
     anything independently verifiable
  5. fails closed when -ExpectedSourceSha is supplied and disagrees with
     the embedded value
  6. succeeds and makes the embedded value authoritative
     ($Script:Receipt.SOURCE_SHA overwritten with it) when everything
     agrees

Testability note: prepare_bys360_candidate.ps1 gained a dot-source guard
(`if ($MyInvocation.InvocationName -ne '.') { ... Main ... }`), the exact
same pattern already established in cutover_bys360_candidate.ps1 (see
tests/quality/test_cutover_stale_process_release_binding_contract_v1.py's
own testability note), purely so this pure, parameterized function can be
loaded and called in isolation without ever invoking Main() (which needs
real PostgreSQL / a real venv / a real HTTP health boot). The two mandatory
params (-PackagePath, -ExpectedPackageSha256) still need dummy values at
dot-source time (PowerShell binds param() on load regardless of
dot-sourcing); -DeployLogsRoot is pointed at a disposable tmp dir so
Invoke-FailClosed's FAILURE_RECEIPT.txt writes never touch the real
C:\\bys360\\deploy_logs.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
PS_EXE = shutil.which("pwsh") or shutil.which("powershell")
PREPARE_SCRIPT = ROOT / "scripts" / "windows" / "prepare_bys360_candidate.ps1"
CUTOVER_SCRIPT = ROOT / "scripts" / "windows" / "cutover_bys360_candidate.ps1"

_VALID_SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e"
assert len(_VALID_SHA) == 40


def _require_ps() -> str:
    if not PS_EXE:
        pytest.skip("PowerShell CLI bulunamadi; mock/dry-run dogrulama atlandi.")
    return PS_EXE


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:  # noqa: F811 - established pattern, see cutover Z tests
    d = Path(tempfile.mkdtemp(prefix="bys360_prepare_embedded_sha_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_ps_snippet(body: str, timeout: int = 30) -> subprocess.CompletedProcess:
    exe = _require_ps()
    return subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", body],
        capture_output=True, text=True, timeout=timeout, check=False,
    )


def _dot_source_prefix(deploy_logs_root: Path) -> str:
    return (
        ". " + _ps_single_quote(str(PREPARE_SCRIPT))
        + " -PackagePath 'dummy_test_package.zip'"
        + " -ExpectedPackageSha256 " + ("a" * 64)
        + " -DeployLogsRoot " + _ps_single_quote(str(deploy_logs_root))
        + "\n"
    )


# ---------------------------------------------------------------------------
# Static: script parses cleanly; dot-source guard loads the function without
# running Main.
# ---------------------------------------------------------------------------


def test_prepare_script_parses_with_zero_syntax_errors() -> None:
    exe = _require_ps()
    script = (
        "$e=$null;$t=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        f"'{PREPARE_SCRIPT}', [ref]$t, [ref]$e);"
        "Write-Output $e.Count"
    )
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "0", f"parse hatasi: {result.stdout} {result.stderr}"


def test_dot_sourcing_loads_embedded_sha_function_without_running_main(tmp_path: Path) -> None:
    body = _dot_source_prefix(tmp_path) + r"""
Write-Output ("FUNC=" + (Test-Path Function:\Test-EmbeddedSourceSha))
Write-Output "DOT_SOURCE_COMPLETED_WITHOUT_MAIN"
"""
    result = _run_ps_snippet(body)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "FUNC=True" in result.stdout
    assert "DOT_SOURCE_COMPLETED_WITHOUT_MAIN" in result.stdout
    # Main() would try Test-HostPrerequisites (real host checks) and log
    # "Phase 1/16" long before anything else -- its total absence here is
    # itself evidence Main() never ran.
    assert "Phase 1/16" not in result.stdout


def test_main_calls_test_embedded_source_sha_right_after_extraction() -> None:
    """Static source-contract check: locks in that Main() actually wires the
    new phase in, immediately after Expand-CandidatePackage and before the
    secret re-scan -- not merely defined-but-unused."""
    text = PREPARE_SCRIPT.read_text(encoding="utf-8")
    main_body = text.split("function Main {", 1)[1].split("\n# BYS360 DEFECT AH", 1)[0]
    assert "Test-EmbeddedSourceSha" in main_body
    assert (
        main_body.index("Expand-CandidatePackage")
        < main_body.index("Test-EmbeddedSourceSha")
        < main_body.index("Test-CandidateExtractedSecretScan")
    )


# ---------------------------------------------------------------------------
# Test-EmbeddedSourceSha: real filesystem, no mocks.
# ---------------------------------------------------------------------------


def _run_embedded_check(
    tmp_path: Path,
    *,
    embedded_content: str | None,
    sidecar_sha: str,
    expected_source_sha: str | None = None,
) -> subprocess.CompletedProcess:
    candidate_dir = tmp_path / "candidate"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    if embedded_content is not None:
        (candidate_dir / "RELEASE_SOURCE_SHA.txt").write_text(embedded_content, encoding="utf-8")

    expected_arg = f" -ExpectedSourceSha {_ps_single_quote(expected_source_sha)}" if expected_source_sha else ""
    body = (
        ". " + _ps_single_quote(str(PREPARE_SCRIPT))
        + " -PackagePath 'dummy_test_package.zip'"
        + " -ExpectedPackageSha256 " + ("a" * 64)
        + " -DeployLogsRoot " + _ps_single_quote(str(tmp_path / "deploy_logs"))
        + expected_arg
        + "\n"
        + f"$Script:Receipt.SOURCE_SHA = {_ps_single_quote(sidecar_sha)}\n"
        + "try {\n"
        + f"    $result = Test-EmbeddedSourceSha -CandidateDir {_ps_single_quote(str(candidate_dir))}\n"
        + '    Write-Output ("RESULT=OK:" + $result)\n'
        + '    Write-Output ("RECEIPT_SOURCE_SHA=" + $Script:Receipt.SOURCE_SHA)\n'
        + "} catch {\n"
        + '    Write-Output ("RESULT=FAIL:" + $_.Exception.Message)\n'
        + "}\n"
    )
    return _run_ps_snippet(body)


def test_missing_embedded_file_fails_closed(tmp_path: Path) -> None:
    result = _run_embedded_check(tmp_path, embedded_content=None, sidecar_sha=_VALID_SHA)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT=FAIL:" in result.stdout
    assert "SOURCE_SHA_FAILED" in result.stdout
    assert "RELEASE_SOURCE_SHA.txt" in result.stdout


def test_invalid_format_embedded_content_fails_closed(tmp_path: Path) -> None:
    result = _run_embedded_check(tmp_path, embedded_content="not-a-real-sha\n", sidecar_sha=_VALID_SHA)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT=FAIL:" in result.stdout
    assert "SOURCE_SHA_FAILED" in result.stdout


def test_sidecar_vs_embedded_mismatch_fails_closed(tmp_path: Path) -> None:
    """The core AH proof on the prepare side: an embedded value that
    disagrees with what the sidecar manifest claimed (simulating a sidecar
    tampered independently of the ZIP) must be rejected, not silently
    trusted."""
    other_sha = "f" * 40
    result = _run_embedded_check(tmp_path, embedded_content=_VALID_SHA + "\n", sidecar_sha=other_sha)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT=FAIL:" in result.stdout
    assert "SOURCE_SHA_FAILED" in result.stdout
    assert _VALID_SHA in result.stdout
    assert other_sha in result.stdout


def test_matching_sidecar_and_embedded_succeeds_and_becomes_authoritative(tmp_path: Path) -> None:
    result = _run_embedded_check(tmp_path, embedded_content=_VALID_SHA + "\n", sidecar_sha=_VALID_SHA)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert f"RESULT=OK:{_VALID_SHA}" in result.stdout
    assert f"RECEIPT_SOURCE_SHA={_VALID_SHA}" in result.stdout


def test_embedded_content_is_trimmed_and_lowercased(tmp_path: Path) -> None:
    """Whitespace/newlines/mixed-case in the embedded file must not cause a
    spurious mismatch -- matches how build_bys360_safe_release.py writes it
    (lowercase git SHA + trailing newline) and how the sidecar's own value
    is compared."""
    result = _run_embedded_check(
        tmp_path, embedded_content="  " + _VALID_SHA.upper() + "  \r\n", sidecar_sha=_VALID_SHA
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert f"RESULT=OK:{_VALID_SHA}" in result.stdout


def test_wrong_expected_source_sha_fails_closed(tmp_path: Path) -> None:
    result = _run_embedded_check(
        tmp_path, embedded_content=_VALID_SHA + "\n", sidecar_sha=_VALID_SHA, expected_source_sha="b" * 40
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "RESULT=FAIL:" in result.stdout
    assert "SOURCE_SHA_FAILED" in result.stdout
    assert "ExpectedSourceSha" in result.stdout


def test_correct_expected_source_sha_succeeds(tmp_path: Path) -> None:
    result = _run_embedded_check(
        tmp_path, embedded_content=_VALID_SHA + "\n", sidecar_sha=_VALID_SHA, expected_source_sha=_VALID_SHA
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert f"RESULT=OK:{_VALID_SHA}" in result.stdout


# ---------------------------------------------------------------------------
# Z compatibility: cutover_bys360_candidate.ps1 must remain untouched by
# this AH change and must still consume CANDIDATE_READY.json's SOURCE_SHA
# field exactly as before -- the field NAME never changed, only where its
# VALUE is authenticated from (embedded, not sidecar) on the prepare side.
# ---------------------------------------------------------------------------


def test_cutover_still_reads_candidate_ready_source_sha_field_unchanged() -> None:
    text = CUTOVER_SCRIPT.read_text(encoding="utf-8")
    assert "$receipt.SOURCE_SHA -ne $CandidateSourceSha" in text
    assert "$Script:Receipt.SOURCE_SHA = $manifest.source_sha" not in text  # cutover never wrote this itself


def test_versionz_loopback_release_identity_contract_still_present() -> None:
    """AF/Z chain compatibility: app/routes.py's loopback-gated /versionz
    release-identity fields (added in Defect AF, consumed by cutover's
    Test-ReleaseIdentityBinding) were not touched or weakened by AH."""
    routes_text = (ROOT / "app" / "routes.py").read_text(encoding="utf-8")
    assert "_bys360_request_is_from_loopback" in routes_text
    assert "orig_remote_addr" in routes_text
