from pathlib import Path

from scripts.quality.bys360_mobile_request_scenario_gate_p3a import run_checks


def test_mobile_api_request_scenario_gate_p3a() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(
        root,
        compile_all=True,
        app_factory=True,
        secret=False,
        pytest_run=False,
        write_report=False,
    )
    assert result["direct_contract_ok"] is True
    assert result["request_scenario_ok"] is True
    assert result["runtime_route_map_ok"] is True
    assert result["routes_py_lines"] <= 300
    assert result["total_mobile_route_decorator_count"] == 28
    assert result["inventory"]["expected_missing_routes"] == []
    assert result["inventory"]["wrong_domain_owner_routes"] == []
    assert result["runtime_route_map"]["missing_runtime_suffixes"] == []
