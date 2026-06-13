from app.services.performance.phase1_rule_center import (
    display_status,
    evaluate_phase1_rules,
    is_general_comment_required,
    is_publish_locked,
    is_score_comment_required,
    requires_president_approval,
    reviewer_action_decision,
)


def test_phase1_score_comment_rules():
    assert is_score_comment_required(1) is True
    assert is_score_comment_required(5) is True
    assert is_score_comment_required(3) is False


def test_phase1_threshold_rules():
    assert is_general_comment_required(69.9) is True
    assert is_general_comment_required(90.1) is True
    assert requires_president_approval(69.9) is True
    assert is_publish_locked(69.9, president_approved=False) is True
    assert is_publish_locked(69.9, president_approved=True) is False


def test_phase1_status_labels_are_institutional_turkish():
    assert display_status("draft") != "draft"
    assert display_status("president_pending") == "Başkan Onayı Bekliyor"
    assert display_status("blocked_president_pending") == "Başkan Onayı Yayın Kilidi"


def test_phase1_third_reviewer_comment_mode():
    decision = reviewer_action_decision(3, "comment_only")
    assert decision["action_type"] == "comment"
    assert decision["affects_score"] is False


def test_phase1_combined_decision():
    decision = evaluate_phase1_rules({
        "criteria_score": 1,
        "final_score": 66,
        "status_code": "president_pending",
        "president_approved": False,
        "reviewer_level": 3,
        "third_reviewer_mode": "comment_only",
    })
    assert decision.requires_score_comment is True
    assert decision.requires_general_comment is True
    assert decision.requires_president_approval is True
    assert decision.publish_locked is True
    assert decision.display_status == "Başkan Onayı Bekliyor"
    assert decision.reviewer_action_type == "comment"
