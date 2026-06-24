from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase3c_compact_route_service_gate_v1 import run_checks


def test_phase3c_compact_route_service_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["compact_route_service_gate_ok"] is True
    assert result["route_decorator_count"] == 22
    assert result["route_import_ok"] is True
    assert result["globals_bridge_ok"] is True
    assert result["route_wrappers_small_ok"] is True
    assert result["service_logic_ok"] is True
    assert result["route_line_reduction_ok"] is True
    assert all(result["service_presence"].values())
