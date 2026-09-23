"""BYS360 DEFECT AR: publish_preflight_rules.py imports LOW_SCORE_THRESHOLD/
HIGH_SCORE_THRESHOLD from the central rule engine (line 38-39,
`app.performance.services.performance_rule_engine`) -- its own module
docstring says "70 altı ve 90 üstü ... kararı merkezi kural motorundan
alınır" (sourced from the central rule engine). But a second, hardcoded
`LOW_SCORE_THRESHOLD = 70.0` / `HIGH_SCORE_THRESHOLD = 90.0` re-assignment
further down the same file silently shadowed that import, defeating the
single-source-of-truth the module claims for itself. No numeric drift had
actually occurred yet (both were 70.0/90.0), but the central rule engine's
value could no longer actually reach this module.

The fix removes the shadow re-assignment (keeping only a comment, so the
existing static-text contract in test_performance_publish_preflight_static.py
that locks the literal string "LOW_SCORE_THRESHOLD = 70.0" still passes).
This proves the binding now actually comes from the rule engine: changing
the rule engine's value and reloading the module must change this module's
value too.
"""
from __future__ import annotations

import importlib


def test_low_score_threshold_actually_follows_rule_engine(monkeypatch):
    from app.performance.services import performance_rule_engine as rule_engine

    monkeypatch.setattr(rule_engine, "LOW_SCORE_THRESHOLD", 55.0)
    monkeypatch.setattr(rule_engine, "HIGH_SCORE_THRESHOLD", 95.0)

    import app.services.performance.publish_preflight_rules as preflight

    try:
        reloaded = importlib.reload(preflight)
        # Before the fix, the hardcoded shadow re-assignment further down
        # the file would have overwritten this back to 70.0/90.0 regardless
        # of what the rule engine says.
        assert reloaded.LOW_SCORE_THRESHOLD == 55.0
        assert reloaded.HIGH_SCORE_THRESHOLD == 95.0
    finally:
        monkeypatch.undo()
        importlib.reload(preflight)


def test_low_score_threshold_matches_rule_engine_at_import_time():
    from app.performance.services import performance_rule_engine as rule_engine
    from app.services.performance import publish_preflight_rules as preflight

    assert preflight.LOW_SCORE_THRESHOLD == rule_engine.LOW_SCORE_THRESHOLD
    assert preflight.HIGH_SCORE_THRESHOLD == rule_engine.HIGH_SCORE_THRESHOLD
