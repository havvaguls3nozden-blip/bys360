"""BYS360 Windows production startup UTF-8 stdio hardening regression tests.

Root cause (proven directly on the live Windows Server 2019 Scheduled Task
"BYS360 Live Waitress 80", 83f12fc release): under a Windows Scheduled Task
with redirected stdout, Python's stdio codec defaulted to the system ANSI
codepage (commonly cp1252). run_server.py's own startup print contains
Turkish characters ("BYS360 baslatiliyor" -- "s," is U+015F), and cp1252
cannot encode it, so the print itself raised UnicodeEncodeError and killed
the process before Waitress ever bound the port. The task showed as
Running; the process was already dead; health checks failed; a controlled
rollback correctly returned to the previous production release.

run_server.py now reconfigures sys.stdout/sys.stderr to UTF-8 as the very
first thing it does (`_ensure_utf8_stdio()`, called before `from app import
create_app`), fixing every subsequent print/log call in the process, not
just this one message -- and failing safe (never raising) if reconfigure
itself is unavailable for a given stream.

These tests prove the fix WITHOUT starting a real app, binding any port
(80 or otherwise), or requiring Windows: `_ensure_utf8_stdio` is extracted
directly from the real run_server.py source via `ast` (so importing/execing
it never triggers `app = create_app()`), and exercised both in-process
(against a deterministic, forced cp1252 stream) and via a real subprocess
(with PYTHONIOENCODING forced to cp1252, which -- unlike relying on OS
locale -- deterministically reproduces the failure mode on any platform).
"""

from __future__ import annotations

import ast
import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
RUN_SERVER_PATH = ROOT / "run_server.py"

# The exact startup message shape from run_server.py -- contains Turkish
# characters that cp1252 cannot encode (this is the literal reproduction
# of the real production crash, not a synthetic stand-in).
STARTUP_MESSAGE = "BYS360 başlatılıyor (production): http://0.0.0.0:80"


def _extract_ensure_utf8_stdio_source() -> str:
    """Returns the exact source text of _ensure_utf8_stdio() as it exists
    in the real run_server.py right now -- so a regression in the actual
    file (not a copy) is what these tests exercise."""
    source = RUN_SERVER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(RUN_SERVER_PATH))
    func_node = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_ensure_utf8_stdio"
    )
    return ast.get_source_segment(source, func_node) or ""


def _load_ensure_utf8_stdio():
    """Execs ONLY the _ensure_utf8_stdio function body extracted from the
    real run_server.py, without ever triggering the module's own
    `app = create_app()` side effect."""
    namespace: dict = {"sys": sys}
    import contextlib
    namespace["contextlib"] = contextlib
    exec(_extract_ensure_utf8_stdio_source(), namespace)
    return namespace["_ensure_utf8_stdio"]


def test_run_server_calls_ensure_utf8_stdio_before_importing_app() -> None:
    """Static contract: the reconfigure call must run before `from app
    import create_app` -- app-factory bootstrap can itself print/log, and
    that must also be UTF-8-safe, not just this module's own message."""
    text = RUN_SERVER_PATH.read_text(encoding="utf-8")
    ensure_call_pos = text.index("_ensure_utf8_stdio()")
    import_app_pos = text.index("from app import create_app")
    assert ensure_call_pos < import_app_pos, (
        "_ensure_utf8_stdio() must be called before importing app "
        "(app-factory bootstrap output must also be UTF-8-safe)"
    )


def test_ensure_utf8_stdio_function_exists_and_is_defensive() -> None:
    source = _extract_ensure_utf8_stdio_source()
    assert source, "_ensure_utf8_stdio not found in run_server.py"
    assert "reconfigure" in source
    assert "AttributeError" in source and "ValueError" in source and "OSError" in source


def test_cp1252_stream_cannot_encode_startup_message_without_fix() -> None:
    """Negative control: proves the failure mode is real. A cp1252-encoded
    stream, untouched by the fix, must raise UnicodeEncodeError on the
    exact startup message shape -- otherwise the "fix" below wouldn't be
    proving anything."""
    fake_stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", write_through=True)
    with pytest.raises(UnicodeEncodeError):
        fake_stream.write(STARTUP_MESSAGE + "\n")


def test_ensure_utf8_stdio_reconfigures_forced_cp1252_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """The actual fix: after _ensure_utf8_stdio() runs against a forced
    cp1252 sys.stdout, writing the exact startup message must succeed."""
    ensure_utf8_stdio = _load_ensure_utf8_stdio()

    fake_stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", write_through=True)
    fake_stderr = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", write_through=True)
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    monkeypatch.setattr(sys, "stderr", fake_stderr)

    ensure_utf8_stdio()

    sys.stdout.write(STARTUP_MESSAGE + "\n")
    sys.stderr.write(STARTUP_MESSAGE + "\n")

    assert sys.stdout.encoding.lower().replace("-", "") == "utf8"
    assert sys.stderr.encoding.lower().replace("-", "") == "utf8"


def test_ensure_utf8_stdio_fails_safe_when_reconfigure_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stream with no .reconfigure() at all (e.g. some redirect/capture
    wrapper) must not crash startup -- the operator message must never be
    able to bring the app down by itself."""
    ensure_utf8_stdio = _load_ensure_utf8_stdio()

    class _NoReconfigureStream:
        def write(self, s: str) -> int:
            return len(s)

        def flush(self) -> None:
            pass

    monkeypatch.setattr(sys, "stdout", _NoReconfigureStream())
    monkeypatch.setattr(sys, "stderr", _NoReconfigureStream())

    ensure_utf8_stdio()  # must not raise


def _subprocess_harness_source() -> str:
    ensure_src = _extract_ensure_utf8_stdio_source()
    return (
        "import sys, contextlib\n"
        f"{ensure_src}\n"
        "_ensure_utf8_stdio()\n"
        f"print({STARTUP_MESSAGE!r})\n"
        "print('SUBPROCESS_STARTUP_PRINT_SUCCEEDED')\n"
    )


def test_subprocess_forced_cp1252_stdio_survives_startup_print(tmp_path: Path) -> None:
    """Real subprocess, real OS pipe. PYTHONIOENCODING=cp1252 deterministically
    forces Python's own initial stdio codec to cp1252 on ANY platform -- the
    same failure class as the Windows Scheduled Task's redirected console --
    without needing Windows or PYTHONUTF8/PYTHONIOENCODING to be set by the
    caller (proving run_server.py's own in-process fix is sufficient by
    itself, not merely relying on the installer's env vars)."""
    harness = tmp_path / "harness.py"
    harness.write_text(_subprocess_harness_source(), encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"
    env.pop("PYTHONUTF8", None)

    result = subprocess.run(
        [sys.executable, str(harness)],
        capture_output=True, text=True, timeout=30, env=env, check=False,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "SUBPROCESS_STARTUP_PRINT_SUCCEEDED" in result.stdout
    assert "UnicodeEncodeError" not in result.stderr


def test_subprocess_forced_cp1252_stdio_crashes_without_ensure_utf8_stdio(tmp_path: Path) -> None:
    """Negative control at the subprocess level: the SAME forced-cp1252
    environment, without calling _ensure_utf8_stdio() first, must actually
    reproduce UnicodeEncodeError -- confirming the prior test's PASS is
    because of the fix, not because the environment failed to force cp1252
    in the first place."""
    harness = tmp_path / "harness_broken.py"
    harness.write_text(f"print({STARTUP_MESSAGE!r})\n", encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"
    env.pop("PYTHONUTF8", None)

    result = subprocess.run(
        [sys.executable, str(harness)],
        capture_output=True, text=True, timeout=30, env=env, check=False,
    )
    assert result.returncode != 0
    assert "UnicodeEncodeError" in result.stderr


def test_subprocess_with_installer_style_env_vars_survives_startup_print(tmp_path: Path) -> None:
    """Proves the installer-generated env vars (PYTHONUTF8=1,
    PYTHONIOENCODING=utf-8) are independently sufficient too -- the second,
    process-level defense layer described in
    scripts/windows/install_bys360_live_waitress_80_task_v1.ps1."""
    harness = tmp_path / "harness_installer_env.py"
    harness.write_text(f"print({STARTUP_MESSAGE!r})\nprint('SUBPROCESS_STARTUP_PRINT_SUCCEEDED')\n", encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, str(harness)],
        capture_output=True, text=True, timeout=30, env=env, check=False,
    )
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "SUBPROCESS_STARTUP_PRINT_SUCCEEDED" in result.stdout
