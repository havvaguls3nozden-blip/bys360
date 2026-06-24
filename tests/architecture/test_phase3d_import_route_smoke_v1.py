from __future__ import annotations

from pathlib import Path

from scripts.quality.bys360_phase3d_import_route_smoke_v1 import run_checks


def test_phase3d_import_route_smoke_v1() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_checks(root, write_report=False)

    assert result["phase3d_import_route_smoke_ok"] is True
    assert result["compile_ok"] is True
    assert result["route_decorator_count"] == 22
    assert result["service_import"]["ok"] is True
    assert result["app_factory_route_smoke"]["ok"] is True
