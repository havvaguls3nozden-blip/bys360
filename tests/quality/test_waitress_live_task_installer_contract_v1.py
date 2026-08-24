"""BYS360 Live Waitress 80 Scheduled Task installer sozlesme testleri (TD-034).

`scripts\\windows\\install_bys360_live_waitress_80_task_v1.ps1`, canli
"BYS360 Live Waitress 80" Windows Scheduled Task'i icin repoda daha once
HIC bulunmayan guvenli bir install/register otomasyonudur. Bu dosya,
kurdugu davranis sozlesmesini dogrular:

  1) VARSAYILAN calisma (-Apply verilmeden) HICBIR Scheduled Task
     cmdlet'ini cagirmaz (Register/Set/Get/Unregister-ScheduledTask hepsi
     mock'lanmis ve cagrilmadigi dogrulanir) ve exit code 0 ile biter.
  2) -Apply verildiginde ve ayni isimde bir gorev YOKSA, gorev
     Register-ScheduledTask (mock) araciligiyla, run_server.py'ye (run.py
     DEGIL) isaret eden dogru Action/WorkingDirectory ile kurulur.
  3) -Apply verildiginde ve ayni isimde bir gorev ZATEN VARSA, -ConfirmReplace
     verilmedikce installer REDDEDER (hicbir mutasyon mock cagrisi yapilmaz);
     -ConfirmReplace de verilirse tam olarak bir Set-ScheduledTask (mock)
     cagrisiyla basarili olur.
  4) Sahte ProjectRoot altinda python.exe veya run_server.py eksikse
     installer `throw` ile fail-fast durur; hicbir mock cmdlet cagrilmaz.
  5) Script metninde gizli/sifre benzeri alt-dizeler (password/secret/token/
     dsn/apikey/api_key) YOKTUR.
  6) PowerShell parser script'i 0 hata ile parse eder.

Hicbir test gercek Register-ScheduledTask/Set-ScheduledTask/
Start-ScheduledTask/Stop-ScheduledTask/Unregister-ScheduledTask veya
`schtasks` cagirmaz; TUM Scheduled Task cmdlet'leri bu dosyadaki PowerShell
mock fonksiyonlariyla degistirilir (dry-run/mock harness). Sahte ProjectRoot
her zaman izole bir `tempfile.mkdtemp()` sandbox'i altinda kurulur; gercek
`C:\\bys360\\project` veya gercek Windows Task Scheduler'a ASLA dokunulmaz.
"""

from __future__ import annotations

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

INSTALLER = ROOT / "scripts" / "windows" / "install_bys360_live_waitress_80_task_v1.ps1"

FORBIDDEN_SECRET_SHAPED_SUBSTRINGS = ("password", "secret", "token", "dsn", "apikey", "api_key")

LOCKED_UNPROVEN_LAUNCHERS = (
    ROOT / "scripts" / "windows" / "watch_bys360_live_waitress80.ps1",
    ROOT / "scripts" / "windows" / "run_performance_mail_reminder_09.ps1",
)

# Mock cmdlet katmani: gercek ScheduledTasks modulu cmdlet'lerinin ayni
# isimli PowerShell fonksiyonlariyla golgelenmesi (fonksiyonlar, cmdlet'lerden
# ONCE tanimlandigi ve modul otomatik import edilmedigi surece cagrilarin
# hepsini yakalar). Her cagri $Global:MockCalls'a kaydedilir; gercek Windows
# Task Scheduler'a HICBIR sekilde dokunulmaz.
MOCK_SCHEDULED_TASK_CMDLETS = r"""
$ErrorActionPreference = 'Stop'
$Global:MockCalls = New-Object System.Collections.ArrayList
if (-not (Test-Path Variable:Global:MockExistingTaskExists)) {
    $Global:MockExistingTaskExists = $false
}

function New-ScheduledTaskAction {
    [CmdletBinding()]
    param([string]$Execute, [string]$Argument, [string]$WorkingDirectory)
    [void]$Global:MockCalls.Add(@{Cmdlet='New-ScheduledTaskAction'; Execute=$Execute; Argument=$Argument; WorkingDirectory=$WorkingDirectory})
    return [PSCustomObject]@{Execute=$Execute; Argument=$Argument; WorkingDirectory=$WorkingDirectory}
}
function New-ScheduledTaskTrigger {
    [CmdletBinding()]
    param([switch]$AtStartup, [switch]$Daily, $At, [switch]$Once, $RepetitionInterval, $RepetitionDuration)
    [void]$Global:MockCalls.Add(@{Cmdlet='New-ScheduledTaskTrigger'; AtStartup=[bool]$AtStartup})
    return [PSCustomObject]@{AtStartup=[bool]$AtStartup}
}
function New-ScheduledTaskSettingsSet {
    [CmdletBinding()]
    param([switch]$AllowStartIfOnBatteries,[switch]$DontStopIfGoingOnBatteries,[switch]$StartWhenAvailable,[string]$MultipleInstances)
    return [PSCustomObject]@{}
}
function New-ScheduledTaskPrincipal {
    [CmdletBinding()]
    param([string]$UserId, [string]$RunLevel)
    return [PSCustomObject]@{}
}
function Get-ScheduledTask {
    [CmdletBinding()]
    param([string[]]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Get-ScheduledTask'; TaskName=($TaskName -join ',')})
    if ($Global:MockExistingTaskExists) {
        return [PSCustomObject]@{TaskName=($TaskName -join ','); State='Running'; TaskPath='\'}
    }
    return $null
}
function Set-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName,$Action,$Trigger,$Settings,$Principal)
    [void]$Global:MockCalls.Add(@{Cmdlet='Set-ScheduledTask'; TaskName=$TaskName})
    return $null
}
function Register-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName,$Action,$Trigger,$Settings,[string]$Description,[switch]$Force,$Principal)
    [void]$Global:MockCalls.Add(@{Cmdlet='Register-ScheduledTask'; TaskName=$TaskName; Description=$Description})
    return $null
}
function Unregister-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName,[switch]$Confirm)
    [void]$Global:MockCalls.Add(@{Cmdlet='Unregister-ScheduledTask'; TaskName=$TaskName})
    return $null
}
function Start-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Start-ScheduledTask'; TaskName=$TaskName})
    return $null
}
function Stop-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Stop-ScheduledTask'; TaskName=$TaskName})
    return $null
}
function Get-ScheduledTaskInfo {
    [CmdletBinding()]
    param([string]$TaskName)
    return $null
}
function schtasks {
    [void]$Global:MockCalls.Add(@{Cmdlet='schtasks'; Args=($args -join ' ')})
    return ""
}
"""


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:  # noqa: F811 - kasitli olarak pytest'in yerlesik tmp_path'ini golgeler.
    """pytest'in yerlesik `tmp_path` fixture'i, bu makinede kullanici adindaki
    Turkce karakterler nedeniyle `AppData\\Local\\Temp\\pytest-of-...`
    dizinini tarayamiyor ve PermissionError firlatiyor (ortam kaynakli, bu
    test dosyasinin mantigiyla ilgisiz). Bunun yerine dogrudan
    `tempfile.mkdtemp()` (8.3 kisa yol kullanir, sorunsuz calisir) tabanli
    kendi sandbox dizinimizi kuruyoruz."""
    d = Path(tempfile.mkdtemp(prefix="bys360_waitress80_installer_"))
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


def _ps_single_quote(value: str) -> str:
    """Bir Python string'ini guvenli bir PowerShell TEK TIRNAKLI literaline
    cevirir (tek ozel durum tek tirnagin kendisidir, iki tek tirnak ile
    kacilir). json.dumps KULLANILMAZ: Windows yollarindaki ters egik
    cizgiler JSON kacis kurallariyla PowerShell tek-tirnakli string
    kurallariyla uyusmaz."""
    return "'" + value.replace("'", "''") + "'"


def _make_dummy_file(path: Path, content: str = "# dummy test fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_fake_project_root(tmp_path: Path, *, include_python: bool = True, include_run_server: bool = True) -> Path:
    """install_bys360_live_waitress_80_task_v1.ps1 icin izole (repo disi)
    sahte bir ProjectRoot kurar. Gercek C:\\bys360\\project'e ASLA dokunulmaz."""
    project_root = tmp_path / "project"
    if include_python:
        _make_dummy_file(project_root / ".venv" / "Scripts" / "python.exe", "dummy python.exe\n")
    if include_run_server:
        _make_dummy_file(project_root / "run_server.py", "# dummy run_server.py fixture\n")
    return project_root


def _run_mocked_installer(
    project_root: Path,
    work_dir: Path,
    *,
    apply: bool = False,
    confirm_replace: bool = False,
    existing_task: bool = False,
    port: int | None = None,
    task_name: str | None = None,
) -> dict:
    """install_bys360_live_waitress_80_task_v1.ps1'i TUM Scheduled Task
    cmdlet'leri mock'lanmis bir PowerShell oturumunda calistirir. Gercek
    Register-ScheduledTask/Set-ScheduledTask/Start-ScheduledTask/
    Stop-ScheduledTask/Unregister-ScheduledTask veya schtasks ASLA
    cagirilmaz (mock fonksiyonlar devreye girer).
    Sonuc: {"success": bool, "error": str|None, "exit_code": int,
    "stdout": str, "mock_calls": [...]}."""
    exe = _require_ps()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "harness_out.json"
    harness_path = work_dir / "harness.ps1"
    log_path = work_dir / "waitress80.log"

    # NOT: PowerShell ARRAY splatting (`@array`) elemanlari POZISYONEL olarak
    # baglar - bir dizi elemani '-LogPath' gibi gorunse dahi bunu bir
    # parametre adi olarak TANIMAZ (denendi ve dogrulandi: bu, bir sonraki
    # pozisyonel parametreye deger olarak sizar ve tip donusum hatasi
    # verir). Bunun yerine HASHTABLE splatting kullaniyoruz - bu, anahtar
    # adlarini gercek parametre adlariyla (sira bagimsiz) eslestirir ve
    # switch parametreleri icin de ($true/$false) dogru calisir.
    pairs = [
        "'ProjectRoot' = " + _ps_single_quote(str(project_root)),
        "'LogPath' = " + _ps_single_quote(str(log_path)),
    ]
    if port is not None:
        pairs.append(f"'Port' = {port}")
    if task_name is not None:
        pairs.append("'TaskName' = " + _ps_single_quote(task_name))
    if apply:
        pairs.append("'Apply' = $true")
    if confirm_replace:
        pairs.append("'ConfirmReplace' = $true")

    harness = MOCK_SCHEDULED_TASK_CMDLETS
    harness += f"\n$Global:MockExistingTaskExists = ${'true' if existing_task else 'false'}\n"
    harness += "$installerPath = " + _ps_single_quote(str(INSTALLER)) + "\n"
    harness += "$installerArgs = @{" + "; ".join(pairs) + "}\n"
    harness += r"""
$errMsg = $null
$success = $true
$stdout = $null
try {
    # Write-Host ciktisi PowerShell'de Information akisina (6) yazilir, 2>&1
    # (sadece hata akisi) bunu yakalamaz; *>&1 TUM akislari (Information
    # dahil) basari akisina yonlendirir.
    $stdout = & $installerPath @installerArgs *>&1 | Out-String
} catch {
    $success = $false
    $errMsg = $_.Exception.Message
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 0 }
$output = [PSCustomObject]@{
    Success = $success
    Error = $errMsg
    ExitCode = $exitCode
    Stdout = $stdout
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
    mock_calls = raw.get("MockCalls") or []
    if isinstance(mock_calls, dict):
        mock_calls = [mock_calls]

    return {
        "success": raw["Success"],
        "error": raw.get("Error"),
        "exit_code": raw.get("ExitCode"),
        "stdout": raw.get("Stdout") or "",
        "mock_calls": mock_calls,
    }


# ---------------------------------------------------------------------------
# 1) Statik dogrulamalar: dosya varligi, parse, kilitli/uydurulmamis
#    launcher'lara dokunulmadigi.
# ---------------------------------------------------------------------------


def test_installer_file_exists() -> None:
    assert INSTALLER.exists(), f"Installer bulunamadi: {INSTALLER}"


def test_installer_parses_with_zero_syntax_errors() -> None:
    _parse_ok(INSTALLER)


def test_installer_references_run_server_not_run_py() -> None:
    text = INSTALLER.read_text(encoding="utf-8")
    assert "run_server.py" in text
    # "run.py" tam olarak dosya adi olarak GECMEMELI (run_server.py icinde
    # "run.py" alt-dizesi zaten dogal olarak yer almaz; bu ayrica dogrulanir).
    assert "run.py" not in text


def test_installer_has_no_secret_shaped_substrings() -> None:
    text_lower = INSTALLER.read_text(encoding="utf-8").lower()
    offenders = [tok for tok in FORBIDDEN_SECRET_SHAPED_SUBSTRINGS if tok in text_lower]
    assert offenders == [], f"Installer script'inde gizli/sifre benzeri alt-dizeler bulundu: {offenders}"


def test_installer_has_no_credential_or_password_parameter() -> None:
    text_lower = INSTALLER.read_text(encoding="utf-8").lower()
    for forbidden_param in ("[string]$password", "[string]$credential", "-credential", "$cred"):
        assert forbidden_param not in text_lower


def test_two_locked_unproven_launchers_were_not_used_or_created() -> None:
    """TD-034 kapsaminda, onceki bir gorevde kanitsiz/uydurulmus oldugu icin
    kilitlenen iki launcher dosyasi ADI ALTINDA HICBIR SEY olusturulmadi ve
    installer script'i bu isimleri referans etmiyor."""
    for locked_path in LOCKED_UNPROVEN_LAUNCHERS:
        assert not locked_path.exists(), f"Kilitli/uydurulmamis dosya olusturulmus: {locked_path}"

    installer_text = INSTALLER.read_text(encoding="utf-8")
    assert "watch_bys360_live_waitress80.ps1" not in installer_text
    assert "run_performance_mail_reminder_09.ps1" not in installer_text


# ---------------------------------------------------------------------------
# 2) Davranis sozlesmesi: mock/dry-run harness ile.
# ---------------------------------------------------------------------------


def test_default_dry_run_makes_zero_scheduled_task_calls_and_exits_zero(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(project_root, tmp_path / "harness")

    assert harness_result["success"] is True, f"Dry-run basarisiz oldu: {harness_result.get('error')}"
    assert harness_result["exit_code"] == 0
    assert harness_result["mock_calls"] == [], (
        "Varsayilan (dry-run) calistirma, HICBIR mock Scheduled Task cmdlet'ini "
        f"cagirmamaliydi. Cagrilar: {harness_result['mock_calls']}"
    )
    assert "PLAN_OK" in harness_result["stdout"]


def test_apply_without_existing_task_registers_it_with_correct_action(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")
    run_server = project_root / "run_server.py"
    python_exe = project_root / ".venv" / "Scripts" / "python.exe"

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=False, port=80,
    )

    assert harness_result["success"] is True, f"Apply basarisiz oldu: {harness_result.get('error')}"
    assert "APPLY_OK" in harness_result["stdout"]

    calls = harness_result["mock_calls"]
    get_calls = [c for c in calls if c.get("Cmdlet") == "Get-ScheduledTask"]
    action_calls = [c for c in calls if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    register_calls = [c for c in calls if c.get("Cmdlet") == "Register-ScheduledTask"]
    set_calls = [c for c in calls if c.get("Cmdlet") == "Set-ScheduledTask"]

    assert len(get_calls) == 1, "Apply modu, carpisma korumasi icin tam olarak bir Get-ScheduledTask cagirmali."
    assert len(register_calls) == 1, "Mevcut gorev yokken tam olarak bir Register-ScheduledTask cagrisi beklenir."
    assert len(set_calls) == 0, "Mevcut gorev yokken Set-ScheduledTask cagrilmamali."

    assert len(action_calls) == 1
    action = action_calls[0]
    assert str(run_server) in action["Argument"], "Action, run_server.py'ye isaret etmeli."
    assert str(python_exe) in action["Argument"], "Action, venv python.exe'yi cagirmali."
    assert "'80'" in action["Argument"] or "= '80'" in action["Argument"], "Port 80 action komutuna gecirilmeli."
    assert action["WorkingDirectory"] == str(project_root)

    # Hicbir gercek/mock Unregister/Start/Stop/schtasks cagrisi olmamali.
    other_forbidden = [c for c in calls if c.get("Cmdlet") in ("Unregister-ScheduledTask", "Start-ScheduledTask", "Stop-ScheduledTask", "schtasks")]
    assert other_forbidden == []


def test_apply_with_custom_port_is_reflected_in_action_command(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=False, port=8080,
    )

    assert harness_result["success"] is True
    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    assert len(action_calls) == 1
    assert "8080" in action_calls[0]["Argument"]
    assert "APP_PORT" in action_calls[0]["Argument"]


def test_apply_action_sets_pythonutf8_env_var(tmp_path: Path) -> None:
    """Windows Scheduled Task redirected stdout defaults to the system ANSI
    codepage (cp1252) -- proven directly on the live "BYS360 Live Waitress 80"
    task to kill run_server.py's Turkish startup print before Waitress ever
    binds the port. The installer must set PYTHONUTF8=1 on the task action
    as one of two independent defense layers (the other being run_server.py's
    own _ensure_utf8_stdio() in-process reconfigure)."""
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=False,
    )

    assert harness_result["success"] is True
    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    assert len(action_calls) == 1
    argument = action_calls[0]["Argument"]
    assert "PYTHONUTF8" in argument
    assert "PYTHONUTF8 = '1'" in argument


def test_apply_action_sets_pythonioencoding_env_var(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=False,
    )

    assert harness_result["success"] is True
    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    assert len(action_calls) == 1
    argument = action_calls[0]["Argument"]
    assert "PYTHONIOENCODING" in argument
    assert "PYTHONIOENCODING = 'utf-8'" in argument


def test_apply_action_still_sets_app_port_alongside_utf8_env_vars(tmp_path: Path) -> None:
    """The new PYTHONUTF8/PYTHONIOENCODING assignments must not have
    displaced the pre-existing APP_PORT assignment in the same inner
    command."""
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=False, port=8080,
    )

    assert harness_result["success"] is True
    action_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "New-ScheduledTaskAction"]
    argument = action_calls[0]["Argument"]
    assert "APP_PORT" in argument and "8080" in argument
    assert "PYTHONUTF8" in argument
    assert "PYTHONIOENCODING" in argument


def test_apply_with_existing_task_is_refused_without_confirm_replace(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=True, confirm_replace=False,
    )

    assert harness_result["success"] is False, "Mevcut gorev varken -ConfirmReplace olmadan sessizce basarili olmamali."
    assert "zaten mevcut" in (harness_result.get("error") or "").lower()
    assert "ConfirmReplace" in (harness_result.get("error") or "")

    calls = harness_result["mock_calls"]
    mutating = [c for c in calls if c.get("Cmdlet") in ("Register-ScheduledTask", "Set-ScheduledTask", "Unregister-ScheduledTask")]
    assert mutating == [], f"Onay olmadan hicbir mutasyon cagrisi yapilmamaliydi: {mutating}"

    # Get-ScheduledTask carpisma kontrolu icin cagrilmis olmali (bu bir okuma,
    # mutasyon degil).
    get_calls = [c for c in calls if c.get("Cmdlet") == "Get-ScheduledTask"]
    assert len(get_calls) == 1


def test_apply_with_existing_task_and_confirm_replace_succeeds_with_exactly_one_set_call(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=True, confirm_replace=True,
    )

    assert harness_result["success"] is True, f"ConfirmReplace ile apply basarisiz oldu: {harness_result.get('error')}"
    assert "APPLY_OK" in harness_result["stdout"]

    calls = harness_result["mock_calls"]
    register_calls = [c for c in calls if c.get("Cmdlet") == "Register-ScheduledTask"]
    set_calls = [c for c in calls if c.get("Cmdlet") == "Set-ScheduledTask"]

    assert len(set_calls) == 1, "ConfirmReplace ile mevcut gorev icin tam olarak bir Set-ScheduledTask cagrisi beklenir."
    assert len(register_calls) == 0, "Mevcut gorev guncellenirken Register-ScheduledTask cagrilmamali (Set kullanilmali)."


@pytest.mark.parametrize("apply_mode", [False, True], ids=["dry_run", "apply"])
def test_missing_python_exe_causes_throw_with_zero_mock_calls(apply_mode: bool, tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox", include_python=False, include_run_server=True)

    harness_result = _run_mocked_installer(project_root, tmp_path / "harness", apply=apply_mode)

    assert harness_result["success"] is False, "Python.exe eksikken installer sessizce basarili olmamali."
    assert "Python bulunamadi" in (harness_result.get("error") or "")
    assert harness_result["mock_calls"] == []


@pytest.mark.parametrize("apply_mode", [False, True], ids=["dry_run", "apply"])
def test_missing_run_server_causes_throw_with_zero_mock_calls(apply_mode: bool, tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox", include_python=True, include_run_server=False)

    harness_result = _run_mocked_installer(project_root, tmp_path / "harness", apply=apply_mode)

    assert harness_result["success"] is False, "run_server.py eksikken installer sessizce basarili olmamali."
    assert "run_server.py bulunamadi" in (harness_result.get("error") or "")
    assert harness_result["mock_calls"] == []


def test_apply_registers_with_configured_task_name(tmp_path: Path) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(
        project_root, tmp_path / "harness", apply=True, existing_task=False,
        task_name="BYS360 Live Waitress 80",
    )

    assert harness_result["success"] is True
    register_calls = [c for c in harness_result["mock_calls"] if c.get("Cmdlet") == "Register-ScheduledTask"]
    assert len(register_calls) == 1
    assert register_calls[0]["TaskName"] == "BYS360 Live Waitress 80"


def test_idempotent_plan_output_stable_across_repeated_dry_runs(tmp_path: Path) -> None:
    """Dry-run cikisi, ayni girdilerle iki kez calistirildiginda hicbir
    Scheduled Task durumuna bagli olmadigindan (hicbir sorgu yapilmadigindan)
    tutarli/kararli olmalidir."""
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    first = _run_mocked_installer(project_root, tmp_path / "harness1")
    second = _run_mocked_installer(project_root, tmp_path / "harness2")

    assert first["success"] is True
    assert second["success"] is True
    assert first["mock_calls"] == [] == second["mock_calls"]
