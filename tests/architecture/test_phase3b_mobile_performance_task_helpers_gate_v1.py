from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase3b_mobile_performance_task_helpers_gate_v1 import run_checks


def test_phase3b_mobile_performance_task_helpers_gate_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["task_helpers_gate_ok"] is True
    assert result["route_decorator_count"] == 22
    assert result["route_import_ok"] is True
    assert result["service_imports_ok"] is True
    assert result["route_line_reduction_ok"] is True
    assert all(result["helper_presence"].values())
    assert all(result["helper_removed_from_route"].values())
