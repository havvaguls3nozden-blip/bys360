"""Cross-language regression test for the wheelhouse identity contract.

Root cause this guards against (found and fixed 2026-08-25, real reproduction
on this host's Turkish system locale): PowerShell's default `Sort-Object`
uses culture-aware (linguistic) string comparison, while Python's `sorted()`
uses ordinal comparison. For the exact same 59 real wheel filenames, these
two orderings disagreed on exactly one file
(flask-3.1.3-py3-none-any.whl vs the flask_*-prefixed packages), which
silently changed scripts/windows/prepare_bys360_candidate.ps1's
independently-recomputed wheelhouse_identity_sha256 relative to
scripts/release/build_bys360_wheelhouse.py's canonical value -- a spurious
cross-host mismatch with zero actual integrity problem, but one that made
the "candidate independently re-verifies the manifest's claims" gate
unusable. Both sides must now use ordinal comparison; this test proves it
mechanically, in both languages, rather than trusting a code review.

Canonical contract (see scripts/release/build_bys360_wheelhouse.py's
wheelhouse_identity()): SHA256 over a UTF-8 text blob of
"<filename>:<sha256-hex-lowercase>\\n" lines, one per .whl file, filenames
sorted by ordinal (codepoint) comparison on the lowercased name, with a
trailing newline after the last line.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("powershell.exe") is None, reason="requires Windows PowerShell")

_CANDIDATE_SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts" / "windows" / "prepare_bys360_candidate.ps1"
)


def _python_identity(wheelhouse_dir: Path) -> str:
    files = sorted(wheelhouse_dir.glob("*.whl"), key=lambda p: p.name.lower())
    lines = [f"{f.name}:{hashlib.sha256(f.read_bytes()).hexdigest()}" for f in files]
    blob = "\n".join(lines) + "\n"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _powershell_identity(wheelhouse_dir: Path) -> str:
    """Invokes the REAL Get-WheelhouseIdentitySha256 function extracted
    from the actual shipped script (via AST), not a re-transcription --
    proves the shipped code, not a copy of it that could silently drift."""
    driver = f"""
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile('{_CANDIDATE_SCRIPT}', [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) {{ throw "parse errors in candidate script" }}
$funcAsts = $ast.FindAll({{ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }}, $true)
$target = $funcAsts | Where-Object {{ $_.Name -eq 'Get-WheelhouseIdentitySha256' }} | Select-Object -First 1
if (-not $target) {{ throw "Get-WheelhouseIdentitySha256 not found in candidate script" }}
Invoke-Expression $target.Extent.Text
Write-Output (Get-WheelhouseIdentitySha256 -WheelhouseDir '{wheelhouse_dir}')
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", driver],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"PowerShell identity computation failed: {result.stderr}"
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert lines, f"PowerShell produced no output: stdout={result.stdout!r} stderr={result.stderr!r}"
    return lines[-1]


def _make_wheel(wheelhouse_dir: Path, filename: str, content: bytes) -> None:
    (wheelhouse_dir / filename).write_bytes(content)


# ---------------------------------------------------------------------------
# A: normal fixture -> both languages must agree
# ---------------------------------------------------------------------------


def test_normal_fixture_python_and_powershell_agree(tmp_path):
    wh = tmp_path / "wheelhouse"
    wh.mkdir()
    _make_wheel(wh, "alpha-1.0.0-py3-none-any.whl", b"alpha content")
    _make_wheel(wh, "beta-2.0.0-py3-none-any.whl", b"beta content")
    _make_wheel(wh, "gamma-3.0.0-py3-none-any.whl", b"gamma content")

    assert _python_identity(wh) == _powershell_identity(wh)


# ---------------------------------------------------------------------------
# real bug repro: hyphen vs underscore at the same relative name position
# (exactly the flask-3.1.3 / flask_limiter class of collision)
# ---------------------------------------------------------------------------


def test_hyphen_vs_underscore_collision_python_and_powershell_agree(tmp_path):
    wh = tmp_path / "wheelhouse"
    wh.mkdir()
    _make_wheel(wh, "flask-3.1.3-py3-none-any.whl", b"flask core")
    _make_wheel(wh, "flask_limiter-3.5.0-py3-none-any.whl", b"flask limiter")
    _make_wheel(wh, "flask_login-0.6.3-py3-none-any.whl", b"flask login")
    _make_wheel(wh, "flask_migrate-4.0.7-py3-none-any.whl", b"flask migrate")

    py = _python_identity(wh)
    ps = _powershell_identity(wh)
    assert py == ps, (
        "This is the exact real-world collision class that caused the original "
        "cross-language mismatch (flask-3.1.3 vs flask_*) -- ordinal comparison "
        "must place 'flask-3.1.3' before every 'flask_*' entry on both sides."
    )


# ---------------------------------------------------------------------------
# B: filenames created in scrambled order -> identity must not depend on
# filesystem enumeration/creation order
# ---------------------------------------------------------------------------


def test_creation_order_does_not_affect_identity(tmp_path):
    wh1 = tmp_path / "wheelhouse_forward"
    wh1.mkdir()
    for name in ["zulu-1.0-py3-none-any.whl", "mike-1.0-py3-none-any.whl", "alpha-1.0-py3-none-any.whl"]:
        _make_wheel(wh1, name, name.encode())

    wh2 = tmp_path / "wheelhouse_reverse"
    wh2.mkdir()
    for name in ["alpha-1.0-py3-none-any.whl", "mike-1.0-py3-none-any.whl", "zulu-1.0-py3-none-any.whl"]:
        _make_wheel(wh2, name, name.encode())

    assert _python_identity(wh1) == _python_identity(wh2)
    assert _powershell_identity(wh1) == _powershell_identity(wh2)
    assert _python_identity(wh1) == _powershell_identity(wh1)


# ---------------------------------------------------------------------------
# D: tampered content -> identity must change
# ---------------------------------------------------------------------------


def test_tampered_wheel_content_changes_identity(tmp_path):
    wh = tmp_path / "wheelhouse"
    wh.mkdir()
    _make_wheel(wh, "alpha-1.0.0-py3-none-any.whl", b"original content")
    before_py = _python_identity(wh)
    before_ps = _powershell_identity(wh)

    (wh / "alpha-1.0.0-py3-none-any.whl").write_bytes(b"tampered content")
    after_py = _python_identity(wh)
    after_ps = _powershell_identity(wh)

    assert before_py != after_py
    assert before_ps != after_ps
    assert after_py == after_ps


# ---------------------------------------------------------------------------
# E: missing wheel -> identity changes (the count/set changes)
# ---------------------------------------------------------------------------


def test_missing_wheel_changes_identity(tmp_path):
    wh = tmp_path / "wheelhouse"
    wh.mkdir()
    _make_wheel(wh, "alpha-1.0.0-py3-none-any.whl", b"alpha")
    _make_wheel(wh, "beta-2.0.0-py3-none-any.whl", b"beta")
    full_identity = _python_identity(wh)

    (wh / "beta-2.0.0-py3-none-any.whl").unlink()
    partial_identity_py = _python_identity(wh)
    partial_identity_ps = _powershell_identity(wh)

    assert full_identity != partial_identity_py
    assert partial_identity_py == partial_identity_ps


# ---------------------------------------------------------------------------
# G: identity survives a real zip round-trip (matches how the wheelhouse
# actually travels: bundled into the release ZIP, then extracted into the
# candidate directory)
# ---------------------------------------------------------------------------


def test_identity_survives_zip_round_trip(tmp_path):
    import zipfile

    wh = tmp_path / "wheelhouse"
    wh.mkdir()
    _make_wheel(wh, "flask-3.1.3-py3-none-any.whl", b"flask core")
    _make_wheel(wh, "flask_limiter-3.5.0-py3-none-any.whl", b"flask limiter")
    _make_wheel(wh, "zzz_last-9.0.0-py3-none-any.whl", b"zzz")
    original_identity = _python_identity(wh)

    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for f in wh.iterdir():
            zf.write(f, arcname=f"wheelhouse/{f.name}")

    extracted = tmp_path / "extracted"
    extracted.mkdir()
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extracted)

    round_tripped_identity_py = _python_identity(extracted / "wheelhouse")
    round_tripped_identity_ps = _powershell_identity(extracted / "wheelhouse")

    assert round_tripped_identity_py == original_identity
    assert round_tripped_identity_ps == original_identity
