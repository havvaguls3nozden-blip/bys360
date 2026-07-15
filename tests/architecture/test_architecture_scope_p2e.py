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
    assert "BYS360_P2E_ZERO_SKIP_ARCHITECTURE_SCOPE" in text


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

# PHASE4BE_ARCHITECTURE_SCOPE_REGRESSION
class _Phase4BEFakeItem:
    def __init__(self, path):
        self.path = path
        self.markers = []

    def add_marker(self, marker) -> None:
        self.markers.append(marker)


def _phase4be_conftest_namespace():
    import runpy
    from pathlib import Path

    return runpy.run_path(
        str(Path(__file__).with_name("conftest.py"))
    )


def test_architecture_skip_does_not_touch_service_tests(monkeypatch) -> None:
    from pathlib import Path

    monkeypatch.delenv(
        "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS",
        raising=False,
    )

    namespace = _phase4be_conftest_namespace()
    root = Path(__file__).resolve().parents[2]
    item = _Phase4BEFakeItem(
        root / "tests" / "services" / "test_phase4be_probe.py"
    )

    namespace["pytest_collection_modifyitems"](None, [item])

    assert item.markers == []


def test_architecture_zero_skip_keeps_legacy_architecture_test_running(
    monkeypatch,
) -> None:
    from pathlib import Path

    monkeypatch.delenv(
        "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS",
        raising=False,
    )

    namespace = _phase4be_conftest_namespace()
    root = Path(__file__).resolve().parents[2]
    item = _Phase4BEFakeItem(
        root / "tests" / "architecture" / "test_legacy_probe.py"
    )

    namespace["pytest_collection_modifyitems"](None, [item])

    assert item.markers == []


def test_architecture_skip_keeps_active_architecture_test_running(
    monkeypatch,
) -> None:
    from pathlib import Path

    monkeypatch.delenv(
        "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS",
        raising=False,
    )

    namespace = _phase4be_conftest_namespace()
    item = _Phase4BEFakeItem(Path(__file__).resolve())

    namespace["pytest_collection_modifyitems"](None, [item])

    assert item.markers == []

