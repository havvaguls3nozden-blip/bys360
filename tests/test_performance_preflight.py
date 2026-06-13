from app.services.performance.preflight import preflight_has_blockers
from app.services.performance_v2.validators import validate_score_comment_rules


def test_preflight_has_blockers_true_when_blocker_rows_exist():
    assert preflight_has_blockers({"blockers": [{"title": "x"}]}) is True


def test_preflight_has_blockers_false_for_empty_payload():
    assert preflight_has_blockers({"blockers": []}) is False
    assert preflight_has_blockers(None) is False


def test_validate_score_comment_rules_requires_comment_for_edge_scores():
    issues = validate_score_comment_rules(raw_score=5, score_100=95, general_comment="")
    # BYS360_A5_P2D1: 1 ve 5 puanda sabit a??klama zorunlulu?u kald?r?ld?.
    assert not any("1 ve 5" in issue and "zorunlu" in issue for issue in issues)
    assert "70 altı ve 90 üstü sonuçlarda genel görüş zorunlu." in issues
