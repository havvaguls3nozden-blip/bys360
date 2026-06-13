from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "app" / "refactor" / "final_quality_service_contract.py"


def load_contract_module():
    spec = importlib.util.spec_from_file_location("final_quality_service_contract", CONTRACT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_live_service_area_manifest_covers_current_live_backbone() -> None:
    module = load_contract_module()
    keys = {item.key for item in module.LIVE_SERVICE_AREAS}
    assert keys == {
        "identity_authorization_settings", "personnel_organization", "performance_management",
        "leave_delegation", "communication_survey_feedback", "ai_decision_support",
        "support_center", "home_weather_summary",
    }


def test_performance_chain_contract_keeps_final_manager_rules() -> None:
    module = load_contract_module()
    rules = {item.key: item for item in module.PERFORMANCE_CHAIN_CONTRACTS}
    assert rules["calisma_grubu_personeli"].first_manager == "grup_baskani"
    assert rules["calisma_grubu_personeli"].second_manager == "koordinator"
    assert rules["calisma_grubu_personeli"].process_order == ("third", "second", "first")
    assert rules["koordinator"].first_manager == "baskan_yardimcisi"
    assert rules["koordinator"].second_manager == "grup_baskani"
    assert rules["grup_baskani"].first_manager == "baskan"
    assert rules["grup_baskani"].second_manager == "baskan_yardimcisi"
    assert rules["grup_baskani"].process_order == ("second", "first")
    assert rules["hukuk_musavirine_bagli_personel"].process_order == ("first",)
    assert rules["baskan_tek_degerlendirici_ozel_roller"].second_manager is None


def test_weather_contract_is_safe_for_homepage() -> None:
    module = load_contract_module()
    weather = module.WEATHER_HOME_CONTRACT
    assert weather["provider"] == "open_meteo"
    assert weather["api_key_required"] is False
    assert weather["must_have_fallback"] is True
    assert weather["cache_minutes_default"] == 60
    assert "bilgilendirme amaçlıdır" in weather["decision_support_disclaimer"]


def test_contract_module_has_no_runtime_side_effects() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    for snippet in ["register_blueprint(", "db.session" + ".commit(", "." + "create_all(", "." + "drop_all(", "ALTER TABLE", "DROP TABLE", "url" + "open("]:
        assert snippet not in text
