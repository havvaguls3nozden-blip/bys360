"""BYS360_DEFECT_Z_CUTOVER_STALE_PROCESS_RELEASE_BINDING_CONTRACT

Regression contract for Defect Z: scripts/windows/cutover_bys360_candidate.ps1
previously accepted ANY process listening on the expected port as proof the
new candidate was live, with no PID/path/freshness binding and no
comparison of the release identity the responding process actually reports
against the candidate the run intended to promote.

Root-cause architecture traced before any fix (see the final delivery
report for the full OLD_PROCESS_STOP_MECHANISM / PID_DISCOVERY / etc.
breakdown): Stop-LiveService (Phase 7/8) only WARNED if $AppPort was still
listening after Stop-ScheduledTask; Start-LiveService (Phase 15) accepted
"something is listening" as full success; GET /versionz existed but
returned no release identity at all; GET /readyz was never called anywhere
in the script.

Fix -- three independent, fail-closed bindings, all exercised directly here
against REAL local disposable resources (never a real Scheduled Task, never
real port 80, never a real PostgreSQL database, never the real
C:\\bys360\\project):
  1. Test-ProcessBinding -- PID owning a port must resolve to the EXACT
     expected executable path, its command line must reference
     run_server.py, and its process start time must be AFTER the
     supplied -NotBeforeUtc (proving freshness, not a stale leftover).
  2. Test-ReleaseIdentityBinding -- calls the now-extended GET /versionz
     and requires source_sha/migration_head to exactly match the intended
     candidate (see app/routes.py::_bys360_release_identity and
     tests/behavior/test_versionz_release_identity_contract.py for that
     half of the fix).
  3. Test-ReadinessGate -- calls GET /readyz and requires BOTH HTTP 200 AND
     body status=="ready".

Testability note: cutover_bys360_candidate.ps1 gained a dot-source guard
(`if ($MyInvocation.InvocationName -ne '.') { ... Main ... }`) purely so
these pure, parameterized functions can be loaded and called in isolation
without ever invoking Main() (which needs real PostgreSQL/Scheduled
Task/filesystem infrastructure this test suite must never touch). A
mandatory -CandidateSourceSha dummy value is still required at dot-source
time (PowerShell binds param() on load regardless of dot-sourcing), but
Main() itself is never called.
"""
from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
PS_EXE = shutil.which("pwsh") or shutil.which("powershell")
CUTOVER_SCRIPT = ROOT / "scripts" / "windows" / "cutover_bys360_candidate.ps1"

# A standalone, non-venv interpreter with no PEP-405 launcher/app-execution-
# -alias redirection -- sys.executable is NOT used here because pytest
# itself runs under this repo's own .venv (which IS such a launcher on this
# sandbox; see the launcher-redirection note on the "accepts" test below).
_STANDALONE_PYTHON_CANDIDATES = [
    Path.home() / "AppData" / "Local" / "Programs" / "Python" / name / "python.exe"
    for name in ("Python314", "Python313", "Python312", "Python311", "Python310")
]
SYSTEM_PYTHON = next((p for p in _STANDALONE_PYTHON_CANDIDATES if p.exists()), None)


def _require_ps() -> str:
    if not PS_EXE:
        pytest.skip("PowerShell CLI bulunamadi; mock/dry-run dogrulama atlandi.")
    return PS_EXE


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:  # noqa: F811 - kasitli olarak pytest'in yerlesik tmp_path'ini golgeler.
    """pytest'in yerlesik `tmp_path` fixture'i bu makinede kullanici adindaki
    Turkce karakterler nedeniyle AppData\\Local\\Temp\\pytest-of-... dizinini
    tarayamiyor -- established pattern, bkz. diger Y/Z test dosyalari."""
    d = Path(tempfile.mkdtemp(prefix="bys360_cutover_binding_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _run_ps_snippet(body: str, timeout: int = 30) -> subprocess.CompletedProcess:
    exe = _require_ps()
    return subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", body],
        capture_output=True, text=True, timeout=timeout, check=False,
    )


def _dot_source_prefix() -> str:
    """Cross-platform not: cutover_bys360_candidate.ps1'in dot-source anindaki
    (Main() cagrilmadan once, ust-seviye) $Script:DeployLogDir atamasi, kendi
    `-DeployLogsRoot` parametresinden BAGIMSIZ olarak sabit `C:\bys360\
    deploy_logs` yolunu kullanir -- gercek/kasitli bir production convention,
    degistirilmedi. test_installer_launcher_overwrite_guard_v1.py::
    _run_mocked_installer()'da zaten kanitlanmis olan ayni fake-C:-PSDrive
    koprusu burada da uygulanir (BYS360 DEFECT: bu dot-source prefix'i,
    Linux runner'inda "Cannot find drive" hatasiyla patliyordu cunku ayni
    koprude yoktu). Mount/unmount, dot-source'un kendisini sarar; testin
    kendi PowerShell govdesi (bu prefix'in sonrasina eklenir) hicbir C:\
    yoluna dokunmaz, sadece dot-source ile yuklenen saf fonksiyonlari
    (Test-ReadinessGate vb.) cagirir.

    Ikinci katman (BYS360 DEFECT, second-layer): Test-ProcessBinding ->
    Get-ListeningProcessOnPort, gercek/kasitli Windows-only Get-NetTCPConnection
    cmdlet'ini cagirir; Test-ReleaseIdentityBinding / Test-ReadinessGate,
    gercek/kasitli Windows'a ozgu `curl.exe` ikili adini cozer (Linux'ta
    gercek curl "curl" adiyla mevcuttur, "curl.exe" degil). Ikisi de gercek,
    degistirilmemis production convention'lardir. Get-Command ... yoksa
    (yalnizca Linux pwsh'ta), bu iki komut adi icin de ayni "sadece harness'ta
    kopru, production'da sifir degisiklik, gercek Windows'ta no-op" felsefesiyle
    dar kapsamli fonksiyon golgeleme (shim) eklenir:
      - Get-NetTCPConnection shim'i sahte bir sonuc UYDURMAZ; istenen
        LocalPort'a gercek bir TCP connect-probe yapar (System.Net.Sockets.
        TcpClient). Dinleyici yoksa $null doner (su an aktif tek testin --
        NO_LISTENER dali -- ihtiyaci budur). Bir dinleyici varsa, gercek ama
        Windows'a ozgu process-sahiplik (OwningProcess) semantiginin capraz
        platformda sadakatle uretilemeyecegini acikca belgeleyerek
        OwningProcess=$null donen uyumlu bir sekil doner -- bu dal, su an
        aktif (skip edilmemis) hicbir testte tetiklenmez.
        BYS360 DEFECT (third-layer harness portability, Linux-only): dinleyici
        yokken Windows'ta loopback yaniti sessizce zaman asimina ugrar (bu
        shim'in Wait(200)-> $false dalini tetikler), ama Linux'ta ayni durum
        neredeyse aninda TCP RST / "Connection refused" ile SONUCLANIR --
        ConnectAsync'in Task'i, 200ms zaman asimi dolmadan once Faulted
        durumuna gecer. .NET'in kendi Task.Wait(ms) sozlesmesi geregi, bir
        Faulted Task uzerinde Wait cagirmak $false DONDURMEZ, AggregateException
        FIRLATIR (dogrudan yerel olarak kanitlandi: zorla Faulted edilmis bir
        Task uzerinde Wait(200), Task.Status=Faulted iken MethodInvocationException
        icinde sarili gercek bir System.AggregateException firlatiyor). Bu shim'in
        eski hali yalnizca try/finally icindeydi (catch yoktu), bu yuzden bu
        AggregateException hicbir yerde yakalanmadan scriptblock'un disina
        sizip cagirani (Get-ListeningProcessOnPort -> Test-ProcessBinding)
        cokertiyordu -- tam olarak "PROBING_PORT olarak nothing-is-listening"
        senaryosunun Linux'taki gercek davranisi, ve tam olarak remote'ta
        gorulen "One or more errors occurred. (Connection refused)" hatasi.
        Asagidaki ic try/catch, YALNIZCA bu beklenen AggregateException'i
        NO_LISTENER anlamina gelecek sekilde $null'a cevirir (timeout dali ile
        ayni anlam); ConnectAsync'in tek govdesi bir baglanti denemesi
        oldugundan, bu Task'ten firlayabilecek her fault zaten aglar/soket
        kaynaklidir -- baska hicbir kod yolu bu Task icinde calismaz. Gercekten
        beklenmeyen (network-disi) hatalar bu catch bloguna hic girmez, cunku
        yalnizca Wait() cagrisini sarmalar; digerleri (ornegin disposal
        hatalari) disaridaki try/finally'e degismeden ulasir.
      - curl.exe shim'i saf bir yonlendiricidir (${function:curl.exe} = {
        & curl @args }); gercek curl'e TUM argumanlari degistirmeden iletir,
        hicbir HTTP yaniti uydurmaz -- testler yine gercek, tek kullanimlik
        yerel sahte sunucuya gercek istek atar."""
    return (
        r"""
$hasRealCDrive = $false
try { $hasRealCDrive = [bool](Test-Path -LiteralPath 'C:\') } catch { $hasRealCDrive = $false }
$FakeCDriveRoot = $null
if (-not $hasRealCDrive) {
    $FakeCDriveRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("bys360_fake_c_drive_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $FakeCDriveRoot | Out-Null
    New-PSDrive -Name 'C' -PSProvider FileSystem -Root $FakeCDriveRoot -Scope Global | Out-Null
}
"""
        + ". " + _ps_single_quote(str(CUTOVER_SCRIPT)) + " -CandidateSourceSha 'dummy_test_sha_for_dotsource_probe'\n"
        + r"""
if ($FakeCDriveRoot) {
    Remove-PSDrive -Name 'C' -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $FakeCDriveRoot -ErrorAction SilentlyContinue
}

if (-not (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) {
    ${function:Get-NetTCPConnection} = {
        param([int]$LocalPort, [string]$State, [string]$ErrorAction)
        $client = $null
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $connectTask = $client.ConnectAsync('127.0.0.1', $LocalPort)
            try {
                if ($connectTask.Wait(200) -and $client.Connected) {
                    return [PSCustomObject]@{ LocalPort = $LocalPort; State = 'Listen'; OwningProcess = $null }
                }
                return $null
            } catch [System.AggregateException] {
                # ConnectAsync's Task faulted (e.g. immediate ECONNREFUSED on
                # Linux) before the 200ms timeout elapsed -- Task.Wait(ms)
                # throws in that case rather than returning $false. Same
                # meaning as the timeout branch above: nothing is listening.
                return $null
            }
        } finally {
            if ($client) { $client.Dispose() }
        }
    }
}

if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
    # BYS360 DEFECT (second-layer harness portability): a bare `curl` call
    # is NOT safe here -- Windows PowerShell (5.1) ships a built-in alias
    # `curl` -> Invoke-WebRequest, which would silently hijack this shim on
    # a machine where both the alias and a real curl happen to coexist
    # (confirmed by direct reproduction: `& curl --version` resolved to
    # Invoke-WebRequest and failed trying to parse "--version" as a URI).
    # -CommandType Application restricts resolution to the real external
    # executable, bypassing any Alias/Function/Cmdlet of the same bare name.
    $realCurlCommand = Get-Command curl -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($realCurlCommand) {
        ${function:curl.exe} = { & $realCurlCommand.Source @args }.GetNewClosure()
    }
}
"""
    )


# ---------------------------------------------------------------------------
# Static: the script parses cleanly and the dot-source guard actually works
# (loads functions, never runs Main, never calls `exit`).
# ---------------------------------------------------------------------------


def test_cutover_script_parses_with_zero_syntax_errors() -> None:
    exe = _require_ps()
    script = (
        "$e=$null;$t=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        f"'{CUTOVER_SCRIPT}', [ref]$t, [ref]$e);"
        "Write-Output $e.Count"
    )
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "0", f"parse hatasi: {result.stdout} {result.stderr}"


def test_dot_sourcing_loads_binding_functions_without_running_main() -> None:
    body = _dot_source_prefix() + r"""
Write-Output ("FUNC_PROCESS=" + (Test-Path Function:\Test-ProcessBinding))
Write-Output ("FUNC_RELEASE=" + (Test-Path Function:\Test-ReleaseIdentityBinding))
Write-Output ("FUNC_READY=" + (Test-Path Function:\Test-ReadinessGate))
Write-Output ("FUNC_LISTEN=" + (Test-Path Function:\Get-ListeningProcessOnPort))
Write-Output "DOT_SOURCE_COMPLETED_WITHOUT_MAIN"
"""
    result = _run_ps_snippet(body)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "FUNC_PROCESS=True" in result.stdout
    assert "FUNC_RELEASE=True" in result.stdout
    assert "FUNC_READY=True" in result.stdout
    assert "FUNC_LISTEN=True" in result.stdout
    assert "DOT_SOURCE_COMPLETED_WITHOUT_MAIN" in result.stdout
    # Main() would try to verify a real CANDIDATE_READY.json and fail loudly
    # with RECEIPT_INVALID long before anything else -- its total absence
    # here is itself evidence Main() never ran.
    assert "RECEIPT_INVALID" not in result.stdout
    assert "Phase 1/20" not in result.stdout


def test_main_wires_the_three_new_bindings_and_stop_service_fails_closed() -> None:
    """Static source-contract check: locks in that Main() actually calls
    the three new gates in order, and that Stop-LiveService no longer just
    warns on a stale listener."""
    text = CUTOVER_SCRIPT.read_text(encoding="utf-8")
    main_body = text.split("function Main {", 1)[1].split("\ntry {", 1)[0]
    assert "Invoke-ReleaseIdentityCheck" in main_body
    assert "Invoke-ReadinessCheck" in main_body
    assert main_body.index("Start-LiveService") < main_body.index("Invoke-ReleaseIdentityCheck") < main_body.index("Invoke-ReadinessCheck")

    stop_service_body = text.split("function Stop-LiveService {", 1)[1].split("\nfunction ", 1)[0]
    assert "Invoke-FailClosed" in stop_service_body
    assert 'Level "WARN"' not in stop_service_body, (
        "Stop-LiveService must fail closed on a lingering listener, not merely warn"
    )


# ---------------------------------------------------------------------------
# Test-ProcessBinding: real local disposable processes, never real port 80.
# ---------------------------------------------------------------------------


def _spawn_listening_process(python_exe: Path, port: int, tmp_path: Path) -> subprocess.Popen:
    script = tmp_path / f"listener_{port}.py"
    script.write_text(
        "import socket, time\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
        "s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
        f"s.bind(('127.0.0.1', {port}))\n"
        "s.listen(1)\n"
        "time.sleep(20)\n",
        encoding="utf-8",
    )
    proc = subprocess.Popen([str(python_exe), str(script)], cwd=str(tmp_path))
    for _ in range(50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            try:
                probe.connect(("127.0.0.1", port))
                return proc
            except OSError:
                time.sleep(0.1)
    proc.kill()
    pytest.fail(f"Disposable listener on port {port} never came up.")


def test_process_binding_accepts_the_genuinely_fresh_expected_process(tmp_path: Path) -> None:
    """Uses a standalone Python install rather than sys.executable or the
    project's own .venv python.exe: both are backed, on this dev sandbox,
    by a Windows Store Python install via a PEP-405 venv launcher, and
    Win32_Process -- correctly, since it reports the OS-level resolved
    image, not a self-reported string -- shows the ultimate WindowsApps
    target rather than the venv's own literal Scripts\\python.exe path.
    That is an environment-specific launcher-redirection quirk of this
    sandbox, not a defect in Test-ProcessBinding's comparison logic (which
    is exactly right to trust the OS-authoritative path, not a spoofable
    self-report). A standalone, non-venv interpreter has no such
    redirection and proves the same matching logic unambiguously."""
    if SYSTEM_PYTHON is None:
        pytest.skip("No standalone (non-venv) Python install found on this host; process-binding match test skipped.")
    port = _free_port()
    before_spawn_utc_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 5))
    proc = _spawn_listening_process(SYSTEM_PYTHON, port, tmp_path)
    try:
        body = _dot_source_prefix() + f"""
$notBefore = [datetime]::ParseExact('{before_spawn_utc_iso}', 'yyyy-MM-ddTHH:mm:ss', $null)
$result = Test-ProcessBinding -Port {port} -ExpectedExecutablePath '{SYSTEM_PYTHON}' -ExpectedCommandLineFragment 'listener_{port}.py' -NotBeforeUtc $notBefore
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=True" in result.stdout, result.stdout
        assert "REASON=OK" in result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_process_binding_rejects_a_process_with_the_wrong_executable_path(tmp_path: Path) -> None:
    """The real Defect Z scenario: SOMETHING is listening, but it is not
    our expected venv python.exe -- a different, real, independently
    verifiable interpreter binary on this same host."""
    if SYSTEM_PYTHON is None:
        pytest.skip("No standalone (non-venv) Python install found on this host; wrong-path test skipped.")
    port = _free_port()
    proc = _spawn_listening_process(SYSTEM_PYTHON, port, tmp_path)
    try:
        body = _dot_source_prefix() + f"""
$result = Test-ProcessBinding -Port {port} -ExpectedExecutablePath 'C:\\bys360\\project\\.venv\\Scripts\\python.exe' -ExpectedCommandLineFragment 'listener_{port}.py'
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=False" in result.stdout, result.stdout
        assert "REASON=EXECUTABLE_PATH_MISMATCH" in result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_process_binding_rejects_a_stale_process_that_predates_the_start_invocation(tmp_path: Path) -> None:
    """THE stale-process negative proof required by Defect Z: the correct
    executable, the correct command line -- but it started BEFORE this
    run's own Start-ScheduledTask invocation, so it must be rejected as
    stale, exactly the scenario that previously slipped through as
    accepted success."""
    if SYSTEM_PYTHON is None:
        pytest.skip("No standalone (non-venv) Python install found on this host; stale-process test skipped.")
    port = _free_port()
    proc = _spawn_listening_process(SYSTEM_PYTHON, port, tmp_path)
    try:
        # Test-ProcessBinding deliberately allows a 2-second clock-skew
        # tolerance around -NotBeforeUtc; sleep well past it so this test
        # unambiguously exercises genuine staleness, not tolerance noise.
        time.sleep(5)
        after_spawn_utc_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time()))
        body = _dot_source_prefix() + f"""
$notBefore = [datetime]::ParseExact('{after_spawn_utc_iso}', 'yyyy-MM-ddTHH:mm:ss', $null)
$result = Test-ProcessBinding -Port {port} -ExpectedExecutablePath '{SYSTEM_PYTHON}' -ExpectedCommandLineFragment 'listener_{port}.py' -NotBeforeUtc $notBefore
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=False" in result.stdout, result.stdout
        assert "REASON=STALE_PROCESS_PREDATES_START" in result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_process_binding_rejects_when_nothing_is_listening() -> None:
    port = _free_port()
    body = _dot_source_prefix() + f"""
$result = Test-ProcessBinding -Port {port} -ExpectedExecutablePath 'C:\\bys360\\project\\.venv\\Scripts\\python.exe' -ExpectedCommandLineFragment 'run_server.py'
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
    result = _run_ps_snippet(body)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "OK=False" in result.stdout
    assert "REASON=NO_LISTENER" in result.stdout


# ---------------------------------------------------------------------------
# Test-ReleaseIdentityBinding / Test-ReadinessGate: real local disposable
# HTTP server, never the real application, never real port 80.
# ---------------------------------------------------------------------------


_FAKE_SERVER_SOURCE = r"""
import http.server
import json
import sys

config = json.loads(sys.argv[2])

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/versionz":
            body = json.dumps(config["versionz_body"]).encode("utf-8")
            self.send_response(config["versionz_status"])
        elif self.path == "/readyz":
            body = json.dumps(config["readyz_body"]).encode("utf-8")
            self.send_response(config["readyz_status"])
        else:
            body = b"{}"
            self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

port = int(sys.argv[1])
server = http.server.HTTPServer(("127.0.0.1", port), Handler)
server.serve_forever()
"""


def _spawn_fake_versionz_readyz_server(port: int, tmp_path: Path, *, config: dict) -> subprocess.Popen:
    script = tmp_path / f"fake_server_{port}.py"
    script.write_text(_FAKE_SERVER_SOURCE, encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(script), str(port), json.dumps(config)],
        cwd=str(tmp_path),
    )
    for _ in range(50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            try:
                probe.connect(("127.0.0.1", port))
                return proc
            except OSError:
                time.sleep(0.1)
    proc.kill()
    pytest.fail(f"Fake versionz/readyz server on port {port} never came up.")


def test_release_identity_binding_accepts_matching_candidate(tmp_path: Path) -> None:
    port = _free_port()
    proc = _spawn_fake_versionz_readyz_server(port, tmp_path, config={
        "versionz_body": {"service": "bys360", "source_sha": "cafef00d", "migration_head": "10858a18e9ac"},
        "versionz_status": 200,
        "readyz_body": {}, "readyz_status": 200,
    })
    try:
        body = _dot_source_prefix() + f"""
$result = Test-ReleaseIdentityBinding -BaseUrl 'http://127.0.0.1:{port}' -HostHeader 'bys360.canakkaletarihialan.gov.tr' -ExpectedSourceSha 'cafef00d' -ExpectedMigrationHead '10858a18e9ac'
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=True" in result.stdout, result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_release_identity_binding_rejects_a_stale_or_wrong_release_responder(tmp_path: Path) -> None:
    """The Defect Z wrong-release negative proof: a real, live, healthy
    responder -- but reporting a DIFFERENT release's identity (e.g. a stale
    process that never got the new candidate's code, or a rollback target
    that was never supposed to be accepted here)."""
    port = _free_port()
    proc = _spawn_fake_versionz_readyz_server(port, tmp_path, config={
        "versionz_body": {"service": "bys360", "source_sha": "STALE_OLD_SHA", "migration_head": "e0efcd07abf7"},
        "versionz_status": 200,
        "readyz_body": {}, "readyz_status": 200,
    })
    try:
        body = _dot_source_prefix() + f"""
$result = Test-ReleaseIdentityBinding -BaseUrl 'http://127.0.0.1:{port}' -HostHeader 'bys360.canakkaletarihialan.gov.tr' -ExpectedSourceSha 'cafef00d' -ExpectedMigrationHead '10858a18e9ac'
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=False" in result.stdout, result.stdout
        assert "REASON=SOURCE_SHA_MISMATCH" in result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_readiness_gate_accepts_ready_status(tmp_path: Path) -> None:
    port = _free_port()
    proc = _spawn_fake_versionz_readyz_server(port, tmp_path, config={
        "versionz_body": {}, "versionz_status": 200,
        "readyz_body": {"status": "ready", "service": "bys360"}, "readyz_status": 200,
    })
    try:
        body = _dot_source_prefix() + f"""
$result = Test-ReadinessGate -BaseUrl 'http://127.0.0.1:{port}' -HostHeader 'bys360.canakkaletarihialan.gov.tr'
Write-Output ("OK=" + $result.Ok)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=True" in result.stdout, result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)


def test_readiness_gate_rejects_degraded_status(tmp_path: Path) -> None:
    port = _free_port()
    proc = _spawn_fake_versionz_readyz_server(port, tmp_path, config={
        "versionz_body": {}, "versionz_status": 200,
        "readyz_body": {"status": "degraded", "service": "bys360", "schema_error_count": 3}, "readyz_status": 503,
    })
    try:
        body = _dot_source_prefix() + f"""
$result = Test-ReadinessGate -BaseUrl 'http://127.0.0.1:{port}' -HostHeader 'bys360.canakkaletarihialan.gov.tr'
Write-Output ("OK=" + $result.Ok)
Write-Output ("REASON=" + $result.Reason)
"""
        result = _run_ps_snippet(body)
        assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        assert "OK=False" in result.stdout, result.stdout
        assert "REASON=HTTP_503" in result.stdout
    finally:
        proc.kill()
        proc.wait(timeout=5)
