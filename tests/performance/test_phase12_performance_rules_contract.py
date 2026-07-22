from app.performance.rules.performance_manager_rules_contract import (
    FORBIDDEN_PRIMARY_TERM,
    HIGH_SCORE_THRESHOLD,
    LOW_SCORE_THRESHOLD,
    NO_BLIND_EVALUATION,
    PERSON_RESULT_VISIBLE_ONLY_AFTER_PUBLISH,
    PRIMARY_TERM,
    build_process_order,
    get_manager_rule,
    is_single_manager_flow,
    requires_detailed_general_opinion,
    requires_score_explanation,
    third_manager_policy,
    validate_weight_total,
)


def test_core_visibility_and_terms_are_locked():
    assert NO_BLIND_EVALUATION is True
    assert PERSON_RESULT_VISIBLE_ONLY_AFTER_PUBLISH is True
    assert PRIMARY_TERM == "Değerlendirme Kriterleri"
    assert FORBIDDEN_PRIMARY_TERM == "Yetkinlik"
    assert LOW_SCORE_THRESHOLD == 70
    assert HIGH_SCORE_THRESHOLD == 90


def test_role_based_manager_rules_are_locked():
    wg = get_manager_rule("working_group_personnel")
    assert wg.first_manager == "Grup Başkanı"
    assert wg.second_manager == "Koordinatör"
    assert wg.process_order == ("3", "2", "1")

    coordinator = get_manager_rule("coordinator")
    assert coordinator.first_manager == "Başkan Yardımcısı"
    assert coordinator.second_manager == "Grup Başkanı"
    assert coordinator.process_order == ("3", "2", "1")

    group_head = get_manager_rule("group_head")
    assert group_head.first_manager == "Başkan"
    assert group_head.second_manager == "Başkan Yardımcısı"
    assert group_head.process_order == ("2", "1")


def test_special_exceptions_are_locked():
    legal = get_manager_rule("legal_single_manager")
    assert legal.first_manager == "Bağlı olduğu hukuk müşaviri"
    assert legal.second_manager is None
    assert legal.third_manager is None
    assert legal.process_order == ("1",)
    assert is_single_manager_flow("legal_single_manager") is True

    president_only = get_manager_rule("president_only_roles")
    assert president_only.first_manager == "Başkan"
    assert president_only.second_manager is None
    assert president_only.process_order == ("1",)
    assert is_single_manager_flow("president_only_roles") is True


def test_third_manager_modes_are_locked():
    comment = third_manager_policy("comment")
    assert comment["score_effect"] == 0
    assert comment["status_text"] == "yorum/görüş bekliyor"
    assert comment["score_input_enabled"] is False
    assert comment["included_in_weight"] is False

    score = third_manager_policy("score")
    assert score["score_effect"] == "dynamic"
    assert score["score_input_enabled"] is True
    assert score["included_in_weight"] is True


def test_explanation_and_threshold_rules_are_locked():
    assert requires_score_explanation(1) is True
    assert requires_score_explanation(5) is True
    assert requires_score_explanation(3) is False
    assert requires_detailed_general_opinion(69.99) is True
    assert requires_detailed_general_opinion(90.01) is True
    assert requires_detailed_general_opinion(70) is False
    assert requires_detailed_general_opinion(90) is False


def test_order_and_weight_helpers_are_locked():
    assert build_process_order("working_group_personnel", has_third_manager=True) == ("3", "2", "1")
    assert build_process_order("working_group_personnel", has_third_manager=False) == ("2", "1")
    assert validate_weight_total({"1": 60, "2": 40}) is True
    assert validate_weight_total({"1": 50, "2": 30, "3": 20}) is True
    assert validate_weight_total({"1": 60, "2": 30}) is False
