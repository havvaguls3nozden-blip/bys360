"""BYS360 Windows installer launcher-overwrite guard sozlesme testleri.

`Install-BysTask` (install_bys360_daily_mail_tasks_v1_4.ps1 /
install_bys360_daily_weather_mail_task.ps1) ve register_bys360_executive_summary_
tasks_v2_14_3.ps1, daha once calistirildiklarinda hedef .ps1 launcher dosyasinin
ICERIGINI kendi minimal (ErrorActionPreference=Continue, guard'siz, kilitsiz)
sablonuyla `Set-Content` ile UZERINE YAZIYORDU. Bu, kaynak kontrollu, guvenli
kanonik launcher'lari (Test-Path guard'lari, Stop policy, gercek throw) her
kurulumda siliyordu.

Bu dosya, duzeltilmis davranisi DOGRULAR:
  1) installer/register scripti launcher dosyasinin ICERIGINE ASLA yazmaz
     (Set-Content/Out-File KULLANILMAZ) - statik kaynak taramasi.
  2) installer, MEVCUT kanonik launcher'i degistirmeden kullanir (idempotent;
     iki kez "calistirildiginda" dosya hash'i degismez).
  3) launcher dosyasi yoksa installer acik `throw` ile durur (sessiz devam etmez).
  4) launcher dosyasi bozuk/parse edilemezse installer `throw` ile durur.
  5) Scheduled Task action'i dogru kanonik launcher yoluna isaret eder.
  6) Hicbir test, gercek Register-ScheduledTask/Unregister-ScheduledTask
     cagirmaz; tum Scheduled Task cmdlet'leri PowerShell mock fonksiyonlariyla
     degistirilir (dry-run). Gercek mail/runner de CALISTIRILMAZ.

Not: scripts\\communication\\run_daily_pulse_check_mail.ps1 gercek repoda hala
YOKTUR (bkz. test_daily_pulse_check_mail_launcher_is_still_blocked_and_not_
fabricated). Bu, onceki turdaki "kanitsiz launcher uydurmama" kuraliyla
tutarlidir; bu test dosyasi sadece installer MEKANIZMASINI dogrular, eksik
launcher'i icat etmez. Weather/executive-summary senaryolari icin kullanilan
"pulse" ve "bozuk syntax" launcher govdeleri SADECE gecici test sandbox'larinda
(pytest tmp_path) olusturulur; gercek repoya asla yazilmaz.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
PS_EXE = shutil.which("pwsh") or shutil.which("powershell")

INSTALL_V1_4 = ROOT / "scripts" / "windows" / "install_bys360_daily_mail_tasks_v1_4.ps1"
INSTALL_WEATHER = ROOT / "scripts" / "windows" / "install_bys360_daily_weather_mail_task.ps1"
INSTALL_PULSE_STANDALONE = ROOT / "scripts" / "windows" / "install_bys360_daily_pulse_mail_task.ps1"
REGISTER_V2_14_3 = ROOT / "scripts" / "windows" / "register_bys360_executive_summary_tasks_v2_14_3.ps1"

CANONICAL_WEATHER_LAUNCHER = ROOT / "scripts" / "communication" / "run_daily_weather_personnel_mail.ps1"
WEATHER_RUNNER = ROOT / "scripts" / "communication" / "send_daily_weather_personnel_mail.py"
PULSE_RUNNER = ROOT / "scripts" / "communication" / "send_daily_pulse_check_mail.py"
PULSE_LAUNCHER_REAL = ROOT / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1"

CANONICAL_EXEC_MORNING = ROOT / "scripts" / "windows" / "run_executive_summary_0830.ps1"
CANONICAL_EXEC_NIGHT = ROOT / "scripts" / "windows" / "run_executive_summary_0001.ps1"

ALL_INSTALL_AND_REGISTER_SCRIPTS = sorted(
    list((ROOT / "scripts" / "windows").glob("install_*.ps1"))
    + list((ROOT / "scripts" / "windows").glob("register_*.ps1"))
)

MOCK_SCHEDULED_TASK_CMDLETS = r"""
$ErrorActionPreference = 'Stop'
$Global:MockCalls = New-Object System.Collections.ArrayList

function New-ScheduledTaskAction {
    [CmdletBinding()]
    param([string]$Execute, [string]$Argument, [string]$WorkingDirectory)
    [void]$Global:MockCalls.Add(@{Cmdlet='New-ScheduledTaskAction'; Execute=$Execute; Argument=$Argument; WorkingDirectory=$WorkingDirectory})
    return [PSCustomObject]@{Execute=$Execute; Argument=$Argument; WorkingDirectory=$WorkingDirectory}
}
function New-ScheduledTaskTrigger {
    [CmdletBinding()]
    param([switch]$Daily, $At, [switch]$Once, $RepetitionInterval, $RepetitionDuration)
    return [PSCustomObject]@{Daily=[bool]$Daily; At=$At}
}
function New-ScheduledTaskSettingsSet {
    [CmdletBinding()]
    param([switch]$AllowStartIfOnBatteries,[switch]$DontStopIfGoingOnBatteries,[switch]$StartWhenAvailable,[string]$MultipleInstances)
    return [PSCustomObject]@{}
}
function New-ScheduledTaskPrincipal {
    [CmdletBinding()]
    param([string]$UserId, [string]$LogonType, [string]$RunLevel)
    [void]$Global:MockCalls.Add(@{Cmdlet='New-ScheduledTaskPrincipal'; UserId=$UserId; LogonType=$LogonType; RunLevel=$RunLevel})
    return [PSCustomObject]@{UserId=$UserId; LogonType=$LogonType; RunLevel=$RunLevel}
}
function Get-ScheduledTask {
    [CmdletBinding()]
    param([string[]]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Get-ScheduledTask'; TaskName=($TaskName -join ',')})
    return $null
}
function Set-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName,$Action,$Trigger,$Settings,$Principal)
    [void]$Global:MockCalls.Add(@{Cmdlet='Set-ScheduledTask'; TaskName=$TaskName; Principal=$Principal})
    return $null
}
function Register-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName,$Action,$Trigger,$Settings,[string]$Description,[switch]$Force,$Principal)
    [void]$Global:MockCalls.Add(@{Cmdlet='Register-ScheduledTask'; TaskName=$TaskName; Description=$Description; Principal=$Principal})
    return $null
}
function Unregister-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName,[switch]$Confirm)
    [void]$Global:MockCalls.Add(@{Cmdlet='Unregister-ScheduledTask'; TaskName=$TaskName})
    return $null
}
function Get-ScheduledTaskInfo {
    [CmdletBinding()]
    param([string]$TaskName)
    return $null
}
"""


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:  # noqa: F811 - kasitli olarak pytest'in yerlesik tmp_path'ini golgeler.
    """pytest'in yerlesik `tmp_path` fixture'i, bu makinede kullanici adindaki
    Turkce karakterler (ornegin 'Havva Gulsen OZDEN') nedeniyle
    `AppData\\Local\\Temp\\pytest-of-...` dizinini tarayamiyor ve
    PermissionError firlatiyor (ortam kaynakli, bu test dosyasinin mantigiyla
    ilgisiz). Bunun yerine dogrudan `tempfile.mkdtemp()` (8.3 kisa yol
    kullanir, sorunsuz calisir) tabanli kendi sandbox dizinimizi kuruyoruz."""
    d = Path(tempfile.mkdtemp(prefix="bys360_installer_guard_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _require_ps() -> str:
    if not PS_EXE:
        pytest.skip("PowerShell CLI bulunamadi; mock/dry-run dogrulama atlandi.")
    return PS_EXE


def _parse_ok(path: Path) -> None:
    exe = _require_ps()
    script = (
        "$e=$null;$t=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        f"'{path}', [ref]$t, [ref]$e);"
        "Write-Output $e.Count"
    )
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"PowerShell parser cagirisi basarisiz: {result.stderr}"
    assert result.stdout.strip() == "0", f"{path} parse hatasi icerir: {result.stdout} {result.stderr}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ps_single_quote(value: str) -> str:
    """Bir Python string'ini guvenli bir PowerShell TEK TIRNAKLI literaline
    cevirir. json.dumps() KULLANILMAZ: PowerShell'in cift-tirnakli string
    kacis kurallari (backslash ozel karakter DEGILDIR) JSON'unkiyle uyusmaz;
    json.dumps ile gomulen Windows yollari, ters egik cizgilerin ikizlenmesine
    (\\\\ -> \\\\\\\\) yol acar. Tek tirnakli PowerShell string'lerinde tek
    ozel durum tek tirnagin kendisidir (iki tek tirnak ile kacilir)."""
    return "'" + value.replace("'", "''") + "'"


def _run_mocked_installer(target_script: Path, project_root: Path, work_dir: Path, runs: int = 1) -> dict:
    """target_script'i, TUM Scheduled Task cmdlet'leri mock'lanmis bir PowerShell
    oturumunda `runs` kez calistirir. Gercek Register-ScheduledTask/
    Unregister-ScheduledTask/Get-ScheduledTask ASLA cagrilmaz (mock fonksiyonlar
    devreye girer). Sonuc: {"results": [{"run":1,"success":bool,"error":str|None}, ...],
    "mock_calls": [...]}.

    Cross-platform not: install_bys360_daily_mail_tasks_v1_4.ps1 ve
    install_bys360_daily_weather_mail_task.ps1, kendi `-ProjectRoot`
    parametresinden BAGIMSIZ olarak, kosulsuz sekilde sabit `C:\bys360\logs`
    yolunu olusturur (bu, gercek run_daily_weather_personnel_mail.ps1
    launcher'inin da bagimsiz olarak referans ettigi, kasitli/gercek bir
    production convention'idir -- degistirilmedi, bkz. TD-032 remote-CI
    unblock dalgasi raporu). GitHub'in Linux runner'inda pwsh'ta hic `C:`
    surucusu olmadigi icin bu satir gercek bir hata ile patlar ("Cannot find
    drive. A drive with the name 'C' does not exist."). Bu fonksiyon, YALNIZ
    gercek bir `C:` suruculu ortam (Windows) YOKSA, pytest-owned bir gecici
    dizini `C:` adiyla PSDrive olarak mount eder -- boylece installer'in
    KENDI, degistirilmemis kodu, hic sandbox-farkli davranmadan, gercek bir
    dosya sistemi hedefine yazabilir. Windows'ta bu blok no-op'tur (gercek
    `C:` zaten var, PSDrive olusturulmaz, hicbir davranis degismez)."""
    exe = _require_ps()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "harness_out.json"
    harness_path = work_dir / "harness.ps1"

    harness = MOCK_SCHEDULED_TASK_CMDLETS
    harness += "\n$installerPath = " + _ps_single_quote(str(target_script)) + "\n"
    harness += "$projectRoot = " + _ps_single_quote(str(project_root)) + "\n"
    harness += f"$runs = {runs}\n"
    harness += r"""
$hasRealCDrive = $false
try { $hasRealCDrive = [bool](Test-Path -LiteralPath 'C:\') } catch { $hasRealCDrive = $false }
$FakeCDriveRoot = $null
if (-not $hasRealCDrive) {
    $FakeCDriveRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("bys360_fake_c_drive_" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $FakeCDriveRoot | Out-Null
    New-PSDrive -Name 'C' -PSProvider FileSystem -Root $FakeCDriveRoot -Scope Global | Out-Null
}

$results = @()
for ($i = 1; $i -le $runs; $i++) {
    $errMsg = $null
    $success = $true
    try {
        & $installerPath -ProjectRoot $projectRoot
    } catch {
        $success = $false
        $errMsg = $_.Exception.Message
    }
    $results += [PSCustomObject]@{ Run = $i; Success = $success; Error = $errMsg }
}

if ($FakeCDriveRoot) {
    Remove-PSDrive -Name 'C' -Force -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $FakeCDriveRoot -ErrorAction SilentlyContinue
}

$output = [PSCustomObject]@{
    Results = $results
    MockCalls = @($Global:MockCalls)
}
"""
    harness += "$output | ConvertTo-Json -Depth 8 | Set-Content -Path " + _ps_single_quote(str(out_json)) + " -Encoding UTF8\n"

    harness_path.write_text(harness, encoding="utf-8")

    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(harness_path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, (
        f"Mock harness kendisi (installer degil) basarisiz oldu: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert out_json.exists(), f"Harness JSON ciktisi olusmadi: stdout={result.stdout!r} stderr={result.stderr!r}"

    # Windows PowerShell (5.1) -Encoding UTF8 BOM ekler; utf-8-sig ile okuyoruz.
    raw = json.loads(out_json.read_text(encoding="utf-8-sig"))
    results = raw["Results"]
    if isinstance(results, dict):
        results = [results]
    mock_calls = raw.get("MockCalls") or []
    if isinstance(mock_calls, dict):
        mock_calls = [mock_calls]

    return {"results": results, "mock_calls": mock_calls}


def _make_dummy_file(path: Path, content: str = "# dummy test fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


PULSE_LAUNCHER_TEST_FIXTURE = """param()
$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\\bys360\\project"
$Python = Join-Path $ProjectRoot ".venv\\Scripts\\python.exe"
$Script = Join-Path $ProjectRoot "scripts\\communication\\send_daily_pulse_check_mail.py"
if (!(Test-Path $Python)) { throw "Python bulunamadi: $Python" }
if (!(Test-Path $Script)) { throw "Pulse mail scripti bulunamadi: $Script" }
Set-Location $ProjectRoot
& $Python $Script
if ($LASTEXITCODE -ne 0) { throw "Daily Pulse Check Mail basarisiz. ExitCode=$LASTEXITCODE" }
"""

BROKEN_PS1_FIXTURE = 'param()\nif ($true) {\n    Write-Host "unterminated block, deliberately broken for test\n'


def _build_weather_sandbox(tmp_path: Path, *, include_weather_launcher: bool = True,
                            weather_launcher_content: str | None = None,
                            include_pulse_launcher: bool = True) -> Path:
    """install_bys360_daily_mail_tasks_v1_4.ps1 / install_bys360_daily_weather_mail_task.ps1
    icin izole (repo disi) bir sahte ProjectRoot kurar."""
    project_root = tmp_path / "project"
    _make_dummy_file(project_root / ".venv" / "Scripts" / "python.exe", "dummy python.exe\n")
    _make_dummy_file(
        project_root / "scripts" / "communication" / "send_daily_weather_personnel_mail.py",
        "# dummy weather runner\n",
    )
    _make_dummy_file(
        project_root / "scripts" / "communication" / "send_daily_pulse_check_mail.py",
        "# dummy pulse runner\n",
    )

    if include_weather_launcher:
        content = weather_launcher_content
        if content is None:
            content = CANONICAL_WEATHER_LAUNCHER.read_text(encoding="utf-8")
        _make_dummy_file(
            project_root / "scripts" / "communication" / "run_daily_weather_personnel_mail.ps1",
            content,
        )

    if include_pulse_launcher:
        _make_dummy_file(
            project_root / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1",
            PULSE_LAUNCHER_TEST_FIXTURE,
        )

    return project_root


def _build_exec_summary_sandbox(tmp_path: Path, *, include_morning: bool = True,
                                 include_night: bool = True,
                                 morning_content: str | None = None,
                                 night_content: str | None = None) -> Path:
    """register_bys360_executive_summary_tasks_v2_14_3.ps1 icin izole ProjectRoot kurar."""
    project_root = tmp_path / "project"
    _make_dummy_file(project_root / ".venv" / "Scripts" / "python.exe", "dummy python.exe\n")

    if include_morning:
        content = morning_content if morning_content is not None else CANONICAL_EXEC_MORNING.read_text(encoding="utf-8")
        _make_dummy_file(project_root / "scripts" / "windows" / "run_executive_summary_0830.ps1", content)

    if include_night:
        content = night_content if night_content is not None else CANONICAL_EXEC_NIGHT.read_text(encoding="utf-8")
        _make_dummy_file(project_root / "scripts" / "windows" / "run_executive_summary_0001.ps1", content)

    return project_root


# ---------------------------------------------------------------------------
# 1) Statik kaynak taramasi: hicbir installer/register scripti artik bir .ps1
#    launcher dosyasinin ICERIGINI uretmiyor/uzerine yazmiyor.
# ---------------------------------------------------------------------------


def _non_comment_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if not ln.strip().startswith("#")]


def test_no_install_or_register_script_generates_or_overwrites_a_launcher_file() -> None:
    """scripts\\windows altindaki TUM install_*.ps1 / register_*.ps1 dosyalari
    taranir: hicbirinde (yorum satirlari haric) Set-Content veya Out-File
    KULLANILMAMALIDIR. Installer'lar sadece Scheduled Task TANIMINI kurar;
    launcher dosyasinin icerigine dokunmaz."""
    assert len(ALL_INSTALL_AND_REGISTER_SCRIPTS) >= 10, "Beklenenden az installer/register dosyasi bulundu."

    offenders = []
    for script in ALL_INSTALL_AND_REGISTER_SCRIPTS:
        code_lines = _non_comment_lines(script.read_text(encoding="utf-8"))
        code_text = "\n".join(code_lines)
        if "Set-Content" in code_text or "Out-File" in code_text:
            offenders.append(script.name)

    assert offenders == [], (
        "Asagidaki installer/register dosyalari hala bir dosyanin (launcher "
        f"olmasi muhtemel) icerigini Set-Content/Out-File ile uretiyor: {offenders}"
    )


def test_fixed_scripts_still_reference_their_canonical_launcher_paths_by_name() -> None:
    """Duzeltme, launcher YOLUNU degil, sadece URETIM/UZERINE-YAZMA davranisini
    kaldirdi. Installer'lar hala dogru kanonik dosya adlarini referans etmeli."""
    v1_4_text = INSTALL_V1_4.read_text(encoding="utf-8")
    weather_text = INSTALL_WEATHER.read_text(encoding="utf-8")
    register_text = REGISTER_V2_14_3.read_text(encoding="utf-8")

    for text in (v1_4_text, weather_text):
        assert "run_daily_weather_personnel_mail.ps1" in text
        assert "run_daily_pulse_check_mail.ps1" in text
        assert "Test-Path $Launcher" in text
        assert "ParseFile" in text

    assert "run_executive_summary_0830.ps1" in register_text
    assert "run_executive_summary_0001.ps1" in register_text
    assert "ParseFile" in register_text
    assert "Test-Path $Path" in register_text


@pytest.mark.parametrize(
    "path",
    ALL_INSTALL_AND_REGISTER_SCRIPTS,
    ids=[p.name for p in ALL_INSTALL_AND_REGISTER_SCRIPTS],
)
def test_all_installer_and_register_scripts_parse_with_zero_errors(path: Path) -> None:
    _parse_ok(path)


# ---------------------------------------------------------------------------
# 2) Mock/dry-run davranis testleri: install_bys360_daily_mail_tasks_v1_4.ps1
#    ve install_bys360_daily_weather_mail_task.ps1 (Install-BysTask fonksiyonu).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("installer", [INSTALL_V1_4, INSTALL_WEATHER], ids=["v1_4", "weather_task_variant"])
def test_install_bystask_never_modifies_canonical_launchers_and_is_idempotent(installer: Path, tmp_path: Path) -> None:
    project_root = _build_weather_sandbox(tmp_path / "sandbox")
    weather_launcher = project_root / "scripts" / "communication" / "run_daily_weather_personnel_mail.ps1"
    pulse_launcher = project_root / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1"

    hash_weather_before = _sha256(weather_launcher)
    hash_pulse_before = _sha256(pulse_launcher)

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", runs=2)

    for run in harness_result["results"]:
        assert run["Success"] is True, f"Run {run['Run']} basarisiz oldu: {run.get('Error')}"

    # Launcher dosyalarinin icerigi degismemis olmali (installer bunlari
    # ASLA yeniden uretmiyor).
    assert _sha256(weather_launcher) == hash_weather_before, "Weather launcher installer tarafindan degistirildi!"
    assert _sha256(pulse_launcher) == hash_pulse_before, "Pulse launcher installer tarafindan degistirildi!"

    # Scheduled Task action'i dogru kanonik launcher yoluna isaret etmeli.
    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    weather_actions = [c for c in action_calls if str(weather_launcher) in (c.get("Argument") or "")]
    pulse_actions = [c for c in action_calls if str(pulse_launcher) in (c.get("Argument") or "")]

    assert len(weather_actions) == 2, "Weather task icin her run'da tam olarak bir Scheduled Task action beklenir."
    assert len(pulse_actions) == 2, "Pulse task icin her run'da tam olarak bir Scheduled Task action beklenir."

    # Idempotentlik: iki run'da uretilen action argumanlari birebir ayni olmali.
    assert weather_actions[0]["Argument"] == weather_actions[1]["Argument"]
    assert pulse_actions[0]["Argument"] == pulse_actions[1]["Argument"]

    # Gercek Register-ScheduledTask/Set-ScheduledTask disinda hicbir gercek
    # Windows Task Scheduler cagrisi yapilmadi (hepsi mock).
    register_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") in ("Register-ScheduledTask", "Set-ScheduledTask")]
    assert len(register_calls) == 4  # 2 gorev x 2 run


@pytest.mark.parametrize("installer", [INSTALL_V1_4, INSTALL_WEATHER], ids=["v1_4", "weather_task_variant"])
def test_install_bystask_registers_every_task_with_explicit_system_service_account_principal(installer: Path, tmp_path: Path) -> None:
    """BYS360 DEFECT Y: without an explicit Principal, Register-ScheduledTask/
    Set-ScheduledTask default to the CURRENT INTERACTIVE caller's identity --
    wrong for these unattended, timer-driven daily mail tasks (SMTP-based,
    no Outlook/COM/interactive-desktop dependency). Every Install-BysTask
    registration must carry an explicit SYSTEM / ServiceAccount / Highest
    principal."""
    project_root = _build_weather_sandbox(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", runs=1)
    assert harness_result["results"][0]["Success"] is True

    register_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") in ("Register-ScheduledTask", "Set-ScheduledTask")]
    assert len(register_calls) == 2, "Weather + Pulse gorevleri icin tam olarak iki kayit cagrisi beklenir."
    for call in register_calls:
        principal = call.get("Principal") or {}
        assert principal.get("UserId") == "SYSTEM", f"Principal SYSTEM olmali: {call!r}"
        assert principal.get("LogonType") == "ServiceAccount", f"LogonType ServiceAccount olmali: {call!r}"
        assert principal.get("RunLevel") == "Highest", f"RunLevel Highest olmali: {call!r}"


@pytest.mark.parametrize("installer", [INSTALL_V1_4, INSTALL_WEATHER], ids=["v1_4", "weather_task_variant"])
def test_install_bystask_throws_when_weather_launcher_is_missing(installer: Path, tmp_path: Path) -> None:
    project_root = _build_weather_sandbox(tmp_path / "sandbox", include_weather_launcher=False)

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False, "Launcher eksikken installer sessizce basarili olmamali."
    assert "Launcher bulunamadi" in (run.get("Error") or "")
    assert "run_daily_weather_personnel_mail.ps1" in (run.get("Error") or "")

    # Hicbir Scheduled Task mutasyonu denenmemis olmali (fail-fast).
    assert harness_result["mock_calls"] == []


@pytest.mark.parametrize("installer", [INSTALL_V1_4, INSTALL_WEATHER], ids=["v1_4", "weather_task_variant"])
def test_install_bystask_throws_when_weather_launcher_has_invalid_syntax(installer: Path, tmp_path: Path) -> None:
    project_root = _build_weather_sandbox(
        tmp_path / "sandbox",
        weather_launcher_content=BROKEN_PS1_FIXTURE,
    )

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False, "Bozuk syntax'li launcher installer'i durdurmali."
    assert "parse hatasi" in (run.get("Error") or "").lower() or "sozdizim" in (run.get("Error") or "").lower()
    assert harness_result["mock_calls"] == []


@pytest.mark.parametrize("installer", [INSTALL_V1_4, INSTALL_WEATHER], ids=["v1_4", "weather_task_variant"])
def test_install_bystask_throws_when_launcher_does_not_reference_expected_runner(installer: Path, tmp_path: Path) -> None:
    """Launcher var ve gecerli PowerShell ama beklenen python runner scriptini
    referans etmiyor (yanlis/eslesmeyen bir dosyaya isaret ediyor olabilir).
    Bu, kullanicinin istegindeki opsiyonel 'contract kontrolu' (madde 4)
    icin eklendi: hash pinleme yerine hafif bir icerik-sozlesmesi kontrolu
    tercih edildi, cunku hash pinleme kanonik launcher her mesru guncellendiginde
    installer'i yanlis pozitif sekilde kirar."""
    mismatched_content = (
        'param()\n$ErrorActionPreference = "Stop"\n'
        'Write-Host "bu launcher yanlislikla baska bir scripti cagiriyor"\n'
    )
    project_root = _build_weather_sandbox(
        tmp_path / "sandbox",
        weather_launcher_content=mismatched_content,
    )

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False
    assert "referans etmiyor" in (run.get("Error") or "")
    assert harness_result["mock_calls"] == []


# ---------------------------------------------------------------------------
# 3) Mock/dry-run davranis testleri: register_bys360_executive_summary_tasks_v2_14_3.ps1
# ---------------------------------------------------------------------------


def test_register_v2_14_3_never_modifies_canonical_launchers_and_is_idempotent(tmp_path: Path) -> None:
    project_root = _build_exec_summary_sandbox(tmp_path / "sandbox")
    morning = project_root / "scripts" / "windows" / "run_executive_summary_0830.ps1"
    night = project_root / "scripts" / "windows" / "run_executive_summary_0001.ps1"

    hash_morning_before = _sha256(morning)
    hash_night_before = _sha256(night)

    harness_result = _run_mocked_installer(REGISTER_V2_14_3, project_root, tmp_path / "harness", runs=2)

    for run in harness_result["results"]:
        assert run["Success"] is True, f"Run {run['Run']} basarisiz oldu: {run.get('Error')}"

    assert _sha256(morning) == hash_morning_before, "Morning executive summary launcher degistirildi!"
    assert _sha256(night) == hash_night_before, "Night executive summary launcher degistirildi!"

    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    morning_actions = [c for c in action_calls if str(morning) in (c.get("Argument") or "")]
    night_actions = [c for c in action_calls if str(night) in (c.get("Argument") or "")]

    assert len(morning_actions) == 2
    assert len(night_actions) == 2
    assert morning_actions[0]["Argument"] == morning_actions[1]["Argument"]
    assert night_actions[0]["Argument"] == night_actions[1]["Argument"]


def test_register_v2_14_3_registers_both_tasks_with_explicit_system_service_account_principal(tmp_path: Path) -> None:
    """BYS360 DEFECT Y: "BYS360 Executive Summary 0001" fires at 00:01, when
    no operator is realistically logged on. Without an explicit Principal,
    Register-ScheduledTask defaults to the current interactive caller's
    identity -- both tasks must carry an explicit SYSTEM / ServiceAccount /
    Highest principal."""
    project_root = _build_exec_summary_sandbox(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(REGISTER_V2_14_3, project_root, tmp_path / "harness", runs=1)
    assert harness_result["results"][0]["Success"] is True

    register_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") in ("Register-ScheduledTask", "Set-ScheduledTask")]
    assert len(register_calls) == 2, "Morning + night gorevleri icin tam olarak iki kayit cagrisi beklenir."
    for call in register_calls:
        principal = call.get("Principal") or {}
        assert principal.get("UserId") == "SYSTEM", f"Principal SYSTEM olmali: {call!r}"
        assert principal.get("LogonType") == "ServiceAccount", f"LogonType ServiceAccount olmali: {call!r}"
        assert principal.get("RunLevel") == "Highest", f"RunLevel Highest olmali: {call!r}"


@pytest.mark.parametrize(
    "missing,label",
    [("morning", "Executive Summary 0830"), ("night", "Executive Summary 0001")],
)
def test_register_v2_14_3_throws_when_a_launcher_is_missing(missing: str, label: str, tmp_path: Path) -> None:
    project_root = _build_exec_summary_sandbox(
        tmp_path / "sandbox",
        include_morning=missing != "morning",
        include_night=missing != "night",
    )

    harness_result = _run_mocked_installer(REGISTER_V2_14_3, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False
    assert "launcher bulunamadi" in (run.get("Error") or "").lower()
    assert label in (run.get("Error") or "")
    assert harness_result["mock_calls"] == []


@pytest.mark.parametrize("broken", ["morning", "night"])
def test_register_v2_14_3_throws_when_a_launcher_has_invalid_syntax(broken: str, tmp_path: Path) -> None:
    morning_content = BROKEN_PS1_FIXTURE if broken == "morning" else None
    night_content = BROKEN_PS1_FIXTURE if broken == "night" else None
    project_root = _build_exec_summary_sandbox(
        tmp_path / "sandbox",
        morning_content=morning_content,
        night_content=night_content,
    )

    harness_result = _run_mocked_installer(REGISTER_V2_14_3, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False
    err = (run.get("Error") or "").lower()
    assert "parse hatasi" in err or "sozdizim" in err
    assert harness_result["mock_calls"] == []


# ---------------------------------------------------------------------------
# 4) BYS360 DEFECT AG closure: the previously-missing launcher now exists,
#    with a real, reviewed, mechanically-proven contract -- not a guess.
# ---------------------------------------------------------------------------


def test_daily_pulse_check_mail_launcher_now_exists_with_reviewed_canonical_contract() -> None:
    """BYS360 DEFECT AG (closure of the prior BLOCKED finding): scripts\\
    communication\\run_daily_pulse_check_mail.ps1 was mechanically confirmed
    missing (install_bys360_daily_mail_tasks_v1_4.ps1 /
    install_bys360_daily_weather_mail_task.ps1 already referenced it as
    their Pulse sub-task's required Launcher, so that sub-task could never
    install -- Install-BysTask's own Test-Path guard threw first). This
    wave created it, mirroring the sibling run_daily_weather_personnel_
    mail.ps1 launcher's exact, already-canonical contract: resolve Python/
    script/log paths from a fixed project root, pre-flight Test-Path guard
    both, cd into the project root, let a real PowerShell process (not
    argv passed to python.exe) own ">>"/"2>&1" redirection, and re-throw on
    a non-zero Python exit code so the Scheduled Task correctly reports
    failure."""
    assert PULSE_LAUNCHER_REAL.exists(), "run_daily_pulse_check_mail.ps1 hala repoda bulunamadi -- AG kapatilmadi."
    _parse_ok(PULSE_LAUNCHER_REAL)

    text = PULSE_LAUNCHER_REAL.read_text(encoding="utf-8")
    assert "send_daily_pulse_check_mail.py" in text
    assert "Test-Path $Python" in text
    assert "Test-Path $Script" in text
    assert "& $Python $Script >> $LogPath 2>&1" in text, (
        "Launcher gercek PowerShell redirection operatorlerini kullanmali "
        "(argv olarak degil) -- Defect AA'nin kok nedeniyle ayni sinif hata."
    )
    assert "$LASTEXITCODE -ne 0" in text and "throw" in text, (
        "Launcher, Python'un sifir olmayan cikis kodunu Scheduled Task'a "
        "yaymak icin throw etmeli."
    )

    for installer in (INSTALL_V1_4, INSTALL_WEATHER):
        installer_text = installer.read_text(encoding="utf-8")
        assert "run_daily_pulse_check_mail.ps1" in installer_text


# ---------------------------------------------------------------------------
# 5) BYS360 DEFECT AG end-to-end proof: v1_4/weather actually install the
#    Pulse sub-task successfully using the REAL launcher file's own content
#    (not the synthetic sandbox fixture used by the tests above).
# ---------------------------------------------------------------------------


def _build_weather_sandbox_with_real_pulse_launcher(tmp_path: Path) -> Path:
    project_root = _build_weather_sandbox(tmp_path, include_pulse_launcher=False)
    _make_dummy_file(
        project_root / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1",
        PULSE_LAUNCHER_REAL.read_text(encoding="utf-8"),
    )
    return project_root


@pytest.mark.parametrize("installer", [INSTALL_V1_4, INSTALL_WEATHER], ids=["v1_4", "weather_task_variant"])
def test_pulse_subtask_installs_successfully_using_the_real_launcher_content(installer: Path, tmp_path: Path) -> None:
    """AG closure proof: this is NOT the synthetic PULSE_LAUNCHER_TEST_FIXTURE
    -- the sandbox is seeded with the ACTUAL bytes of scripts/communication/
    run_daily_pulse_check_mail.ps1 read straight off disk, proving the real,
    just-created file (not an assumption about its shape) satisfies Install-
    BysTask's launcher-content-reference contract end to end."""
    project_root = _build_weather_sandbox_with_real_pulse_launcher(tmp_path / "sandbox")
    pulse_launcher = project_root / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1"

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]
    assert run["Success"] is True, f"Pulse sub-task kurulumu basarisiz oldu: {run.get('Error')}"

    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    pulse_actions = [c for c in action_calls if str(pulse_launcher) in (c.get("Argument") or "")]
    assert len(pulse_actions) == 1, "Gercek launcher iceriginden tam olarak bir Pulse Scheduled Task action'i beklenir."


# ---------------------------------------------------------------------------
# 6) BYS360 DEFECT AA: the standalone install_bys360_daily_pulse_mail_
#    task.ps1 no longer passes ">>"/"2>&1" as literal argv to python.exe.
# ---------------------------------------------------------------------------


def _build_standalone_pulse_sandbox(tmp_path: Path, *, include_launcher: bool = True, include_runner: bool = True) -> Path:
    project_root = tmp_path / "project"
    _make_dummy_file(project_root / ".venv" / "Scripts" / "python.exe", "dummy python.exe\n")
    if include_runner:
        _make_dummy_file(project_root / "scripts" / "communication" / "send_daily_pulse_check_mail.py", "# dummy runner\n")
    if include_launcher:
        _make_dummy_file(
            project_root / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1",
            PULSE_LAUNCHER_REAL.read_text(encoding="utf-8"),
        )
    return project_root


def _run_mocked_standalone_pulse_installer(project_root: Path, work_dir: Path) -> dict:
    """install_bys360_daily_pulse_mail_task.ps1'i mock'lanmis bir PowerShell
    oturumunda calistirir (ayni MOCK_SCHEDULED_TASK_CMDLETS katmani, ama
    sadece -ProjectRoot alan tek bir installer icin, -File tabanli calistirma
    olmadan -- bu dosya Apply/dry-run modu yok, dogrudan calistirilir)."""
    exe = _require_ps()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "harness_out.json"
    harness_path = work_dir / "harness.ps1"

    harness = MOCK_SCHEDULED_TASK_CMDLETS
    harness += "\n$installerPath = " + _ps_single_quote(str(INSTALL_PULSE_STANDALONE)) + "\n"
    harness += "$projectRoot = " + _ps_single_quote(str(project_root)) + "\n"
    harness += r"""
$errMsg = $null
$success = $true
try {
    & $installerPath -ProjectRoot $projectRoot
} catch {
    $success = $false
    $errMsg = $_.Exception.Message
}
$output = [PSCustomObject]@{
    Success = $success
    Error = $errMsg
    MockCalls = @($Global:MockCalls)
}
"""
    harness += "$output | ConvertTo-Json -Depth 8 | Set-Content -Path " + _ps_single_quote(str(out_json)) + " -Encoding UTF8\n"
    harness_path.write_text(harness, encoding="utf-8")

    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(harness_path)],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, f"Mock harness kendisi basarisiz oldu: stdout={result.stdout!r} stderr={result.stderr!r}"
    assert out_json.exists(), f"Harness JSON ciktisi olusmadi: stdout={result.stdout!r} stderr={result.stderr!r}"

    raw = json.loads(out_json.read_text(encoding="utf-8-sig"))
    mock_calls = raw.get("MockCalls") or []
    if isinstance(mock_calls, dict):
        mock_calls = [mock_calls]
    return {"success": raw["Success"], "error": raw.get("Error"), "mock_calls": mock_calls}


def test_standalone_pulse_installer_no_longer_passes_redirection_operators_as_python_argv(tmp_path: Path) -> None:
    project_root = _build_standalone_pulse_sandbox(tmp_path / "sandbox")

    result = _run_mocked_standalone_pulse_installer(project_root, tmp_path / "harness")
    assert result["success"] is True, f"Installer basarisiz oldu: {result.get('error')}"

    action_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    assert len(action_calls) == 1
    action = action_calls[0]

    assert action["Execute"] == "powershell.exe", (
        f"Action artik python.exe'yi DOGRUDAN degil, launcher uzerinden powershell.exe ile "
        f"calistirmali. Execute={action['Execute']!r}"
    )
    argument = action["Argument"] or ""
    assert ">>" not in argument, "Defect AA: '>>' artik argv olarak gecilmemeli."
    assert "2>&1" not in argument, "Defect AA: '2>&1' artik argv olarak gecilmemeli."
    assert "-File" in argument
    assert "run_daily_pulse_check_mail.ps1" in argument

    register_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") in ("Register-ScheduledTask", "Set-ScheduledTask")]
    assert len(register_calls) == 1
    principal = register_calls[0].get("Principal") or {}
    assert principal.get("UserId") == "SYSTEM", "Defect Y'nin SYSTEM principal'i Defect AA duzeltmesiyle bozulmamali."


def test_standalone_pulse_installer_throws_when_launcher_is_missing(tmp_path: Path) -> None:
    project_root = _build_standalone_pulse_sandbox(tmp_path / "sandbox", include_launcher=False)

    result = _run_mocked_standalone_pulse_installer(project_root, tmp_path / "harness")
    assert result["success"] is False, "Launcher eksikken installer sessizce basarili olmamali."
    assert "Launcher bulunamadi" in (result.get("error") or "")
    assert result["mock_calls"] == [], "Launcher eksikken hicbir Scheduled Task mutasyonu denenmemeli."


def test_standalone_pulse_installer_throws_when_python_runner_script_is_missing(tmp_path: Path) -> None:
    project_root = _build_standalone_pulse_sandbox(tmp_path / "sandbox", include_runner=False)

    result = _run_mocked_standalone_pulse_installer(project_root, tmp_path / "harness")
    assert result["success"] is False, "Runner script eksikken installer sessizce basarili olmamali."
    assert "Script bulunamadi" in (result.get("error") or "")
    assert result["mock_calls"] == []


def test_two_unrelated_unproven_launchers_remain_untouched() -> None:
    """Bu gorev SADECE installer/register mekanizmasini duzeltir; belirsiz
    launcher'lar icin kod uydurmaz (kullanici talimati)."""
    assert not (ROOT / "scripts" / "windows" / "watch_bys360_live_waitress80.ps1").exists()
    assert not (ROOT / "scripts" / "windows" / "run_performance_mail_reminder_09.ps1").exists()
