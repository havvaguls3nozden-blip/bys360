from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_publish_preflight_rules_hold_constitution():
    text = _read("app/services/performance/publish_preflight_rules.py")
    assert "LOW_SCORE_THRESHOLD = 70.0" in text
    assert "HIGH_SCORE_THRESHOLD = 90.0" in text
    assert "extreme_score_explanation_required" in text
    assert "low_score_general_comment_required" in text
    assert "high_score_general_comment_required" in text
    assert "level_3_comment_required" in text
    assert "expected_publish_levels" in text
    assert "validate_evaluation_for_publish" in text


def test_visibility_guard_uses_strict_publish_preflight():
    text = _read("app/services/performance/visibility_guard.py")
    assert "is_evaluation_publishable_strict" in text
    assert "validate_evaluation_for_publish" in text
    assert "publish_preflight" in text
    assert "scorecard-visibility-lock-v2" in text


def test_publish_guard_shows_strict_blockers():
    text = _read("app/services/performance/publish_guard.py")
    assert "_strict_period_findings" in text
    assert "Yayın ön kontrol blokajı" in text
    assert "validate_evaluation_for_publish" in text
    assert "2026-04-18-publish-preflight-lock-v1" in text
