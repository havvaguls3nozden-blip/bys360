from pathlib import Path


def test_anonymous_pulse_rows_do_not_feed_named_risk_list():
    source = Path("app/services/feedback_service.py").read_text(encoding="utf-8")
    assert "identified_rows" in source
    assert "is_anonymous" in source
    assert "for row in identified_rows:" in source
    assert "not bool(getattr(row, \"is_anonymous\", False))" in source
