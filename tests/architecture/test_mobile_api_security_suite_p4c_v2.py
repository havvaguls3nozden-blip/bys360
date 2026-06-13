from __future__ import annotations

import pytest

# -*- coding: utf-8 -*-

import importlib.util
from pathlib import Path


def _load_gate(root: Path):
    script = root / "scripts" / "quality" / "bys360_mobile_security_suite_gate_p4c_v2.py"
    spec = importlib.util.spec_from_file_location("bys360_mobile_security_suite_gate_p4c_v2", script)
    assert spec and spec.loader, f"cannot load {script}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mobile_security_suite_gate_p4c_v2():
    root = Path(__file__).resolve().parents[2]
    module = _load_gate(root)

    class Args:
        compile_all = False
        app_factory = False
        secret_gate = False
        pytest_gate = False

    report = module.build_report(root, Args())
    assert report["ok"], report
    assert report["p4_security_suite_ok"] is True
    assert report["security_gate_count"] == 2
    assert report["security_gates_passed"] == 2
    assert report["auth_guard_matrix_ok"] is True
    assert report["role_boundary_matrix_ok"] is True
    assert report["total_probe_count"] >= 90
    assert report["direct_contract_ok"] is True




pytestmark = pytest.mark.mobile
