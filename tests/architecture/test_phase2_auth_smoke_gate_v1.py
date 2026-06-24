from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase2_auth_smoke_gate_v1 import run_checks


def test_phase2_mobile_auth_smoke_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["auth_smoke_ok"] is True

    responses = {item["name"]: item for item in result["responses"]}

    assert responses["mobile_login_empty_payload"]["status_code"] not in {404, 405, 500}
    assert responses["mobile_refresh_empty_payload"]["status_code"] not in {404, 405, 500}
    assert responses["mobile_me_without_token"]["status_code"] not in {404, 405, 500}
