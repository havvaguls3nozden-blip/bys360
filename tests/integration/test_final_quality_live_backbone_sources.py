from __future__ import annotations
import pytest

import importlib.util
import sys
from pathlib import Path


# BYS360_SPRINT2_LEGACY_INTEGRATION_SCOPE_V8
pytestmark = [pytest.mark.legacy_integration, pytest.mark.realdb]
ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "app"
CONTRACT_PATH = ROOT / "app" / "refactor" / "final_quality_live_backbone_contract.py"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("final_quality_live_backbone_contract", CONTRACT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _read_app_sources() -> str:
    chunks: list[str] = []
    assert APP_DIR.exists(), "app klasörü bulunamadı"
    for path in APP_DIR.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "__pycache__" in rel or ".venv" in rel:
            continue
        chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def test_each_live_backbone_area_has_source_evidence() -> None:
    module = load_contract_module()
    source = _read_app_sources()
    missing: list[str] = []
    for area in module.LIVE_BACKBONE_AREAS:
        if not any(token in source for token in area.source_tokens):
            missing.append(area.key)
    assert not missing, f"Canlı omurga kaynak kanıtı eksik: {missing}"


def test_live_backbone_evidence_paths_are_present_or_have_source_tokens() -> None:
    module = load_contract_module()
    source = _read_app_sources()
    missing: list[str] = []
    for area in module.LIVE_BACKBONE_AREAS:
        path_exists = any((ROOT / rel).exists() for rel in area.evidence_paths)
        token_exists = any(token in source for token in area.source_tokens)
        if not path_exists and not token_exists:
            missing.append(area.key)
    assert not missing, f"Canlı omurga path/token kanıtı eksik: {missing}"


def test_integration_flow_tokens_exist_without_forcing_database_runtime() -> None:
    module = load_contract_module()
    source = _read_app_sources()
    weak_flows: list[str] = []
    for flow in module.CRITICAL_INTEGRATION_FLOWS:
        matched = sum(1 for token in flow.required_tokens if token in source)
        if matched < 1:
            weak_flows.append(flow.key)
    assert not weak_flows, f"Entegrasyon akışı kaynak token kanıtı zayıf: {weak_flows}"


def test_final_quality_integration_tests_do_not_mutate_database_or_call_external_network() -> None:
    test_dir = ROOT / "tests" / "integration"
    files = sorted(test_dir.glob("test_final_quality_*.py"))
    assert len(files) >= 3
    joined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
    forbidden = [
        "db.session" + ".commit(",
        ".create" + "_all(",
        ".drop" + "_all(",
        "requests" + ".get(",
        "url" + "open(",
        "ALTER " + "TABLE",
        "DROP " + "TABLE",
    ]
    for snippet in forbidden:
        assert snippet not in joined
