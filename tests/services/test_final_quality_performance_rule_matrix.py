from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "app" / "refactor" / "final_quality_performance_rules.py"


def load_rules_module():
    spec = importlib.util.spec_from_file_location("final_quality_performance_rules", CONTRACT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_performance_role_matrix_keeps_final_manager_order() -> None:
    module = load_rules_module()
    get = module.get_role_rule

    calisma = get("calisma_grubu_personeli")
    assert calisma.first_manager == "grup_baskani"
    assert calisma.second_manager == "koordinator"
    assert calisma.third_manager == "koordinatore_bagli_birim_amiri_opsiyonel"
    assert calisma.process_order == ("third", "second", "first")

    koordinator = get("koordinator")
    assert koordinator.first_manager == "baskan_yardimcisi"
    assert koordinator.second_manager == "grup_baskani"
    assert koordinator.process_order == ("third", "second", "first")

    grup_baskani = get("grup_baskani")
    assert grup_baskani.first_manager == "baskan"
    assert grup_baskani.second_manager == "baskan_yardimcisi"
    assert grup_baskani.process_order == ("second", "first")


def test_special_single_manager_rules_do_not_create_fake_waiting() -> None:
    module = load_rules_module()
    for key in module.SPECIAL_SINGLE_MANAGER_ROLE_KEYS:
        rule = module.get_role_rule(key)
        assert rule.single_manager is True
        assert rule.second_manager is None
        assert rule.third_manager is None
        assert rule.process_order == ("first",)
        assert rule.fake_waiting_forbidden is True
        assert rule.weight_profile == (100, 0, 0)
        assert module.validate_weight_profile(rule.weight_profile)


def test_president_only_special_roles_are_locked() -> None:
    module = load_rules_module()
    rule = module.get_role_rule("baskan_tek_degerlendirici_ozel_roller")
    assert rule.first_manager == "baskan"
    assert rule.second_manager is None
    assert rule.third_manager is None
    assert module.SPECIAL_PRESIDENT_ONLY_ROLES == ("baskan_danismani", "ozel_kalem", "ic_denetci")


def test_rule_module_has_no_runtime_side_effects() -> None:
    text = CONTRACT_PATH.read_text(encoding="utf-8")
    forbidden = ["register_blueprint(", "db.session" + ".commit(", "." + "create_all(", "." + "drop_all(", "ALTER TABLE", "DROP TABLE"]
    for snippet in forbidden:
        assert snippet not in text
