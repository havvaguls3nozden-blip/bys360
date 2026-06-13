from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_mobile_response_suite_gate_p3f import run_checks


def test_mobile_api_response_suite_p3f() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(
        root,
        compile_all=False,
        app_factory=False,
        secret_gate_run=False,
        pytest_gate=False,
        write_report=False,
    )
    assert result["p3_suite_ok"] is True
    assert result["p3_gates_passed"] == result["p3_gate_count"] == 5
    assert result["routes_py_lines"] <= 300
    assert result["total_mobile_route_decorator_count"] == 24
    assert result["feature_coverage"].get("performance") is True
    assert result["feature_coverage"].get("auth") is True
    assert result["feature_coverage"].get("support") is True
