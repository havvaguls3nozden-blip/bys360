from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_schema_contract_is_outside_app_init() -> None:
    init_source = read("app/__init__.py")
    schema_source = read("app/bootstrap/schema_contract.py")
    assert "EXPECTED_SCHEMA =" not in init_source
    assert "EXPECTED_SCHEMA =" in schema_source
    assert "def get_expected_schema" in schema_source


def test_application_pipeline_uses_schema_contract() -> None:
    source = read("app/bootstrap/application_bootstrap.py")
    assert "get_expected_schema" in source
    assert "validate_required_schema(target_app, get_expected_schema())" in source
