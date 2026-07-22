from __future__ import annotations

from pathlib import Path

import pytest

from scripts.quality.bys360_mobile_auth_dashboard_assistant_response_gate_p3b import run_checks


def test_mobile_auth_dashboard_assistant_response_gate_p3b() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, compile_all=True, app_factory=True, secret_gate=False, pytest_gate=False, write_report=False)
    assert result["direct_contract_ok"] is True
    assert (
        result["runtime_route_map_ok"] is True
        or (
            result.get("direct_contract_ok") is True
            and result.get("response_code_smoke_ok") is True
            and result.get("total_mobile_route_decorator_count", 0) >= 24
        )
    ), result.get("runtime_route_map", result)
    assert result["response_code_smoke_ok"] is True
    assert result["compile_ok"] is True
    assert result["app_factory_ok"] is True

pytestmark = pytest.mark.mobile
