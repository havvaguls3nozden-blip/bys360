from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_file_center_storage_root_is_not_windows_hardcoded():
    services = read("app/file_center/services.py")
    maintenance = read("app/file_center/maintenance_service.py")
    assert "C:/bys360/local_storage/file_center" not in services
    assert "C:\\bys360\\local_storage\\file_center" not in maintenance
    assert "FILE_CENTER_STORAGE_ROOT canlı ortamda zorunludur" in services


def test_guest_routes_do_not_leak_raw_exception_messages():
    routes = read("app/file_center/routes.py")
    assert 'error=f"Dosya indirilemedi: {exc}"' not in routes
    assert 'flash(str(exc), "danger")' in routes  # only ValueError/user-facing validation branch remains
    assert "guest_file_download_failed" in routes
    assert "guest_file_upload_failed" in routes


def test_file_center_rate_limits_are_registered():
    app_init = read("app/__init__.py")
    rate = read("app/security/api_rate_limit.py")
    assert "API and File Center rate limit" in app_init
    assert "main.file_center_guest_download" in rate
    assert "FILE_CENTER_GUEST_UPLOAD_RATE_LIMIT" in rate
    assert "_apply_file_center_limits" in rate


def test_file_center_maintenance_tick_exists():
    maintenance = read("app/file_center/maintenance_service.py")
    tick = read("scripts/local/file_center_ops_tick_v1l.py")
    assert "run_file_center_maintenance_tick" in maintenance
    assert "storage_health_summary" in maintenance
    assert "scan_pending_files" in maintenance
    assert "file_center_ops_tick_v1l" in str(ROOT / "scripts/local/file_center_ops_tick_v1l.py")
    assert "run_file_center_maintenance_tick" in tick


def test_clamav_optional_integration_is_explicit():
    services = read("app/file_center/services.py")
    security_tpl = read("app/templates/file_center/security.html")
    assert "FILE_CENTER_CLAMAV_ENABLED" in services
    assert "_run_clamav_scan" in services
    assert "Gerçek antivirüs taraması etkin değil" in security_tpl
    assert "Temel dosya türü ve güvenlik ön kontrolü geçti" in services


def test_secret_hygiene_tooling_exists():
    audit = read("scripts/local/audit_file_center_secret_hygiene_v1l.py")
    ps = read("scripts/windows/repair_file_center_secret_hygiene_v1l.ps1")
    assert "secret_like_files" in audit
    assert "backups" in ps
    assert "MoveRootEnv" in ps
