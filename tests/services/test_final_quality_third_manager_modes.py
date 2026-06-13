from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "app" / "refactor" / "final_quality_performance_rules.py"


def load_rules_module():
    spec = importlib.util.spec_from_file_location("final_quality_performance_rules_third_manager", CONTRACT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_third_manager_comment_mode_is_not_score_waiting() -> None:
    module = load_rules_module()
    mode = module.get_third_manager_mode("comment_only")
    assert mode.score_enabled is False
    assert mode.score_impact_percent == 0
    assert mode.included_in_final_score is False
    assert mode.status_label == "yorum/görüş bekliyor"


def test_third_manager_score_mode_can_contribute_to_final_score() -> None:
    module = load_rules_module()
    mode = module.get_third_manager_mode("score_contributor")
    assert mode.score_enabled is True
    assert mode.included_in_final_score is True
    assert mode.status_label == "puan bekliyor"
    assert module.PERFORMANCE_SCORING_CONTRACT["weight_total_percent"] == 100


def test_weight_total_contract_is_strictly_100_percent() -> None:
    module = load_rules_module()
    assert module.validate_weight_profile((100, 0, 0)) is True
    assert module.validate_weight_profile((50, 50, 0)) is True
    assert module.validate_weight_profile((40, 40, 20)) is True
    assert module.validate_weight_profile((40, 40, 10)) is False
