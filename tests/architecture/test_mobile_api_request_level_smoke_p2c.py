
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_gate_module():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "quality" / "bys360_mobile_request_level_smoke_gate_p2c_v2.py"
    spec = importlib.util.spec_from_file_location("bys360_mobile_request_level_smoke_gate_p2c_v2", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mobile_api_request_level_smoke_contract_gate():
    module = _load_gate_module()
    root = Path(__file__).resolve().parents[2]
    result = module.run_gate(root, mode="pytest", compile_all=False, run_app_factory=False, run_secret=False, run_pytest_flag=False, write_report=False)
    assert result["direct_contract_ok"] is True
    assert result["behavior_smoke_ok"] is True
    assert result["request_level_smoke_ok"] is True
    assert result["routes_py_lines"] <= 300
    assert result["total_mobile_route_decorator_count"] == 24
