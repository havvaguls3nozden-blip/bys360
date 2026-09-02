"""BYS360_DEFECT_Y_SCHEDULED_TASK_UNATTENDED_PRINCIPAL_CONTRACT

Regression contract for a mechanically-confirmed Windows Scheduled Task
defect (Defect Y): ten of the eleven active task installers under
``scripts/windows/`` called ``Register-ScheduledTask``/``Set-ScheduledTask``
without an explicit ``-Principal``. Without one, both cmdlets default to the
CURRENT INTERACTIVE caller's identity with an interactive logon type -- wrong
for every task covered here, since each is a periodic, unattended background
job (daily mail dispatch or a social-media import poll) that must run
whether or not any operator is logged on, including at times (e.g. 07:45,
00:01) when nobody realistically is.

Root-cause confirmation performed before any fix: none of the underlying
Python entry points use Outlook COM automation, Selenium/webdriver, or any
other interactive-desktop-only mechanism (grep across
scripts/communication/*.py and scripts/portal/run_bys360_social_media_embed_
scan_v3b.py found zero win32com/Outlook/selenium/webdriver hits); mail
sending goes through a corporate SMTP service, which works identically
whether the caller is an interactive user or the well-known SYSTEM service
identity. This makes SYSTEM mechanically safe here, not merely convenient.

The exact fix pattern was NOT invented -- it is the pre-existing, ALREADY-
CORRECT precedent already present in this same directory,
``install_bys360_cic_auto_mail_scheduler_task.ps1`` (unchanged by this
remediation, confirmed here as the reference/positive-control case):
``New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest``. The ten
fixed installers reuse this identical shape, made fully explicit per this
remediation wave's own instruction not to rely on API defaults by also
naming ``-LogonType ServiceAccount`` (the objectively correct, documented
LogonType for a well-known service identity -- not a new policy).

This file covers the six installers with the simplest CLI surface (bare
``-ProjectRoot``, or ``-ProjectRoot``+``-Create``) that are not already
exercised by an existing per-installer contract test file:
  - install_bys360_cic_auto_mail_scheduler_task.ps1  (POSITIVE CONTROL --
    already correct before this wave; asserted here to lock it in, not
    fixed)
  - install_bys360_corporate_information_tasks_v3_0.ps1
  - install_bys360_daily_pulse_mail_task.ps1
  - install_bys360_executive_mail_center_v2_tasks.ps1
  - install_bys360_social_auto_import_v3b2_task.ps1
  - install_corporate_information_center_tasks_v3_0_phase2.ps1

The remaining four fixed installers already have their own dedicated,
pre-existing contract test files, extended in place with the same
Principal-value assertions rather than duplicated here:
  - install_bys360_live_waitress_80_task_v1.ps1 ->
    tests/quality/test_waitress_live_task_installer_contract_v1.py
  - install_bys360_daily_mail_tasks_v1_4.ps1 /
    install_bys360_daily_weather_mail_task.ps1 /
    register_bys360_executive_summary_tasks_v2_14_3.ps1 ->
    tests/quality/test_installer_launcher_overwrite_guard_v1.py

register_bys360_executive_summary_tasks_v2_14_1.ps1 is intentionally absent
from every Y test: it is a documented DEPRECATED pure delegator (see its own
top-of-file comment) that produces no ``Register-ScheduledTask``/``Set-
ScheduledTask`` call of its own -- it only invokes
register_bys360_executive_summary_tasks_v2_14_3.ps1, which is already
covered above. NOT_A_DEFECT_FOR_THIS_SCRIPT.

Fixture pattern: proven per this remediation wave's mandatory rule -- the
function-shadowing PowerShell mock technique (same-named functions resolved
in preference to the real ScheduledTasks module cmdlets) already established
in tests/quality/test_waitress_live_task_installer_contract_v1.py and
tests/quality/test_installer_launcher_overwrite_guard_v1.py. No test in this
file calls a real Register-ScheduledTask/Set-ScheduledTask/Get-ScheduledTask/
Unregister-ScheduledTask or touches the real Windows Task Scheduler; every
sandbox is an isolated tempfile.mkdtemp() directory, never the real
C:\\bys360\\project.
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
WINDOWS_DIR = ROOT / "scripts" / "windows"

INSTALL_CIC = WINDOWS_DIR / "install_bys360_cic_auto_mail_scheduler_task.ps1"
INSTALL_CORP_INFO_V3_0 = WINDOWS_DIR / "install_bys360_corporate_information_tasks_v3_0.ps1"
INSTALL_PULSE = WINDOWS_DIR / "install_bys360_daily_pulse_mail_task.ps1"
INSTALL_EXEC_MAIL_CENTER_V2 = WINDOWS_DIR / "install_bys360_executive_mail_center_v2_tasks.ps1"
INSTALL_SOCIAL_AUTO_IMPORT = WINDOWS_DIR / "install_bys360_social_auto_import_v3b2_task.ps1"
INSTALL_CORP_INFO_CENTER_PHASE2 = WINDOWS_DIR / "install_corporate_information_center_tasks_v3_0_phase2.ps1"

REGISTER_V2_14_1 = WINDOWS_DIR / "register_bys360_executive_summary_tasks_v2_14_1.ps1"

EXPECTED_TASK_COUNTS = {
    INSTALL_CIC: 1,
    INSTALL_CORP_INFO_V3_0: 5,
    INSTALL_PULSE: 1,
    INSTALL_EXEC_MAIL_CENTER_V2: 5,
    INSTALL_SOCIAL_AUTO_IMPORT: 1,
    INSTALL_CORP_INFO_CENTER_PHASE2: 5,
}

# Mock cmdlet katmani: gercek ScheduledTasks modulu cmdlet'lerinin ayni
# isimli PowerShell fonksiyonlariyla golgelenmesi. Her cagri
# $Global:MockCalls'a kaydedilir; gercek Windows Task Scheduler'a HICBIR
# sekilde dokunulmaz.
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
    """pytest'in yerlesik `tmp_path` fixture'i bu makinede kullanici adindaki
    Turkce karakterler nedeniyle AppData\\Local\\Temp\\pytest-of-... dizinini
    tarayamiyor. tempfile.mkdtemp() (8.3 kisa yol) tabanli kendi sandbox
    dizinimizi kuruyoruz -- established pattern, bkz. diger Y test dosyalari."""
    d = Path(tempfile.mkdtemp(prefix="bys360_task_principal_"))
    try:
        yield d
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _require_ps() -> str:
    if not PS_EXE:
        pytest.skip("PowerShell CLI bulunamadi; mock/dry-run dogrulama atlandi.")
    return PS_EXE


def _ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _make_dummy_file(path: Path, content: str = "# dummy test fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_fake_project_root(tmp_path: Path) -> Path:
    """Izole (repo disi) sahte bir ProjectRoot kurar, bu dosyadaki ALTI
    installer'in olasi TUM Test-Path kontrollerini gececek sekilde. Gercek
    C:\\bys360\\project'e ASLA dokunulmaz."""
    project_root = tmp_path / "project"
    _make_dummy_file(project_root / ".venv" / "Scripts" / "python.exe", "dummy python.exe\n")
    _make_dummy_file(project_root / "scripts" / "windows" / "run_cic_auto_mail_scheduler.ps1", "# dummy launcher\n")
    _make_dummy_file(project_root / "scripts" / "communication" / "send_daily_pulse_check_mail.py", "# dummy runner\n")
    # BYS360 DEFECT AA closure: install_bys360_daily_pulse_mail_task.ps1 now
    # delegates to this launcher (see tests/quality/test_installer_launcher_
    # overwrite_guard_v1.py for the AA/AG-specific behavioral contract
    # tests) instead of passing shell-redirection syntax as literal argv to
    # python.exe -- its own pre-flight Test-Path guard requires this file.
    _make_dummy_file(project_root / "scripts" / "communication" / "run_daily_pulse_check_mail.ps1", "# dummy launcher\n")
    _make_dummy_file(project_root / "scripts" / "communication" / "run_corporate_information_center_task_v3_0_phase2.py", "# dummy runner\n")
    return project_root


def _run_mocked_installer(target_script: Path, project_root: Path, work_dir: Path, *, extra_switches: tuple[str, ...] = ()) -> dict:
    """target_script'i, TUM Scheduled Task cmdlet'leri mock'lanmis bir
    PowerShell oturumunda bir kez calistirir. Sonuc:
    {"success": bool, "error": str|None, "stdout": str, "mock_calls": [...]}."""
    exe = _require_ps()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "harness_out.json"
    harness_path = work_dir / "harness.ps1"

    switches = "; ".join(f"'{s}' = $true" for s in extra_switches)
    pairs = "'ProjectRoot' = " + _ps_single_quote(str(project_root))
    if switches:
        pairs += "; " + switches

    harness = MOCK_SCHEDULED_TASK_CMDLETS
    harness += "$installerPath = " + _ps_single_quote(str(target_script)) + "\n"
    harness += "$installerArgs = @{" + pairs + "}\n"
    harness += r"""
$errMsg = $null
$success = $true
$stdout = $null
try {
    $stdout = & $installerPath @installerArgs *>&1 | Out-String
} catch {
    $success = $false
    $errMsg = $_.Exception.Message
}
$output = [PSCustomObject]@{
    Success = $success
    Error = $errMsg
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

    raw = json.loads(out_json.read_text(encoding="utf-8-sig"))
    mock_calls = raw.get("MockCalls") or []
    if isinstance(mock_calls, dict):
        mock_calls = [mock_calls]

    return {
        "success": raw["Success"],
        "error": raw.get("Error"),
        "stdout": raw.get("Stdout") or "",
        "mock_calls": mock_calls,
    }


# ---------------------------------------------------------------------------
# Static: every installer covered here parses cleanly.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "installer",
    [INSTALL_CIC, INSTALL_CORP_INFO_V3_0, INSTALL_PULSE, INSTALL_EXEC_MAIL_CENTER_V2, INSTALL_SOCIAL_AUTO_IMPORT, INSTALL_CORP_INFO_CENTER_PHASE2],
    ids=["cic_auto_mail_scheduler", "corporate_information_v3_0", "daily_pulse_mail", "executive_mail_center_v2", "social_auto_import_v3b2", "corporate_information_center_phase2"],
)
def test_installer_file_exists_and_parses_with_zero_syntax_errors(installer: Path) -> None:
    assert installer.exists(), f"Installer bulunamadi: {installer}"
    exe = _require_ps()
    script = (
        "$e=$null;$t=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        f"'{installer}', [ref]$t, [ref]$e);"
        "Write-Output $e.Count"
    )
    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "0", f"{installer} parse hatasi icerir: {result.stdout} {result.stderr}"


# ---------------------------------------------------------------------------
# Behavioral: every fixed installer registers/updates each of its tasks with
# an explicit SYSTEM / ServiceAccount / Highest principal. install_bys360_
# cic_auto_mail_scheduler_task.ps1 is the POSITIVE CONTROL (already correct,
# unchanged) confirming the reference pattern this remediation reused.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "installer,extra_switches",
    [
        (INSTALL_CIC, ()),
        (INSTALL_CORP_INFO_V3_0, ()),
        (INSTALL_PULSE, ()),
        (INSTALL_EXEC_MAIL_CENTER_V2, ()),
        (INSTALL_SOCIAL_AUTO_IMPORT, ("Create",)),
        (INSTALL_CORP_INFO_CENTER_PHASE2, ()),
    ],
    ids=["cic_auto_mail_scheduler", "corporate_information_v3_0", "daily_pulse_mail", "executive_mail_center_v2", "social_auto_import_v3b2", "corporate_information_center_phase2"],
)
def test_every_registered_or_updated_task_uses_explicit_system_service_account_principal(
    installer: Path, extra_switches: tuple[str, ...], tmp_path: Path,
) -> None:
    project_root = _build_fake_project_root(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(installer, project_root, tmp_path / "harness", extra_switches=extra_switches)

    assert harness_result["success"] is True, f"Installer basarisiz oldu: {harness_result.get('error')}"

    calls = harness_result["mock_calls"]
    register_or_set_calls = [c for c in calls if c.get("Cmdlet") in ("Register-ScheduledTask", "Set-ScheduledTask")]

    expected_count = EXPECTED_TASK_COUNTS[installer]
    assert len(register_or_set_calls) == expected_count, (
        f"{installer.name}: {expected_count} gorev kaydi/guncellemesi beklenirken "
        f"{len(register_or_set_calls)} gorundu: {register_or_set_calls!r}"
    )

    for call in register_or_set_calls:
        principal = call.get("Principal") or {}
        assert principal.get("UserId") == "SYSTEM", (
            f"{installer.name}: {call.get('TaskName')!r} gorevi acikca SYSTEM principal'i "
            f"almali (varsayilan/interaktif caller degil). Gecen deger: {principal!r}"
        )
        assert principal.get("RunLevel") == "Highest", (
            f"{installer.name}: {call.get('TaskName')!r} gorevi acikca Highest RunLevel "
            f"almali. Gecen deger: {principal!r}"
        )
        if installer != INSTALL_CIC:
            # install_bys360_cic_auto_mail_scheduler_task.ps1 is the
            # POSITIVE CONTROL: already correct before this wave, and
            # deliberately left byte-unchanged (its own literal source
            # pattern is locked separately, below). It only ever passed
            # -UserId/-RunLevel, never -LogonType -- this remediation's
            # explicit-LogonType strengthening applies only to the five
            # installers actually fixed by Defect Y.
            assert principal.get("LogonType") == "ServiceAccount", (
                f"{installer.name}: {call.get('TaskName')!r} gorevi acikca ServiceAccount "
                f"LogonType almali. Gecen deger: {principal!r}"
            )


def test_cic_installer_source_still_matches_the_reference_principal_pattern_unchanged() -> None:
    """install_bys360_cic_auto_mail_scheduler_task.ps1 was the ALREADY-CORRECT
    reference pattern this whole remediation wave reused (not invented) --
    lock its own literal source pattern in place so a future edit cannot
    silently regress the one installer that was already right."""
    text = INSTALL_CIC.read_text(encoding="utf-8")
    assert 'New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest' in text


# ---------------------------------------------------------------------------
# register_bys360_executive_summary_tasks_v2_14_1.ps1: documented deprecated
# pure delegator, NOT_A_DEFECT_FOR_THIS_SCRIPT -- confirm it produces zero
# Scheduled Task mutation calls of its own (it must fully delegate).
# ---------------------------------------------------------------------------


def test_v2_14_1_deprecated_delegator_makes_no_scheduled_task_calls_of_its_own() -> None:
    text = REGISTER_V2_14_1.read_text(encoding="utf-8")
    assert "Register-ScheduledTask" not in text
    assert "Set-ScheduledTask" not in text
    assert "New-ScheduledTaskPrincipal" not in text
