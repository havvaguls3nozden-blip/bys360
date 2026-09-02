"""BYS360 Yonetici Ozeti installer canonicalization sozlesme testleri.

Onceki turda (bkz. tests/quality/test_installer_launcher_overwrite_guard_v1.py)
register_bys360_executive_summary_tasks_v2_14_3.ps1 icin bir
"Assert-LauncherReady" guvenlik kontrati kilitlenmisti. Bu turda, AYRI bir
sorun duzeltildi: register_bys360_executive_summary_tasks_v2_14_1.ps1 (eski
script) ile register_bys360_executive_summary_tasks_v2_14_3.ps1 (kanonik
script) AYNI Scheduled Task TaskName'lerini ("BYS360 Executive Summary 0001" /
"BYS360 Executive Summary 0830") FARKLI mekanizmalarla kuruyordu:
  - v2_14_1 (eski, ONCEKI hali): launcher'siz, inline "-Command" ile python'u
    dogrudan cagiran KENDI Action'ini uretiyordu (Assert-LauncherReady /
    icerik-sozlesmesi kontrolu YOKTU).
  - v2_14_3 (kanonik): kaynak kontrollu run_executive_summary_0001.ps1 /
    run_executive_summary_0830.ps1 launcher dosyalarina "-File" ile baglanan,
    Test-Path + ParseFile + icerik-sozlesmesi (Assert-LauncherReady) ile
    korunan bir Action uretiyor.
Hangisi son calistirilirse ayni TaskName'in Action'i O OLUYORDU -> ongorulemeyen
production davranisi (registry drift).

Duzeltme: v2_14_1 artik KENDI Action'ini URETMEZ. Sadece:
  1) Kanonik register_bys360_executive_summary_tasks_v2_14_3.ps1'in kendi
     $PSScriptRoot'unda (v2_14_1 ile AYNI dizinde) var olup olmadigini
     Test-Path ile kontrol eder; yoksa acik `throw` ile durur.
  2) Varsa `& $CanonicalScript -ProjectRoot $ProjectRoot` ile TAMAMEN ona
     delege eder (kendi Register-ScheduledTask/New-ScheduledTaskAction
     cagrisi YAPMAZ).

Bu dosya, bu delegasyon davranisini dogrular:
  A) v2_14_1 calistirildiginda KENDI BASINA farkli bir Scheduled Task Action
     URETMEZ; sadece v2_14_3 uzerinden (mock ortaminda) gecen action'lar
     gorulur.
  B) Kanonik v2_14_3 scripti (v2_14_1 ile ayni dizinde) bulunamazsa v2_14_1
     acik `throw` ile durur (sessizce devam etmez / kendi eski davranisina
     geri donmez).
  C) Ayni TaskName icin v2_14_1 uzerinden (delege ederek) uretilen Action,
     v2_14_3'un DOGRUDAN calistirilmasiyla uretilen Action ile BIREBIR
     AYNIDIR (registry drift artik mumkun degil).
  D) Zincir (v2_14_1 -> v2_14_3) launcher dosyalarinin ICERIGINE dokunmaz ve
     idempotenttir (iki kez calistirildiginda launcher hash'i degismez, uretilen
     action'lar birebir ayni kalir).
  E) Bir launcher eksik/bozuksa hata zincir boyunca (v2_14_3 -> v2_14_1) dogru
     sekilde yukari tasinir; hicbir Scheduled Task mutasyonu denenmez.
  F) Hicbir test gercek Register-ScheduledTask/Unregister-ScheduledTask
     cagirmaz (tum Scheduled Task cmdlet'leri mock'lanir); gercek mail/
     executive summary script'i de CALISTIRILMAZ (v2_14_3 sadece Test-Path/
     ParseFile/icerik kontrolu yapar, launcher'i asla invoke etmez).

Not: Bu dosya, onceki turda kilitlenmis olan
tests/quality/test_installer_launcher_overwrite_guard_v1.py dosyasindaki
mock/dry-run desenini (MOCK_SCHEDULED_TASK_CMDLETS + PowerShell harness)
REFERANS ALIR ve ayni usluptaki yardimci fonksiyonlari bu dosya icin
kendi icinde (bagimsiz calisabilecek sekilde) yeniden kurar. Mevcut dosyaya
dokunulmadi (regresyonsuz).
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

REGISTER_V2_14_1 = ROOT / "scripts" / "windows" / "register_bys360_executive_summary_tasks_v2_14_1.ps1"
REGISTER_V2_14_3 = ROOT / "scripts" / "windows" / "register_bys360_executive_summary_tasks_v2_14_3.ps1"

CANONICAL_EXEC_MORNING = ROOT / "scripts" / "windows" / "run_executive_summary_0830.ps1"
CANONICAL_EXEC_NIGHT = ROOT / "scripts" / "windows" / "run_executive_summary_0001.ps1"

TASK_NAME_NIGHT = "BYS360 Executive Summary 0001"
TASK_NAME_MORNING = "BYS360 Executive Summary 0830"

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
    Turkce karakterler nedeniyle `AppData\\Local\\Temp\\pytest-of-...` dizinini
    tarayamiyor ve PermissionError firlatiyor (ortam kaynakli). Bunun yerine
    dogrudan `tempfile.mkdtemp()` tabanli kendi sandbox dizinimizi kuruyoruz
    (onceki turdaki test_installer_launcher_overwrite_guard_v1.py ile ayni
    cozum)."""
    d = Path(tempfile.mkdtemp(prefix="bys360_exec_canon_"))
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
    cevirir (json.dumps KULLANILMAZ - ters egik cizgi kacis kurallari
    uyusmuyor). Bkz. test_installer_launcher_overwrite_guard_v1.py'deki ayni
    isimli yardimci fonksiyon."""
    return "'" + value.replace("'", "''") + "'"


def _run_mocked_installer(target_script: Path, project_root: Path, work_dir: Path, runs: int = 1) -> dict:
    """target_script'i, TUM Scheduled Task cmdlet'leri mock'lanmis bir
    PowerShell oturumunda `runs` kez calistirir. Gercek Register-ScheduledTask/
    Unregister-ScheduledTask/Get-ScheduledTask ASLA cagrilmaz. target_script
    icinde ic ice `&` cagrilari olsa bile (ornegin v2_14_1 -> v2_14_3),
    mock fonksiyonlari $Global: kapsaminda tanimlandigindan tum cagri
    derinliklerinde gecerli kalir (PowerShell fonksiyon cozumlemesi kapsam
    zincirini yukari dogru tarar)."""
    exe = _require_ps()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "harness_out.json"
    harness_path = work_dir / "harness.ps1"

    harness = MOCK_SCHEDULED_TASK_CMDLETS
    harness += "\n$installerPath = " + _ps_single_quote(str(target_script)) + "\n"
    harness += "$projectRoot = " + _ps_single_quote(str(project_root)) + "\n"
    harness += f"$runs = {runs}\n"
    harness += r"""
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


BROKEN_PS1_FIXTURE = 'param()\nif ($true) {\n    Write-Host "unterminated block, deliberately broken for test\n'


def _build_exec_summary_sandbox(tmp_path: Path, *, include_morning: bool = True,
                                 include_night: bool = True,
                                 morning_content: str | None = None,
                                 night_content: str | None = None) -> Path:
    """register_bys360_executive_summary_tasks_v2_14_3.ps1 (ve onu cagiran
    v2_14_1) icin izole ProjectRoot kurar. v2_14_3'un launcher yollari
    $ProjectRoot'a GORELI oldugundan (Join-Path $ProjectRoot
    "scripts\\windows\\run_executive_summary_08 30.ps1" vb.), bu sandbox
    yeterlidir - v2_14_1/v2_14_3 SCRIPT dosyalarinin kendisi repodaki gercek
    konumlarindan calisir (asagida REGISTER_V2_14_1 / REGISTER_V2_14_3)."""
    project_root = tmp_path / "project"
    _make_dummy_file(project_root / ".venv" / "Scripts" / "python.exe", "dummy python.exe\n")

    if include_morning:
        content = morning_content if morning_content is not None else CANONICAL_EXEC_MORNING.read_text(encoding="utf-8")
        _make_dummy_file(project_root / "scripts" / "windows" / "run_executive_summary_0830.ps1", content)

    if include_night:
        content = night_content if night_content is not None else CANONICAL_EXEC_NIGHT.read_text(encoding="utf-8")
        _make_dummy_file(project_root / "scripts" / "windows" / "run_executive_summary_0001.ps1", content)

    return project_root


def _copy_v2_14_1_without_canonical_sibling(tmp_path: Path) -> Path:
    """v2_14_1'in ($PSScriptRoot uzerinden) kanonik v2_14_3 scriptini KENDI
    dizininde aradigini dogrulamak icin: v2_14_1'in GERCEK icerigini
    (degistirmeden, oldugu gibi) izole bir dizine kopyalar ve o dizine
    KASITLI olarak v2_14_3'u KOYMAZ. Boylece "kanonik script bulunamadi"
    senaryosu, repodaki gercek v2_14_3'u silmeye/gizlemeye gerek kalmadan
    (worktree disina cikmadan) test edilebilir."""
    isolated_dir = tmp_path / "isolated_v2_14_1_no_sibling"
    isolated_dir.mkdir(parents=True, exist_ok=True)
    copy_path = isolated_dir / "register_bys360_executive_summary_tasks_v2_14_1.ps1"
    copy_path.write_text(REGISTER_V2_14_1.read_text(encoding="utf-8"), encoding="utf-8")
    return copy_path


def _action_calls(mock_calls: list[dict]) -> list[dict]:
    return [c for c in mock_calls if c.get("Cmdlet") == "New-ScheduledTaskAction"]


def _register_calls(mock_calls: list[dict]) -> list[dict]:
    return [c for c in mock_calls if c.get("Cmdlet") == "Register-ScheduledTask"]


# ---------------------------------------------------------------------------
# 0) Parser saglamligi (bagimsiz olarak bu dosyada da tekrar dogrulanir).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [REGISTER_V2_14_1, REGISTER_V2_14_3],
    ids=["register_v2_14_1", "register_v2_14_3"],
)
def test_parses_with_zero_errors(path: Path) -> None:
    assert path.exists(), f"Beklenen script bulunamadi: {path}"
    _parse_ok(path)


# ---------------------------------------------------------------------------
# A + C) v2_14_1 KENDI BASINA farkli bir Action URETMEZ; v2_14_1 uzerinden
#        (delege ederek) uretilen Action, v2_14_3'un DOGRUDAN calistirilmasiyla
#        uretilen Action ile BIREBIR AYNIDIR.
# ---------------------------------------------------------------------------


def test_v2_14_1_produces_no_action_of_its_own_only_relays_v2_14_3s_actions(tmp_path: Path) -> None:
    """v2_14_1 calistirildiginda toplamda TAM OLARAK 2 New-ScheduledTaskAction
    cagrisi gorulmeli (biri gece, biri sabah gorevi icin) - bunlarin HEPSI
    v2_14_3'un ic cagrisindan gelir. Eger v2_14_1 hala kendi eski (launcher'siz,
    inline -Command) Action'ini uretiyor olsaydi, bu sayi 4'e cikardi (kendi 2'si
    + v2_14_3'un 2'si) veya launcher'siz farkli bir Argument iceren fazladan
    action'lar gorulurdu."""
    project_root = _build_exec_summary_sandbox(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(REGISTER_V2_14_1, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]
    assert run["Success"] is True, f"v2_14_1 calistirilmasi basarisiz oldu: {run.get('Error')}"

    action_calls = _action_calls(harness_result["mock_calls"])
    assert len(action_calls) == 2, (
        "v2_14_1 calistirildiginda TAM OLARAK 2 New-ScheduledTaskAction cagrisi "
        f"bekleniyordu (sadece v2_14_3'ten delege), {len(action_calls)} bulundu: {action_calls}"
    )

    morning_launcher = project_root / "scripts" / "windows" / "run_executive_summary_0830.ps1"
    night_launcher = project_root / "scripts" / "windows" / "run_executive_summary_0001.ps1"

    # v2_14_1'in ESKI (silinen) davranisi launcher'siz, inline "-Command" ile
    # python'u dogrudan cagiran bir Argument uretiyordu. Bu artik hicbir
    # action cagrisinda GORULMEMELI.
    for call in action_calls:
        argument = call.get("Argument") or ""
        assert "-File" in argument, f"Action launcher-tabanli '-File' kullanmiyor (eski davranis geri donmus olabilir): {call}"
        assert "-Command" not in argument, f"Action hala eski inline '-Command' bicimini kullaniyor: {call}"
        assert (str(morning_launcher) in argument) or (str(night_launcher) in argument), (
            f"Action beklenen kanonik launcher yollarindan hicbirini referans etmiyor: {call}"
        )


def test_v2_14_1_relayed_action_is_byte_for_byte_identical_to_v2_14_3_direct_run(tmp_path: Path) -> None:
    """Ayni TaskName ('BYS360 Executive Summary 0001' / '...0830') icin,
    v2_14_1 uzerinden (delege ederek) uretilen Action'in Execute/Argument/
    WorkingDirectory alanlari, v2_14_3'un DOGRUDAN calistirilmasiyla uretilen
    Action ile BIREBIR AYNI olmalidir. Bu, "registry drift" (iki farkli
    mekanizmanin ayni TaskName icin farkli Action uretmesi) riskinin ortadan
    kalktigini kanitlar."""
    project_root_chain = _build_exec_summary_sandbox(tmp_path / "sandbox_chain")
    project_root_direct = _build_exec_summary_sandbox(tmp_path / "sandbox_direct")

    chain_result = _run_mocked_installer(REGISTER_V2_14_1, project_root_chain, tmp_path / "harness_chain", runs=1)
    direct_result = _run_mocked_installer(REGISTER_V2_14_3, project_root_direct, tmp_path / "harness_direct", runs=1)

    assert chain_result["results"][0]["Success"] is True, chain_result["results"][0].get("Error")
    assert direct_result["results"][0]["Success"] is True, direct_result["results"][0].get("Error")

    chain_actions = _action_calls(chain_result["mock_calls"])
    direct_actions = _action_calls(direct_result["mock_calls"])

    assert len(chain_actions) == 2
    assert len(direct_actions) == 2

    # project_root_chain ve project_root_direct farkli tmp dizinlerinde
    # oldugundan launcher YOLLARI (WorkingDirectory/Argument icindeki mutlak
    # yol) birebir string olarak farkli olacaktir; bu yuzden yapisal
    # karsilastirma yapiyoruz: her iki tarafta da morning/night launcher'a
    # dogru sekilde, ayni Execute degeriyle ve ayni "-NoProfile
    # -ExecutionPolicy Bypass -File" bicimiyle baglaniyor mu?
    def _by_suffix(actions: list[dict], suffix: str) -> dict:
        matches = [a for a in actions if suffix in (a.get("Argument") or "")]
        assert len(matches) == 1, f"'{suffix}' icin tam olarak 1 action bekleniyordu, {len(matches)} bulundu: {actions}"
        return matches[0]

    for suffix in ("run_executive_summary_0830.ps1", "run_executive_summary_0001.ps1"):
        chain_action = _by_suffix(chain_actions, suffix)
        direct_action = _by_suffix(direct_actions, suffix)

        assert chain_action["Execute"] == direct_action["Execute"] == "powershell.exe"

        # WorkingDirectory farkli sandbox'lardan geldigi icin ayri kontrol
        # edilir (kendi ProjectRoot'una esit olmali), Argument'in BICIMI
        # (launcher dosya adi haric prefix/suffix) birebir ayni olmalidir.
        chain_arg = chain_action["Argument"]
        direct_arg = direct_action["Argument"]
        assert chain_arg.startswith('-NoProfile -ExecutionPolicy Bypass -File "')
        assert direct_arg.startswith('-NoProfile -ExecutionPolicy Bypass -File "')
        assert chain_arg.endswith(f'{suffix}"')
        assert direct_arg.endswith(f'{suffix}"')

        assert chain_action["WorkingDirectory"] == str(project_root_chain)
        assert direct_action["WorkingDirectory"] == str(project_root_direct)

    # Register-ScheduledTask cagrilari da (TaskName + Description) birebir
    # ayni olmali.
    chain_registers = {c["TaskName"]: c["Description"] for c in _register_calls(chain_result["mock_calls"])}
    direct_registers = {c["TaskName"]: c["Description"] for c in _register_calls(direct_result["mock_calls"])}

    assert set(chain_registers) == {TASK_NAME_NIGHT, TASK_NAME_MORNING}
    assert chain_registers == direct_registers, (
        "v2_14_1 zinciri ile v2_14_3 dogrudan calistirmasi ayni TaskName icin "
        f"farkli Register-ScheduledTask cagrisi uretti (registry drift): "
        f"chain={chain_registers} direct={direct_registers}"
    )


# ---------------------------------------------------------------------------
# B) Kanonik v2_14_3 (v2_14_1 ile ayni dizinde) bulunamazsa v2_14_1 acik
#    `throw` ile durur.
# ---------------------------------------------------------------------------


def test_v2_14_1_throws_when_canonical_v2_14_3_is_missing_next_to_it(tmp_path: Path) -> None:
    isolated_v2_14_1 = _copy_v2_14_1_without_canonical_sibling(tmp_path / "isolated")
    assert not (isolated_v2_14_1.parent / "register_bys360_executive_summary_tasks_v2_14_3.ps1").exists()

    # Bu senaryoda ProjectRoot hicbir zaman kullanilmaz (throw, ProjectRoot'a
    # bagli her turlu islemden ONCE gerceklesir); yine de gecerli bir sandbox
    # veriyoruz ki "throw'un asil nedeni ProjectRoot eksikligi degil, kanonik
    # script eksikligi" oldugu net olsun.
    project_root = _build_exec_summary_sandbox(tmp_path / "sandbox")

    harness_result = _run_mocked_installer(isolated_v2_14_1, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False, "Kanonik v2_14_3 eksikken v2_14_1 sessizce basarili olmamali."
    error = (run.get("Error") or "")
    assert "kanonik registrasyon scripti bulunamadi" in error.lower(), error
    assert "register_bys360_executive_summary_tasks_v2_14_3.ps1" in error

    # Hicbir Scheduled Task mutasyonu denenmemis olmali (fail-fast, eski
    # davranisa geri donup KENDI Action'ini uretmeye CALISMAMALI).
    assert harness_result["mock_calls"] == []


def test_v2_14_1_does_not_fall_back_to_its_own_legacy_registration_when_canonical_missing(tmp_path: Path) -> None:
    """Ek guvence: kanonik script eksikken v2_14_1'in KAYNAK KODUNDA, throw
    disinda bir 'yedek/legacy' Register-ScheduledTask/New-ScheduledTaskAction
    cagrisi kalmamis olmali (statik tarama). Bu, birinin ileride v2_14_1'e
    'kanonik yoksa eski yontemle devam et' seklinde bir fallback eklemesini
    yakalar."""
    text = REGISTER_V2_14_1.read_text(encoding="utf-8")
    code_lines = [ln for ln in text.splitlines() if not ln.strip().startswith("#")]
    code_text = "\n".join(code_lines)

    assert "New-ScheduledTaskAction" not in code_text, (
        "register_bys360_executive_summary_tasks_v2_14_1.ps1 hala kendi "
        "New-ScheduledTaskAction cagrisini iceriyor; delegasyon tam degil."
    )
    assert "Register-ScheduledTask" not in code_text, (
        "register_bys360_executive_summary_tasks_v2_14_1.ps1 hala kendi "
        "Register-ScheduledTask cagrisini iceriyor; delegasyon tam degil."
    )
    assert "Set-Content" not in code_text and "Out-File" not in code_text, (
        "register_bys360_executive_summary_tasks_v2_14_1.ps1 bir dosyanin "
        "icerigini uretiyor/uzerine yaziyor olabilir (launcher-overwrite riski)."
    )


# ---------------------------------------------------------------------------
# D) Zincir (v2_14_1 -> v2_14_3) launcher dosyalarina dokunmaz ve
#    idempotenttir.
# ---------------------------------------------------------------------------


def test_v2_14_1_chain_never_modifies_canonical_launchers_and_is_idempotent(tmp_path: Path) -> None:
    project_root = _build_exec_summary_sandbox(tmp_path / "sandbox")
    morning = project_root / "scripts" / "windows" / "run_executive_summary_0830.ps1"
    night = project_root / "scripts" / "windows" / "run_executive_summary_0001.ps1"

    hash_morning_before = _sha256(morning)
    hash_night_before = _sha256(night)

    harness_result = _run_mocked_installer(REGISTER_V2_14_1, project_root, tmp_path / "harness", runs=2)

    for run in harness_result["results"]:
        assert run["Success"] is True, f"Run {run['Run']} basarisiz oldu: {run.get('Error')}"

    assert _sha256(morning) == hash_morning_before, "Morning launcher, v2_14_1 zinciri tarafindan degistirildi!"
    assert _sha256(night) == hash_night_before, "Night launcher, v2_14_1 zinciri tarafindan degistirildi!"

    action_calls = _action_calls(harness_result["mock_calls"])
    morning_actions = [c for c in action_calls if str(morning) in (c.get("Argument") or "")]
    night_actions = [c for c in action_calls if str(night) in (c.get("Argument") or "")]

    assert len(morning_actions) == 2, "Her run'da tam olarak bir morning action bekleniyordu."
    assert len(night_actions) == 2, "Her run'da tam olarak bir night action bekleniyordu."
    assert morning_actions[0]["Argument"] == morning_actions[1]["Argument"], "Run'lar arasi morning action degisti (idempotent degil)."
    assert night_actions[0]["Argument"] == night_actions[1]["Argument"], "Run'lar arasi night action degisti (idempotent degil)."


# ---------------------------------------------------------------------------
# E) Eksik/bozuk launcher hatasi zincir boyunca dogru sekilde yukari tasinir.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing,label",
    [("morning", "Executive Summary 0830"), ("night", "Executive Summary 0001")],
)
def test_v2_14_1_chain_throws_when_a_launcher_is_missing(missing: str, label: str, tmp_path: Path) -> None:
    project_root = _build_exec_summary_sandbox(
        tmp_path / "sandbox",
        include_morning=missing != "morning",
        include_night=missing != "night",
    )

    harness_result = _run_mocked_installer(REGISTER_V2_14_1, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False, "Launcher eksikken v2_14_1 zinciri sessizce basarili olmamali."
    error = (run.get("Error") or "")
    assert "launcher bulunamadi" in error.lower(), error
    assert label in error, error

    # Hata v2_14_3'ten (Assert-LauncherReady) geliyor olmali, v2_14_1'in
    # kendi "kanonik script bulunamadi" hatasi DEGIL.
    assert "kanonik registrasyon scripti bulunamadi" not in error.lower()
    assert harness_result["mock_calls"] == []


@pytest.mark.parametrize("broken", ["morning", "night"])
def test_v2_14_1_chain_throws_when_a_launcher_has_invalid_syntax(broken: str, tmp_path: Path) -> None:
    morning_content = BROKEN_PS1_FIXTURE if broken == "morning" else None
    night_content = BROKEN_PS1_FIXTURE if broken == "night" else None
    project_root = _build_exec_summary_sandbox(
        tmp_path / "sandbox",
        morning_content=morning_content,
        night_content=night_content,
    )

    harness_result = _run_mocked_installer(REGISTER_V2_14_1, project_root, tmp_path / "harness", runs=1)
    run = harness_result["results"][0]

    assert run["Success"] is False
    err = (run.get("Error") or "").lower()
    assert "parse hatasi" in err or "sozdizim" in err
    assert harness_result["mock_calls"] == []


# ---------------------------------------------------------------------------
# F) Gercek Scheduled Task / gercek mail gonderimi olmadigi kaniti.
# ---------------------------------------------------------------------------


def test_v2_14_1_chain_only_calls_expected_mocked_cmdlets_no_real_side_effects(tmp_path: Path) -> None:
    """Mock oturumunda gorulen TUM cmdlet cagrilari, MOCK_SCHEDULED_TASK_CMDLETS
    icinde tanimlanan (ve dolayisiyla gercek Windows Task Scheduler'a asla
    dokunmayan) fonksiyonlarla sinirlidir. Ayrica Unregister-ScheduledTask
    (yikici islem) hic cagrilmaz, ve ne v2_14_1 ne de v2_14_3 python.exe'yi
    veya send_daily_executive_summary.py'yi invoke etmez (ikisi de sadece
    Test-Path/ParseFile/icerik kontrolu yapar, launcher'i asla calistirmaz)."""
    project_root = _build_exec_summary_sandbox(tmp_path / "sandbox")
    harness_result = _run_mocked_installer(REGISTER_V2_14_1, project_root, tmp_path / "harness", runs=1)

    assert harness_result["results"][0]["Success"] is True

    allowed_cmdlets = {
        "New-ScheduledTaskAction",
        "New-ScheduledTaskTrigger",
        "New-ScheduledTaskSettingsSet",
        "New-ScheduledTaskPrincipal",
        "Register-ScheduledTask",
        "Get-ScheduledTask",
        "Set-ScheduledTask",
    }
    seen_cmdlets = {c.get("Cmdlet") for c in harness_result["mock_calls"]}
    assert seen_cmdlets <= allowed_cmdlets, f"Beklenmeyen cmdlet cagrisi gorundu: {seen_cmdlets - allowed_cmdlets}"
    assert "Unregister-ScheduledTask" not in seen_cmdlets

    # dummy python.exe fixture'i, gercek bir calistirma olsaydi "dummy
    # python.exe" (fixture icerigi) exec edilmeye calisilir ve PowerShell'de
    # bir yürütülebilir dosya hatasi/istisnasi ile Success=False donerdi.
    # Success True oldugu ve mock cagrilari sadece Scheduled Task tanim
    # cmdlet'lerinden ibaret oldugu icin, dummy python.exe'nin gercekten
    # invoke edilmedigi dolayli olarak da dogrulanmis olur.
    dummy_python = project_root / ".venv" / "Scripts" / "python.exe"
    assert dummy_python.read_text(encoding="utf-8") == "dummy python.exe\n", "Dummy python.exe fixture'i beklenmedik sekilde degisti."
