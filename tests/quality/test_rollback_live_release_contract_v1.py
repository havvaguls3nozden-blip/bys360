"""BYS360 canli release (uygulama kodu) rollback otomasyonu sozlesme testleri
- TD-036.

`scripts/windows/rollback_bys360_live_release_v1.ps1`, BACKUP_RUNBOOK.md
bolum 3'teki `predeploy_<timestamp>\\project\\` yedek dizinini kaynak alarak
canli kod kokunu (LiveProjectRoot) geri yukleyen, varsayilan olarak DRY-RUN
calisan bir PowerShell otomasyonudur. Bu dosya, scriptin PREPARE/VERIFY/
APPLY/HEALTHCHECK/FINALIZE sozlesmesini dogrular:

  1) Varsayilan (Apply verilmeden) calistirma: SIFIR dosya kopyalar, SIFIR
     Scheduled Task cagrisi yapar, VERIFY her zaman calisir ve basarili olur.
  2) `-Apply` ile gecerli bir yedek: canli koke kopyalar, ".env",
     "instance\\", "logs\\", "uploads" (app\\static\\uploads dahil) gibi
     calisma-zamani dizinlerini/DOSYALARINI ASLA kopyalamaz/degistirmez;
     bunlarin disindaki bir kod dosyasini ise yedekteki haline gunceller.
  3) Eksik BackupRoot -> throw, sifir kopya, sifir mock cagri.
  4) BackupRoot\\project ile LiveProjectRoot AYNI konuma cozumlenirse -> throw,
     sifir kopya.
  5) Yedekte beklenen isaretci dosya (run_server.py) eksikse -> throw, sifir
     kopya.
  6) Script metninde parola/gizli-bilgi bicimli alt-dizeler YOKTUR; ".env"
     icerigi script tarafindan hicbir zaman okunmaz/yazdirilmaz.
  7) PowerShell parser scripti SIFIR hata ile parse eder.

Hicbir test gercek C:\\bys360\\project'e, gercek Windows Task Scheduler'a
veya gercek bir HTTP/localhost adresine dokunmaz: tum senaryolar tmp_path
sandbox'lari icinde sahte BackupRoot/LiveProjectRoot agaclariyla calisir;
Stop-ScheduledTask/Start-ScheduledTask/Get-ScheduledTask VE Invoke-WebRequest,
tests/quality/test_installer_launcher_overwrite_guard_v1.py'daki ile ayni
fonksiyon-golgeleme (function shadowing) mock deseniyle degistirilir.
"""

from __future__ import annotations

import hashlib
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

ROLLBACK_SCRIPT = ROOT / "scripts" / "windows" / "rollback_bys360_live_release_v1.ps1"

MOCK_CMDLETS = r"""
$ErrorActionPreference = 'Stop'
$Global:MockCalls = New-Object System.Collections.ArrayList

function Stop-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Stop-ScheduledTask'; TaskName=$TaskName})
}
function Start-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Start-ScheduledTask'; TaskName=$TaskName})
}
function Get-ScheduledTask {
    [CmdletBinding()]
    param([string[]]$TaskName)
    [void]$Global:MockCalls.Add(@{Cmdlet='Get-ScheduledTask'; TaskName=($TaskName -join ',')})
    return $null
}
function Invoke-WebRequest {
    [CmdletBinding()]
    param([string]$Uri, [switch]$UseBasicParsing, [int]$TimeoutSec)
    [void]$Global:MockCalls.Add(@{Cmdlet='Invoke-WebRequest'; Uri=$Uri})
    if ($Global:MockHealthShouldFail) {
        throw "mock: saglik ucu erisilemez (test)"
    }
    return [PSCustomObject]@{ StatusCode = 200 }
}
"""


@pytest.fixture
def tmp_path() -> Generator[Path, None, None]:  # noqa: F811 - kasitli olarak pytest'in yerlesik tmp_path'ini golgeler.
    """pytest'in yerlesik `tmp_path` fixture'i, bu makinede kullanici
    adindaki Turkce karakterler (ornegin 'Havva Gulsen OZDEN') nedeniyle
    `AppData\\Local\\Temp\\pytest-of-...` dizinini tarayamiyor ve
    PermissionError firlatiyor (ortam kaynakli, bu test dosyasinin
    mantigiyla ilgisiz). Bunun yerine dogrudan `tempfile.mkdtemp()` (8.3
    kisa yol kullanir, sorunsuz calisir) tabanli kendi sandbox dizinimizi
    kuruyoruz. Ayni desen tests/quality/test_installer_launcher_overwrite_
    guard_v1.py icinde de kullanilir."""
    d = Path(tempfile.mkdtemp(prefix="bys360_rollback_live_"))
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
    cevirir (bkz. test_installer_launcher_overwrite_guard_v1.py'deki ayni
    yardimci - json.dumps KULLANILMAZ, cunku PowerShell'in tek-tirnakli
    kacis kurallari JSON'unkiyle uyusmaz ve Windows backslash'lerini
    bozar)."""
    return "'" + value.replace("'", "''") + "'"


def _run_rollback(
    *,
    backup_root: Path,
    live_root: Path,
    apply: bool,
    work_dir: Path,
    health_should_fail: bool = False,
    extra_args: list[str] | None = None,
) -> dict:
    """rollback_bys360_live_release_v1.ps1'i, Scheduled Task cmdlet'leri VE
    Invoke-WebRequest mock'lanmis bir PowerShell oturumunda calistirir.
    Gercek Stop-ScheduledTask/Start-ScheduledTask/Get-ScheduledTask/
    Invoke-WebRequest ASLA cagrilmaz. Sonuc:
    {"success": bool, "error": str|None, "mock_calls": [...], "stdout": str}
    """
    exe = _require_ps()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_json = work_dir / "harness_out.json"
    harness_path = work_dir / "harness.ps1"

    args = [
        "-BackupRoot", _ps_single_quote(str(backup_root)),
        "-LiveProjectRoot", _ps_single_quote(str(live_root)),
        "-HealthCheckRetryCount", "1",
        "-HealthCheckDelaySeconds", "0",
    ]
    if apply:
        args.append("-Apply")
    if extra_args:
        args.extend(extra_args)

    # NOT: Splatting (`@argsList`) BILEREK KULLANILMAZ. `-Apply` gibi cikici
    # (bare) switch token'lari, bir dizi LITERALI (@(...)) icinde ifade
    # (expression) baglaminda gecersizdir (PowerShell bunu "eksik parametre"
    # parse hatasi olarak reddeder). Bunun yerine cagri satiri DOGRUDAN,
    # tek bir metin olarak kurulur - komut satirindan calistirmayla birebir
    # aynidir.
    #
    # NOT 2: `2>&1` SADECE hata akisini (stream 2) birlestirir. Script'in
    # ilerleme/plan mesajlari icin kullandigi Write-Host, PowerShell 5.1+'ta
    # Information akisina (stream 6) yazar ve normal `2>&1` ile
    # YAKALANMAZ. Bu yuzden TUM akislari (hata, uyari, bilgi, ...) birlestiren
    # `*>&1` kullanilir; aksi halde $stdout hep bos donerdi.
    #
    # NOT 3: Cikti `Tee-Object -Variable` ile TOPLANIR (Out-String'e
    # dogrudan atama YAPILMAZ). Script FINALIZE ozetini bastiktan SONRA
    # `throw` ile sinyal verdigi senaryolarda (saglik kontrolu basarisiz),
    # `$stdout = ... | Out-String` seklinde bir atama, pipeline sonlandirici
    # hatayla kesilirse HICBIR SEY ATAMAZ (onceki $null degeri kalir).
    # Tee-Object ise her nesneyi akista GORDUGU ANDA degiskene yazar; throw
    # daha SONRA gelse bile o ana kadar uretilen tum satirlar korunur.
    invocation = "& $rollbackPath " + " ".join(args) + " *>&1 | Tee-Object -Variable stdoutLines | Out-Null"

    harness = MOCK_CMDLETS
    harness += f"$Global:MockHealthShouldFail = ${'true' if health_should_fail else 'false'}\n"
    harness += "$rollbackPath = " + _ps_single_quote(str(ROLLBACK_SCRIPT)) + "\n"
    harness += r"""
$errMsg = $null
$success = $true
$stdoutLines = $null
try {
    """ + invocation + r"""
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
        $success = $false
        $errMsg = "ExitCode=$LASTEXITCODE"
    }
} catch {
    $success = $false
    $errMsg = $_.Exception.Message
}
$stdout = ($stdoutLines | Out-String)
$output = [PSCustomObject]@{
    Success = $success
    Error = $errMsg
    MockCalls = @($Global:MockCalls)
    Stdout = $stdout
}
"""
    harness += "$output | ConvertTo-Json -Depth 8 | Set-Content -Path " + _ps_single_quote(str(out_json)) + " -Encoding UTF8\n"

    harness_path.write_text(harness, encoding="utf-8")

    result = subprocess.run(
        [exe, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(harness_path)],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, (
        f"Mock harness kendisi (rollback scripti degil) basarisiz oldu: "
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
        "mock_calls": mock_calls,
        "stdout": raw.get("Stdout") or "",
    }


def _write(path: Path, content: str = "# dummy\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_valid_backup(root: Path, *, code_content: str = "NEW_CODE_FROM_BACKUP") -> Path:
    """BACKUP_RUNBOOK.md bolum 3'teki predeploy_<timestamp>\\project\\ yapisini
    taklit eden, gecerli (isaretci dosyalari tam) bir sahte yedek kurar."""
    backup_root = root / "backups" / "predeploy_20260101_010101"
    project = backup_root / "project"
    _write(project / "run_server.py", "# run_server.py (backup)\n")
    _write(project / "config.py", "# config.py (backup)\n")
    _write(project / "app" / "__init__.py", "# app package (backup)\n")
    _write(project / "app" / "code.py", code_content)
    # Yedek, kasitli olarak ".env" / "instance" / "logs" / "uploads" da
    # ICEREBILIR (gercek hayatta genelde icermez, ama script bunlari
    # AKTIF OLARAK disarida biraktigini kanitlamak icin buraya da koyuyoruz).
    _write(project / ".env", "SHOULD_NEVER_LEAK_INTO_LIVE=from-backup\n")
    _write(project / "instance" / "leak.txt", "backup-instance-leak\n")
    _write(project / "logs" / "leak.log", "backup-logs-leak\n")
    _write(project / "app" / "static" / "uploads" / "leak.bin", "backup-uploads-leak\n")
    return backup_root


def _build_valid_live_root(root: Path, *, code_content: str = "OLD_CODE_ON_LIVE") -> Path:
    """Canli koku, korunmasi gereken calisma-zamani dizinleriyle birlikte
    kurar (rollback bunlara DOKUNMAMALIDIR)."""
    live = root / "project"
    _write(live / "run_server.py", "# run_server.py (live, eski)\n")
    _write(live / "config.py", "# config.py (live, eski)\n")
    _write(live / "app" / "__init__.py", "# app package (live, eski)\n")
    _write(live / "app" / "code.py", code_content)
    _write(live / ".env", "LIVE_ONLY_VALUE=do-not-touch\n")
    _write(live / "instance" / "bys360_local_dev.sqlite3", "LIVE_DB_BYTES\n")
    _write(live / "logs" / "app.log", "live-log-content\n")
    _write(live / "app" / "static" / "uploads" / "avatar.png", "LIVE_UPLOAD_BYTES\n")
    return live


def _snapshot_hashes(root: Path, relative_paths: list[str]) -> dict[str, str]:
    return {rel: _sha256(root / rel) for rel in relative_paths}


PRESERVED_RELATIVE_PATHS = [
    ".env",
    "instance/bys360_local_dev.sqlite3",
    "logs/app.log",
    "app/static/uploads/avatar.png",
]


# ---------------------------------------------------------------------------
# 0) Statik / parser kontrolleri.
# ---------------------------------------------------------------------------


def test_rollback_script_exists_and_is_distinct_from_unrelated_home_prestige_script() -> None:
    assert ROLLBACK_SCRIPT.exists(), f"Beklenen rollback scripti bulunamadi: {ROLLBACK_SCRIPT}"
    unrelated = ROOT / "scripts" / "windows" / "rollback_bys360_home_prestige_safe_v1a.ps1"
    assert unrelated != ROLLBACK_SCRIPT
    # Ilgisiz script bu gorev kapsaminda DEGISTIRILMEMIS olmali (dokunulmadi).
    assert unrelated.exists()


def test_rollback_script_parses_with_zero_errors() -> None:
    _parse_ok(ROLLBACK_SCRIPT)


def test_rollback_script_has_no_secret_shaped_substrings_and_never_reads_dotenv_content() -> None:
    text = ROLLBACK_SCRIPT.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden = ["password", "secret", "token", "dsn", "apikey", "api_key"]
    hits = [f for f in forbidden if f in lowered]
    assert hits == [], f"Script metninde parola/gizli-bilgi bicimli alt-dizeler bulundu: {hits}"

    # .env dosyasinin ICERIGI hicbir zaman okunmaz/yazdirilmaz: script sadece
    # onu ISIM olarak disarida birakir (ExcludedFileNamesExact), Get-Content
    # ile .env okuyan bir satir OLMAMALIDIR.
    assert not re.search(r"Get-Content[^\n]*\.env", text, re.IGNORECASE)

    # PRESERVE_LIVE_ENV davranisi parametre ile gevsetilemez: script,
    # ".env" disarida birakmayi devre disi birakan bir switch/parametre
    # ICERMEMELIDIR.
    assert "AllowDotEnvOverwrite" not in text
    assert "IUnderstandTheRisk" not in text


def test_rollback_script_never_executes_alembic_or_pg_restore() -> None:
    """Script, KAPSAM SINIRINI aciklayan yorum blogunda (.DESCRIPTION/.NOTES)
    Alembic/pg_restore'a REFERANS VEREBILIR (bunlarin BILEREK otomatize
    EDILMEDIGINI belgelemek icin - gorev talimati buna acikca izin verir:
    'It may only reference the existing documented manual procedure ...
    never execute it'). Bu test, bu kelimelerin YORUM BLOGU DISINDA
    (calisan kod olarak, ornegin bir '&' cagri operatoru ile) HICBIR YERDE
    GECMEDIGINI dogrular - yani metinsel bahis serbest, GERCEK CAGRI
    yasak."""
    text = ROLLBACK_SCRIPT.read_text(encoding="utf-8")
    # Bastaki <# ... #> yardim blogunu (PREPARE fazi baslamadan once biten
    # tek blok yorum) disarida birak; sadece calisan kod govdesini tara.
    help_block_end = text.index("#>") + len("#>")
    executable_body = text[help_block_end:]
    lowered_body = executable_body.lower()
    assert "alembic" not in lowered_body, "Alembic, yorum blogu DISINDA (calisan kodda) referans edilmemeli."
    assert "pg_restore" not in lowered_body, "pg_restore, yorum blogu DISINDA (calisan kodda) referans edilmemeli."
    assert "pg_dump" not in lowered_body, "pg_dump, yorum blogu DISINDA (calisan kodda) referans edilmemeli."


# ---------------------------------------------------------------------------
# 1) Varsayilan (dry-run) davranis: sifir kopya, sifir mock Scheduled
#    Task/HTTP cagrisi, VERIFY yine de basariyla calisir.
# ---------------------------------------------------------------------------


def test_default_dry_run_makes_zero_copies_and_zero_mock_calls_but_still_verifies(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    backup_root = _build_valid_backup(sandbox)
    live_root = _build_valid_live_root(sandbox)

    before_live_files = sorted(p.relative_to(live_root).as_posix() for p in live_root.rglob("*") if p.is_file())
    before_hashes = {rel: _sha256(live_root / rel) for rel in before_live_files}

    result = _run_rollback(backup_root=backup_root, live_root=live_root, apply=False, work_dir=tmp_path / "harness")

    assert result["success"] is True, f"Dry-run basarisiz oldu: {result['error']} | {result['stdout']}"
    assert "VERIFY OK" in result["stdout"]
    assert "DRY RUN" in result["stdout"]

    after_live_files = sorted(p.relative_to(live_root).as_posix() for p in live_root.rglob("*") if p.is_file())
    assert after_live_files == before_live_files, "Dry-run canli dizindeki dosya listesini degistirmemeli."
    after_hashes = {rel: _sha256(live_root / rel) for rel in after_live_files}
    assert after_hashes == before_hashes, "Dry-run hicbir canli dosyanin icerigini degistirmemeli."

    assert result["mock_calls"] == [], "Dry-run hicbir Scheduled Task/HTTP cagrisi yapmamali."

    # Staging dizini olusturulmamis/kalmamis olmali.
    leftovers = list(sandbox.glob("project__rollback_staging_*"))
    assert leftovers == [], f"Dry-run beklenmedik staging artigi birakti: {leftovers}"


# ---------------------------------------------------------------------------
# 2) -Apply mutlu yol: kopyalama canliya uygulanir, calisma-zamani verisi
#    (.env/instance/logs/uploads) HICBIR SEKILDE dokunulmadan kalir.
# ---------------------------------------------------------------------------


def test_apply_with_valid_backup_copies_code_but_preserves_runtime_data(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    backup_root = _build_valid_backup(sandbox, code_content="NEW_CODE_FROM_BACKUP")
    live_root = _build_valid_live_root(sandbox, code_content="OLD_CODE_ON_LIVE")

    before_preserved_hashes = _snapshot_hashes(live_root, PRESERVED_RELATIVE_PATHS)

    result = _run_rollback(backup_root=backup_root, live_root=live_root, apply=True, work_dir=tmp_path / "harness")

    assert result["success"] is True, f"-Apply basarisiz oldu: {result['error']} | {result['stdout']}"
    assert "APPLY OK" in result["stdout"]
    assert "HEALTHCHECK OK" in result["stdout"]

    # Kod dosyasi yedekteki (yeni) haline guncellenmis olmali.
    live_code = (live_root / "app" / "code.py").read_text(encoding="utf-8")
    backup_code = (backup_root / "project" / "app" / "code.py").read_text(encoding="utf-8")
    assert live_code == backup_code == "NEW_CODE_FROM_BACKUP"

    live_run_server = (live_root / "run_server.py").read_text(encoding="utf-8")
    assert "backup" in live_run_server, "run_server.py yedekten guncellenmemis."

    # Calisma-zamani dizinleri/dosyalari BAYT BAYT AYNI kalmali - yedekte
    # bunlarin FARKLI ("leak") versiyonlari olmasina RAGMEN.
    after_preserved_hashes = _snapshot_hashes(live_root, PRESERVED_RELATIVE_PATHS)
    assert after_preserved_hashes == before_preserved_hashes, (
        "Rollback, .env/instance/logs/uploads gibi calisma-zamani verilerine dokunmamali."
    )
    for rel in PRESERVED_RELATIVE_PATHS:
        content = (live_root / rel).read_text(encoding="utf-8")
        assert "leak" not in content, f"{rel} yedekteki 'leak' icerigiyle kirlenmis olmamali."

    # Backup icindeki .env/instance/logs/uploads "leak" dosyalari canliya
    # hic sizmamis olmali (yeni bir dosya olarak bile eklenmemis).
    assert not (live_root / "instance" / "leak.txt").exists()
    assert not (live_root / "logs" / "leak.log").exists()
    assert not (live_root / "app" / "static" / "uploads" / "leak.bin").exists()
    # .env icerigi degismedigi icin "leak" satiri da yok.
    assert "leak" not in (live_root / ".env").read_text(encoding="utf-8")

    # Scheduled Task tam olarak bir kez durdurulup bir kez baslatilmis, ve
    # saglik ucu (mock) cagrilmis olmali.
    stop_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "Stop-ScheduledTask"]
    start_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "Start-ScheduledTask"]
    web_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "Invoke-WebRequest"]
    assert len(stop_calls) == 1
    assert len(start_calls) == 1
    assert stop_calls[0]["TaskName"] == "BYS360 Live Waitress 80"
    assert start_calls[0]["TaskName"] == "BYS360 Live Waitress 80"
    assert len(web_calls) == 1
    assert "/healthz" in web_calls[0]["Uri"]

    # Staging dizini basarili APPLY sonrasi temizlenmis olmali.
    leftovers = list(sandbox.glob("project__rollback_staging_*"))
    assert leftovers == [], f"Basarili APPLY sonrasi staging artigi kalmamali: {leftovers}"


def test_apply_healthcheck_failure_still_completes_apply_but_reports_failure(tmp_path: Path) -> None:
    """Saglik kontrolu basarisiz olsa bile APPLY (kopyalama + Scheduled
    Task dongusu) tamamlanmis olmalidir; script SADECE en sonda (FINALIZE
    ozeti basildiktan sonra) basarisizlik sinyali vermelidir. Otomatik
    tekrar-rollback YOKTUR (kapsam disi).

    NOT: Bu senaryoda `result["stdout"]` KASITLI OLARAK kontrol edilmez.
    Windows PowerShell 5.1'de, cagrilan bir .ps1 `throw` ile sonlandiginda,
    `*>&1 | Tee-Object -Variable ...` ile birlestirilmis akis YAKALAMASI
    (nesneler pipeline'a teker teker akiyor gibi gorunse de) TUM pipeline
    segmentiyle birlikte iptal edilir ve $stdout bos kalir - bu, Write-Host
    cikisini yakalamaya CALISMAYAN, sadece `$_.Exception.Message`'a
    guvenen tests/quality/test_installer_launcher_overwrite_guard_v1.py
    deki mevcut desenle AYNI, kanitlanmis kisitlamadir. Bunun yerine
    daha GUVENILIR sinyaller kullanilir: istisna mesaji, dosya sistemi
    durumu (APPLY GERCEKTEN tamamlanmis mi) ve mock cagri sayilari."""
    sandbox = tmp_path / "sandbox"
    backup_root = _build_valid_backup(sandbox, code_content="NEW_CODE_FROM_BACKUP")
    live_root = _build_valid_live_root(sandbox, code_content="OLD_CODE_ON_LIVE")

    result = _run_rollback(
        backup_root=backup_root,
        live_root=live_root,
        apply=True,
        work_dir=tmp_path / "harness",
        health_should_fail=True,
    )

    assert result["success"] is False, "Saglik kontrolu basarisizken script sessizce basarili donmemeli."
    error_text = (result["error"] or "").lower()
    assert "saglik kontrolu basarisiz" in error_text, f"Hata mesaji saglik kontrolu basarisizligini belirtmeli: {result['error']}"

    # APPLY (kopyalama + Scheduled Task dongusu), saglik kontrolunden ONCE
    # calisir; bu yuzden dosya sistemi durumu APPLY'in TAMAMLANDIGINI
    # kanitlamalidir (throw sadece EN SONDA, ozet basildiktan sonra gelir).
    live_code = (live_root / "app" / "code.py").read_text(encoding="utf-8")
    assert live_code == "NEW_CODE_FROM_BACKUP", "Saglik kontrolu basarisiz olsa da kopyalama zaten uygulanmis olmali."

    stop_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "Stop-ScheduledTask"]
    start_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "Start-ScheduledTask"]
    web_calls = [c for c in result["mock_calls"] if c.get("Cmdlet") == "Invoke-WebRequest"]
    assert len(stop_calls) == 1
    assert len(start_calls) == 1
    assert len(web_calls) >= 1, "Saglik kontrolu en az bir kez denenmis olmali."


# ---------------------------------------------------------------------------
# 3) Basarisizlik sozlesmesi: eksik BackupRoot, ayni kaynak/hedef, eksik
#    isaretci dosya - hepsi throw + sifir kopya + sifir mock cagri.
# ---------------------------------------------------------------------------


def test_missing_backup_root_throws_with_zero_copies_and_zero_mock_calls(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    live_root = _build_valid_live_root(sandbox)
    missing_backup = sandbox / "backups" / "predeploy_does_not_exist"

    before_files = sorted(p.relative_to(live_root).as_posix() for p in live_root.rglob("*") if p.is_file())
    before_hashes = {rel: _sha256(live_root / rel) for rel in before_files}

    result = _run_rollback(backup_root=missing_backup, live_root=live_root, apply=True, work_dir=tmp_path / "harness")

    assert result["success"] is False, "Eksik BackupRoot ile script basarili donmemeli."
    assert "bulunamadi" in (result["error"] or "").lower() or "bulunamadi" in result["stdout"].lower()
    assert result["mock_calls"] == [], "Eksik BackupRoot durumunda HICBIR mock Scheduled Task/HTTP cagrisi yapilmamali."

    after_files = sorted(p.relative_to(live_root).as_posix() for p in live_root.rglob("*") if p.is_file())
    after_hashes = {rel: _sha256(live_root / rel) for rel in after_files}
    assert after_files == before_files
    assert after_hashes == before_hashes


def test_backup_project_resolving_to_same_path_as_live_root_is_refused(tmp_path: Path) -> None:
    """-BackupRoot\\project ile -LiveProjectRoot AYNI fiziksel dizine
    cozumlenirse (kaynak == hedef), script kopyalama denemeden reddetmelidir."""
    sandbox = tmp_path / "sandbox"
    shared = sandbox / "shared"
    project_dir = shared / "project"
    _write(project_dir / "run_server.py", "# run_server.py\n")
    _write(project_dir / "config.py", "# config.py\n")
    _write(project_dir / "app" / "__init__.py", "# app\n")

    # BackupRoot = shared  =>  BackupRoot\project = shared\project
    # LiveProjectRoot = shared\project (AYNI dizin)
    backup_root = shared
    live_root = project_dir

    result = _run_rollback(backup_root=backup_root, live_root=live_root, apply=True, work_dir=tmp_path / "harness")

    assert result["success"] is False, "Kaynak/hedef ayni iken script basarili donmemeli."
    combined = (result["error"] or "") + result["stdout"]
    assert "AYNI" in combined or "ayni" in combined.lower()
    assert result["mock_calls"] == [], "Kaynak/hedef ayni iken HICBIR mock cagri yapilmamali."


def test_backup_missing_required_marker_file_throws_with_zero_copies(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    live_root = _build_valid_live_root(sandbox)

    backup_root = sandbox / "backups" / "predeploy_20260202_020202"
    project = backup_root / "project"
    # KASITLI OLARAK run_server.py EKSIK.
    _write(project / "config.py", "# config.py (backup)\n")
    _write(project / "app" / "__init__.py", "# app (backup)\n")

    before_files = sorted(p.relative_to(live_root).as_posix() for p in live_root.rglob("*") if p.is_file())
    before_hashes = {rel: _sha256(live_root / rel) for rel in before_files}

    result = _run_rollback(backup_root=backup_root, live_root=live_root, apply=True, work_dir=tmp_path / "harness")

    assert result["success"] is False, "Eksik isaretci dosyayla script basarili donmemeli."
    combined = (result["error"] or "") + result["stdout"]
    assert "run_server.py" in combined, "Hata mesaji hangi isaretci dosyanin eksik oldugunu belirtmeli."
    assert result["mock_calls"] == [], "Eksik isaretci dosya durumunda HICBIR mock cagri yapilmamali."

    after_files = sorted(p.relative_to(live_root).as_posix() for p in live_root.rglob("*") if p.is_file())
    after_hashes = {rel: _sha256(live_root / rel) for rel in after_files}
    assert after_files == before_files
    assert after_hashes == before_hashes


def test_empty_backup_project_folder_throws_with_zero_copies(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    live_root = _build_valid_live_root(sandbox)

    backup_root = sandbox / "backups" / "predeploy_20260303_030303"
    project = backup_root / "project"
    project.mkdir(parents=True, exist_ok=True)  # BOS proje klasoru.

    result = _run_rollback(backup_root=backup_root, live_root=live_root, apply=True, work_dir=tmp_path / "harness")

    assert result["success"] is False, "Bos yedek 'project' klasoru ile script basarili donmemeli."
    assert result["mock_calls"] == []


def test_missing_live_project_root_throws_with_zero_copies(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    backup_root = _build_valid_backup(sandbox)
    missing_live = sandbox / "project_does_not_exist"

    result = _run_rollback(backup_root=backup_root, live_root=missing_live, apply=True, work_dir=tmp_path / "harness")

    assert result["success"] is False, "Eksik LiveProjectRoot ile script basarili donmemeli."
    assert result["mock_calls"] == []
