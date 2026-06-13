from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "tests" / "architecture"


def test_architecture_scope_conftest_exists_and_documents_active_gate() -> None:
    conftest = ARCH / "conftest.py"
    assert conftest.exists()
    text = conftest.read_text(encoding="utf-8")
    assert "BYS360_P2E_ACTIVE_ARCHITECTURE_SCOPE" in text
    assert "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS" in text
    assert "ACTIVE_ARCHITECTURE_TEST_FILES" in text


def test_architecture_scope_keeps_current_mobile_gates_active() -> None:
    text = (ARCH / "conftest.py").read_text(encoding="utf-8")
    for file_name in [
        "test_pytest_standard_p2d.py",
        "test_mobile_api_contract_p2a.py",
        "test_mobile_api_behavior_smoke_p2b.py",
        "test_mobile_api_request_level_smoke_p2c_v3.py",
    ]:
        assert file_name in text
        assert (ARCH / file_name).exists(), f"aktif mimari test dosyası eksik: {file_name}"
