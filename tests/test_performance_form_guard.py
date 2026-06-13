from app.services.performance.form_guard import build_form_actions, build_form_guard_state


def test_build_form_guard_state_does_not_add_level2_comment_rule_when_score_three_policy_is_locked_off():
    payload = build_form_guard_state(
        manager_level=2,
        requires_level_2_comment=True,
        level_3_scoring_enabled=False,
        evaluation_window={"can_submit": True},
        workflow_status_label="Taslak",
        saved=False,
    )
    assert all(rule["title"] != "3 puan açıklaması" for rule in payload["rule_cards"])
    assert payload["can_submit"] is True


def test_build_form_actions_for_level_1_contains_complete_and_return():
    actions = build_form_actions(
        manager_level=1,
        can_withdraw_level_1=False,
        can_return_to_level_1=True,
        level_3_scoring_enabled=False,
        evaluation_window={"can_submit": True},
    )
    values = {action.get("value") for action in actions if action.get("type") == "submit"}
    assert "complete_level_2" in values
    assert "return_to_level_1" in values
