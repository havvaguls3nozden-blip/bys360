from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase3_route_density_gate_v1 import run_checks


def test_phase3_route_density_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["route_density_gate_ok"] is True
    assert result["python_file_count"] > 0
    assert result["duplicate_path_count"] == 0
    assert result["total_lines"] > 0
    assert result["total_route_decorators"] > 0
    assert result["top_by_lines"]
    assert result["top_by_routes"]
