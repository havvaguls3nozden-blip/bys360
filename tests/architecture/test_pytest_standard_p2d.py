from __future__ import annotations

from pathlib import Path


def test_pytest_standard_files_exist():
    root = Path(__file__).resolve().parents[2]
    assert (root / "requirements-dev.txt").exists()
    assert (root / "scripts" / "quality" / "bys360_pytest_standard_gate_p2d.py").exists()


def test_mobile_architecture_tests_exist():
    root = Path(__file__).resolve().parents[2]
    expected = [
        "tests/architecture/test_mobile_api_contract_p2a.py",
        "tests/architecture/test_mobile_api_behavior_smoke_p2b.py",
        "tests/architecture/test_mobile_api_request_level_smoke_p2c_v3.py",
    ]
    missing = [item for item in expected if not (root / item).exists()]
    assert missing == []
