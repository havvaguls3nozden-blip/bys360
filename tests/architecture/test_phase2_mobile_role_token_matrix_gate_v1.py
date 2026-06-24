from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase2_mobile_role_token_matrix_gate_v1 import run_checks


def test_phase2_mobile_role_token_matrix_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["role_token_matrix_ok"] is True
    assert result["login_ok"] is True
    assert result["role_identity_ok"] is True
    assert result["matrix_route_ok"] is True
    assert result["failures"] == []
