from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase2_auth_success_flow_gate_v1 import run_checks


def test_phase2_mobile_auth_success_flow_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["auth_success_flow_ok"] is True

    steps = {step["name"]: step for step in result["steps"]}
    assert steps["login_with_sicil"]["status_code"] == 200
    assert steps["login_with_sicil"]["has_access_token"] is True
    assert steps["login_with_sicil"]["has_refresh_token"] is True
    assert steps["me_with_access_token"]["status_code"] == 200
    assert steps["refresh_with_refresh_token"]["status_code"] == 200
    assert steps["refresh_with_refresh_token"]["has_access_token"] is True
