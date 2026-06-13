from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_factory_setup_is_outside_app_init() -> None:
    init_source = read("app/__init__.py")
    factory_source = read("app/bootstrap/factory_bootstrap.py")
    assert "db.init_app(app)" not in init_source
    assert "csrf.init_app(app)" not in init_source
    assert "db.init_app(app)" in factory_source
    assert "csrf.init_app(app)" in factory_source


def test_application_pipeline_calls_factory_helpers() -> None:
    source = read("app/bootstrap/application_bootstrap.py")
    for fragment in [
        "create_configured_flask_app(import_name)",
        "run_preflight_checks(app)",
        "initialize_core_extensions(app)",
        "configure_login_manager_defaults()",
    ]:
        assert fragment in source
