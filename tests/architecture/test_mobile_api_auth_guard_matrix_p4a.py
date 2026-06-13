from pathlib import Path

from scripts.quality.bys360_mobile_auth_guard_matrix_gate_p4a import run_checks


def test_mobile_api_auth_guard_matrix_p4a() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(
        root,
        compile_all=True,
        app_factory=True,
        secret_gate_enabled=False,
        pytest_gate_enabled=False,
        write_report=False,
    )
    assert result["direct_contract_ok"] is True
    assert result["runtime_route_map_ok"] is True
    assert result["auth_guard_matrix_ok"] is True
    assert result["compile_ok"] is True
    assert result["app_factory_ok"] is True
