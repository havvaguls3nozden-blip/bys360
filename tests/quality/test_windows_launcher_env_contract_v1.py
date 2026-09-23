from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]


def _parse_ok(path: Path) -> None:
    """PowerShell dosyasinin gecerli (parse edilebilir) syntax'a sahip oldugunu dogrular.

    pwsh/powershell CLI bu ortamda mevcut degilse test atlanir (Windows disi
    CI ortami); mevcutsa gercek AST parser ile sifir hata beklenir.
    """
    import shutil
    import subprocess

    exe = shutil.which("pwsh") or shutil.which("powershell")
    if not exe:
        pytest.skip("PowerShell CLI bulunamadi; syntax dogrulama atlandi.")

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


def test_cic_auto_mail_scheduler_launcher_exists_and_matches_installer_contract() -> None:
    launcher = ROOT / "scripts" / "windows" / "run_cic_auto_mail_scheduler.ps1"
    installer = ROOT / "scripts" / "windows" / "install_bys360_cic_auto_mail_scheduler_task.ps1"

    assert launcher.exists(), "CIC auto mail scheduler launcher eksik."
    assert installer.exists(), "CIC auto mail scheduler installer eksik."

    launcher_text = launcher.read_text(encoding="utf-8")
    installer_text = installer.read_text(encoding="utf-8")

    # install_bys360_cic_auto_mail_scheduler_task.ps1 tam olarak bu yolu bekliyor.
    assert "run_cic_auto_mail_scheduler.ps1" in installer_text

    # scripts/archive/quality/phase2y-wave1/check_bys360_cic_v3_0_system_auto_mail_scheduler_v1.py
    # gate sozlesmesi: bu ifade dosyada bulunmali.
    assert "cic_auto_mail_scheduler.log" in launcher_text

    # Launcher gercek CIC scheduler python modulunu cagirmali.
    assert "scripts\\scheduled\\run_cic_auto_scheduler.py" in launcher_text

    # Sabit proje kokü + venv python + guvenli guard'lar.
    assert 'C:\\bys360\\project' in launcher_text
    assert '.venv\\Scripts\\python.exe' in launcher_text
    assert "Test-Path $Python" in launcher_text
    assert "Test-Path $Script" in launcher_text
    assert "Set-Location $ProjectRoot" in launcher_text
    assert "$LASTEXITCODE" in launcher_text

    # 5 dakikada bir tetiklenen gorev icin ust uste binmeyi engelleyen basit kilit.
    assert "LockPath" in launcher_text

    # Gizli bilgi (parola/token/DSN) loglanmamali.
    for forbidden in ("password", "secret", "token", "dsn", "apikey", "api_key"):
        assert forbidden not in launcher_text.lower()

    _parse_ok(launcher)


def test_daily_weather_personnel_mail_launcher_exists_and_matches_install_bystask_contract() -> None:
    launcher = ROOT / "scripts" / "communication" / "run_daily_weather_personnel_mail.ps1"
    installer_v1_4 = ROOT / "scripts" / "windows" / "install_bys360_daily_mail_tasks_v1_4.ps1"
    weather_runner = ROOT / "scripts" / "communication" / "send_daily_weather_personnel_mail.py"

    assert launcher.exists(), "Daily weather personnel mail launcher eksik."
    assert installer_v1_4.exists(), "Daily mail tasks v1.4 installer eksik."
    assert weather_runner.exists(), "Weather mail runner (python) eksik."

    launcher_text = launcher.read_text(encoding="utf-8")
    installer_text = installer_v1_4.read_text(encoding="utf-8")

    # Install-BysTask -Launcher parametresi tam olarak bu yolu bekliyor.
    assert "run_daily_weather_personnel_mail.ps1" in installer_text
    # Install-BysTask -LogPath parametresi tam olarak bu log dosya adini bekliyor.
    assert "daily_weather_personnel_mail.log" in installer_text

    # Launcher dogru python scriptini cagirmali.
    assert "send_daily_weather_personnel_mail.py" in launcher_text
    assert "daily_weather_personnel_mail.log" in launcher_text

    assert 'C:\\bys360\\project' in launcher_text
    assert '.venv\\Scripts\\python.exe' in launcher_text
    assert "Test-Path $Python" in launcher_text
    assert "Test-Path $Script" in launcher_text
    assert "Set-Location $ProjectRoot" in launcher_text
    assert "$LASTEXITCODE" in launcher_text

    for forbidden in ("password", "secret", "token", "dsn", "apikey", "api_key"):
        assert forbidden not in launcher_text.lower()

    _parse_ok(launcher)


def test_weather_runner_supports_dry_run_flag_for_non_destructive_testing() -> None:
    """send_daily_weather_personnel_mail.py --dry-run destekler; launcher'i gercek
    mail gondermeden manuel test etmek icin bu bayrak kullanilabilir. Bu test
    sadece python CLI kontratini dogrular; gercek mail GONDERMEZ."""
    weather_runner = ROOT / "scripts" / "communication" / "send_daily_weather_personnel_mail.py"
    text = weather_runner.read_text(encoding="utf-8")
    assert "--dry-run" in text


def test_two_unproven_launchers_are_not_fabricated() -> None:
    """watch_bys360_live_waitress80.ps1 ve run_performance_mail_reminder_09.ps1 icin
    repoda hicbir installer/cagri zinciri/davranis sozlesmesi bulunmadigindan bu
    launcher'lar KASITLI olarak olusturulmamistir (bkz. deployment dokumantasyonu).
    Bu test, birinin varsayimla/isimden davranis uydurularak eklenmedigini kilitler."""
    assert not (ROOT / "scripts" / "windows" / "watch_bys360_live_waitress80.ps1").exists()
    assert not (ROOT / "scripts" / "windows" / "run_performance_mail_reminder_09.ps1").exists()
