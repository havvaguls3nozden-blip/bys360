from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_mobile_personnel_kpi_communication_response_gate_p3c_v2 import (
    run_checks,
)


def test_mobile_personnel_kpi_communication_response_gate_p3c_v2() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(
        root,
        compile_all=False,
        app_factory=False,
        secret_gate=False,
        pytest_gate=False,
        write_report=False,
    )
    assert result["direct_contract_ok"] is True
    assert result["runtime_route_map_ok"] is True
    assert result["response_code_smoke_ok"] is True
    assert result["routes_py_lines"] <= 300
    assert result["total_mobile_route_decorator_count"] == 28
