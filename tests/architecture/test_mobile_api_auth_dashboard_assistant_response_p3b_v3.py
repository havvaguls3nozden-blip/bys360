from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_mobile_auth_dashboard_assistant_response_gate_p3b_v3 import run_checks


def test_mobile_auth_dashboard_assistant_response_gate_p3b_v3() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(
        root,
        compile_all=False,
        app_factory=True,
        secret_gate_enabled=False,
        pytest_gate_enabled=False,
        write_report=False,
    )
    assert result["direct_contract_ok"] is True
    assert result["runtime_route_map_ok"] is True
    assert result["response_code_smoke_ok"] is True
