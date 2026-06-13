from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_faz1_operational_helpers_are_outside_app_init() -> None:
    source = read("app/__init__.py")
    assert "configure_operational_logging" not in source
    assert "register_operational_guards" not in source
    assert "register_response_hardening" not in source
    for rel in [
        "app/bootstrap/operational_logging.py",
        "app/bootstrap/operational_guards.py",
        "app/bootstrap/response_hardening.py",
        "app/bootstrap/schema_validation.py",
    ]:
        assert (ROOT / rel).exists()


def test_faz1_schema_guard_contract_survives_faz5_pipeline() -> None:
    source = read("app/bootstrap/application_bootstrap.py")
    assert "run_schema_guard_bootstrap" in source
    assert "validate_required_schema(target_app, get_expected_schema())" in source
