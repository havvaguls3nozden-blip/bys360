from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "app" / "refactor" / "final_quality_performance_rules.py"


def load_rules_module():
    spec = importlib.util.spec_from_file_location("final_quality_performance_rules_visibility", CONTRACT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_visibility_rules_lock_no_blind_and_publish_before_employee_visibility() -> None:
    module = load_rules_module()
    rules = {item.key: item for item in module.PERFORMANCE_VISIBILITY_RULES}
    assert rules["no_blind_evaluation"].enabled is True
    assert "önceki puanı" in rules["no_blind_evaluation"].note
    assert rules["publish_required_before_employee_visibility"].enabled is True
    assert "yayınlamadan" in rules["publish_required_before_employee_visibility"].note
    assert rules["manager_visibility_separate_from_employee_visibility"].enabled is True


def test_score_explanation_rules_are_fixed() -> None:
    module = load_rules_module()
    rules = {item.key: item for item in module.SCORE_EXPLANATION_RULES}
    assert rules["score_1_comment_required"].threshold_or_score == 1
    assert rules["score_1_comment_required"].required is True
    assert rules["score_5_comment_required"].threshold_or_score == 5
    assert rules["score_5_comment_required"].required is True
    assert rules["final_below_70_general_comment_required"].threshold_or_score == 70
    assert rules["final_above_90_general_comment_required"].threshold_or_score == 90


def test_scoring_contract_keeps_terms_and_thresholds() -> None:
    module = load_rules_module()
    scoring = module.PERFORMANCE_SCORING_CONTRACT
    assert scoring["criteria_score_min"] == 1
    assert scoring["criteria_score_max"] == 5
    assert scoring["converted_scale_max"] == 100
    assert scoring["failure_threshold_below"] == 70
    assert scoring["high_success_threshold_above"] == 90
    assert scoring["primary_term"] == "Değerlendirme Kriterleri"
    assert scoring["forbidden_primary_term"] == "Yetkinlik"
