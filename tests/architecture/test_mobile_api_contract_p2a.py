from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_gate():
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "quality" / "bys360_mobile_pytest_contract_gate_p2a_v3.py"
    spec = importlib.util.spec_from_file_location("bys360_mobile_pytest_contract_gate_p2a_v3", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


def test_mobile_api_domain_contract_is_stable():
    gate, root = _load_gate()
    inventory = gate.build_inventory(root)
    checks = gate.build_contract_checks(inventory)
    assert checks["domain_dir_exists"]
    assert checks["expected_domain_files_exist"]
    assert checks["routes_py_under_300_lines"]
    assert checks["route_contract_count_expected"]
    assert checks["no_duplicate_route_decorators"]


def test_mobile_api_expected_domains_compile():
    gate, root = _load_gate()
    inventory = gate.build_inventory(root)
    compile_ok, compile_results = gate._compile([Path(item["abs_path"]) for item in inventory["domain_inventory"] if item["exists"]])
    assert compile_ok, compile_results
