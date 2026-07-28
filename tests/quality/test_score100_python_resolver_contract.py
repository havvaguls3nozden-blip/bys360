"""BYS360 Phase 6 dependency-audit closure -- Score100 Python resolver contract.

Real ``powershell.exe`` subprocess invocations of the actual
``Resolve-BysPython`` function in
``scripts/windows/repair_bys360_score100_quality_gate_v1.ps1`` (dot-sourced,
so only function definitions load -- the gate's own main execution body is
never triggered by these tests, see the ``BYS360_SCORE100_DOT_SOURCE_GUARD``
in that file). No network access is used anywhere in this file: "PATH
python" scenarios use a real, already-installed, self-contained CPython
3.12 interpreter hardlinked into an isolated temp directory, never
downloaded or installed on the fly.

Windows-only (the wrapper itself is a .ps1 file); skipped on other
platforms or when powershell.exe is unavailable.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts" / "windows" / "repair_bys360_score100_quality_gate_v1.ps1"
CANONICAL_PYTHON = Path(r"C:\bys360\project\.venv\Scripts\python.exe")

_POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")

pytestmark = [
    pytest.mark.ci_safe,
    pytest.mark.skipif(sys.platform != "win32", reason="Score100 wrapper is a Windows PowerShell script"),
    pytest.mark.skipif(_POWERSHELL is None, reason="powershell.exe not available on PATH"),
]


def _powershell_exe() -> str:
    assert _POWERSHELL is not None  # guaranteed by the module-level skipif above
    return _POWERSHELL


def _standalone_base_python() -> Path | None:
    """Locate a real, standalone (non-venv, no pyvenv.cfg dependency) CPython
    3.12 install to hardlink for PATH-only resolver scenarios, by reading it
    out of the canonical venv's own pyvenv.cfg ``executable=`` line -- this
    machine's actual base interpreter, not a guess."""
    cfg = CANONICAL_PYTHON.parent.parent / "pyvenv.cfg"
    if not cfg.is_file():
        return None
    for line in cfg.read_text(encoding="utf-8").splitlines():
        if line.strip().lower().startswith("executable"):
            _, _, value = line.partition("=")
            candidate = Path(value.strip())
            if candidate.is_file():
                return candidate
    return None


def _run_resolver(
    *,
    root: Path,
    explicit_python: str = "",
    canonical_sibling: str = r"C:\nonexistent_bys360_sibling\python.exe",
    required_major_minor: str = "3.12",
    env_overrides: dict[str, str] | None = None,
    clear_env: tuple[str, ...] = (),
    path_override: str | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    ps_command = (
        # BYS360 Phase 10F: PowerShell 5.1's stdout byte encoding for a piped
        # invocation is ambient/unstable (observed as both ibm857 and UTF-8
        # across sessions on this machine); pin it to BOM-less UTF-8 so the
        # Python side's explicit encoding="utf-8" below always matches.
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        f". '{WRAPPER}'; "
        f"$r = Resolve-BysPython -Root '{root}' -ExplicitPythonPath '{explicit_python}' "
        f"-CanonicalSiblingPythonPath '{canonical_sibling}' -RequiredMajorMinor '{required_major_minor}'; "
        "if ($r) { "
        "Write-Output ('RESOLVED_SOURCE=' + $r.Source); "
        "Write-Output ('RESOLVED_PATH=' + $r.Path); "
        "Write-Output ('RESOLVED_VERSION=' + $r.Version) "
        "}"
    )
    env = os.environ.copy()
    for key in clear_env:
        env.pop(key, None)
    if env_overrides:
        env.update(env_overrides)
    if path_override is not None:
        env["Path"] = path_override
        env["PATH"] = path_override
    proc = subprocess.run(
        [_powershell_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        encoding="utf-8",
        env=env,
        timeout=timeout,
    )
    return proc


def _windows_system_path_entry() -> str:
    system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
    return f"{system_root}\\System32"


# --- Test A: explicit -PythonPath wins ---


def test_explicit_python_path_is_selected_when_valid() -> None:
    if not CANONICAL_PYTHON.is_file():
        pytest.skip("canonical venv python not present on this machine")

    proc = _run_resolver(
        root=ROOT,
        explicit_python=str(CANONICAL_PYTHON),
        canonical_sibling=r"C:\nonexistent_bys360_sibling\python.exe",
        clear_env=("BYS360_CANONICAL_PYTHON",),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESOLVED_SOURCE=explicit" in proc.stdout
    assert f"RESOLVED_PATH={CANONICAL_PYTHON}" in proc.stdout


# --- Test B: BYS360_CANONICAL_PYTHON env var wins over repo-venv/sibling ---


def test_env_var_python_is_selected_when_valid() -> None:
    if not CANONICAL_PYTHON.is_file():
        pytest.skip("canonical venv python not present on this machine")

    proc = _run_resolver(
        root=ROOT,
        explicit_python="",
        canonical_sibling=r"C:\nonexistent_bys360_sibling\python.exe",
        env_overrides={"BYS360_CANONICAL_PYTHON": str(CANONICAL_PYTHON)},
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESOLVED_SOURCE=env" in proc.stdout
    assert f"RESOLVED_PATH={CANONICAL_PYTHON}" in proc.stdout


# --- Test C: no repo-venv, canonical sibling present -> selected ---


def test_canonical_sibling_is_selected_when_repo_has_no_venv() -> None:
    if not CANONICAL_PYTHON.is_file():
        pytest.skip("canonical venv python not present on this machine")

    proc = _run_resolver(
        root=ROOT,  # this worktree has no .venv/venv of its own
        explicit_python="",
        canonical_sibling=str(CANONICAL_PYTHON),
        clear_env=("BYS360_CANONICAL_PYTHON",),
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESOLVED_SOURCE=canonical-sibling" in proc.stdout
    assert f"RESOLVED_PATH={CANONICAL_PYTHON}" in proc.stdout


# --- Test D: wrong-version explicit candidate must fail closed, not silently pass ---


def test_wrong_version_explicit_candidate_fails_closed(tmp_path: Path) -> None:
    """A real but wrong-major.minor interpreter must be rejected outright --
    proves the resolver does not silently accept version drift."""
    wrong_version_python = _find_non_312_python()
    if wrong_version_python is None:
        pytest.skip("no non-3.12 Python interpreter available on this machine to test against")

    proc = _run_resolver(
        root=tmp_path,
        explicit_python=str(wrong_version_python),
        canonical_sibling=r"C:\nonexistent_bys360_sibling\python.exe",
        clear_env=("BYS360_CANONICAL_PYTHON",),
    )

    assert proc.returncode == 6
    assert "SCORE100_PYTHON_RESOLUTION_FAILED" in proc.stdout
    assert "SCORE100_PYTHON_UNAVAILABLE" in proc.stdout
    assert "VERSION_MISMATCH" in proc.stdout
    assert "RESOLVED_PATH=" not in proc.stdout


def _find_non_312_python() -> Path | None:
    for candidate_dir in (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python",):
        if not candidate_dir.is_dir():
            continue
        for sub in candidate_dir.iterdir():
            exe = sub / "python.exe"
            if exe.is_file() and "312" not in sub.name and "3.12" not in sub.name:
                return exe
    return None


# --- Test E: only a validated PATH python is available (CI-like: setup-python) ---


def test_path_only_validated_python_is_selected(tmp_path: Path) -> None:
    base_python = _standalone_base_python()
    if base_python is None:
        pytest.skip("could not locate a standalone base CPython to hardlink for PATH test")

    isolated_dir = tmp_path / "path_only_python"
    isolated_dir.mkdir()
    linked = isolated_dir / "python.exe"
    try:
        os.link(base_python, linked)
    except OSError:
        pytest.skip("hardlink not supported for this base python on this filesystem")

    empty_root = tmp_path / "no_venv_project"
    empty_root.mkdir()

    isolated_path = f"{isolated_dir};{_windows_system_path_entry()}"
    proc = _run_resolver(
        root=empty_root,
        explicit_python="",
        canonical_sibling=r"C:\nonexistent_bys360_sibling\python.exe",
        clear_env=("BYS360_CANONICAL_PYTHON",),
        path_override=isolated_path,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESOLVED_SOURCE=validated-path" in proc.stdout
    assert f"RESOLVED_PATH={linked}" in proc.stdout


# --- Test E2: same as Test E, but the path deliberately contains non-ASCII
# characters chosen independently of the real OS account name. Test E's
# tmp_path happens to expose a PowerShell/subprocess text-encoding mismatch
# only on machines whose Windows username contains non-ASCII characters
# (see the explicit UTF-8 handling in _run_resolver); this test makes that
# same guarantee -- the resolver reports the exact resolved path byte-for-
# character correctly -- deterministic on any machine or CI runner. ---


def test_path_only_resolved_path_preserves_non_ascii_characters(tmp_path: Path) -> None:
    base_python = _standalone_base_python()
    if base_python is None:
        pytest.skip("could not locate a standalone base CPython to hardlink for PATH test")

    isolated_dir = tmp_path / "pythön_çözümleyici_ıığşü_test"
    isolated_dir.mkdir()
    linked = isolated_dir / "python.exe"
    try:
        os.link(base_python, linked)
    except OSError:
        pytest.skip("hardlink not supported for this base python on this filesystem")

    empty_root = tmp_path / "no_venv_project"
    empty_root.mkdir()

    isolated_path = f"{isolated_dir};{_windows_system_path_entry()}"
    proc = _run_resolver(
        root=empty_root,
        explicit_python="",
        canonical_sibling=r"C:\nonexistent_bys360_sibling\python.exe",
        clear_env=("BYS360_CANONICAL_PYTHON",),
        path_override=isolated_path,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESOLVED_SOURCE=validated-path" in proc.stdout
    assert f"RESOLVED_PATH={linked}" in proc.stdout


# --- Negative: nothing usable anywhere -> explicit fail-closed, no global fallback ---


def test_no_usable_candidate_fails_closed_with_no_silent_fallback(tmp_path: Path) -> None:
    empty_root = tmp_path / "isolated_project"
    empty_root.mkdir()

    proc = _run_resolver(
        root=empty_root,
        explicit_python="",
        canonical_sibling=r"C:\nonexistent_bys360_sibling\python.exe",
        clear_env=("BYS360_CANONICAL_PYTHON",),
        path_override=_windows_system_path_entry(),
    )

    assert proc.returncode == 6
    assert "SCORE100_PYTHON_UNAVAILABLE" in proc.stdout
    assert "RESOLVED_PATH=" not in proc.stdout


# --- Wrapper stays parseable and dot-sourceable (no accidental main-body execution) ---


def test_wrapper_script_is_valid_powershell_syntax() -> None:
    ps_command = (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        "$errors = $null; $tokens = $null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{WRAPPER}', [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Output $_.Message }; exit 1 } else { exit 0 }"
    )
    proc = subprocess.run(
        [_powershell_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_dot_sourcing_wrapper_does_not_execute_main_gate_body(tmp_path: Path) -> None:
    """Dot-sourcing must only define functions; it must not attempt to
    resolve a project root, invoke Python, or print the gate banner."""
    ps_command = (
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
        f". '{WRAPPER}'; Write-Output 'DOT_SOURCE_OK'"
    )
    proc = subprocess.run(
        [_powershell_exe(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_command],
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "DOT_SOURCE_OK" in proc.stdout
    assert "BYS360 SCORE 100 QUALITY GATE V1 başlıyor" not in proc.stdout
