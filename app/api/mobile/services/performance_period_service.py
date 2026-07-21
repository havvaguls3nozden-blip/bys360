# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Performance period service extraction target for mobile performance routes."""
from __future__ import annotations


def _v2853_note_type_label(*args, **kwargs):
    from app.api.mobile import performance_routes as _bys360_performance_routes
    return _bys360_performance_routes._bys360_legacy__v2853_note_type_label(*args, **kwargs)


def _v2853_note_bool(*args, **kwargs):
    from app.api.mobile import performance_routes as _bys360_performance_routes
    return _bys360_performance_routes._bys360_legacy__v2853_note_bool(*args, **kwargs)


def delegate_mobile_performance_in_period_notes(*args, **kwargs):
    from app.api.mobile.performance_routes import _bys360_legacy_mobile_performance_in_period_notes
    return _bys360_legacy_mobile_performance_in_period_notes(*args, **kwargs)


def delegate_mobile_performance_in_period_notes_v2853(*args, **kwargs):
    from app.api.mobile.performance_routes import (
        _bys360_legacy_mobile_performance_in_period_notes_v2853,
    )
    return _bys360_legacy_mobile_performance_in_period_notes_v2853(*args, **kwargs)


def delegate_mobile_performance_note_scorecard_v2863a(*args, **kwargs):
    from app.api.mobile.performance_routes import (
        _bys360_legacy_mobile_performance_note_scorecard_v2863a,
    )
    return _bys360_legacy_mobile_performance_note_scorecard_v2863a(*args, **kwargs)

def mobile_performance_period_detail(*args, **kwargs):
    """Delegated wrapper for mobile_performance_period_detail."""
    from app.api.mobile import performance_routes as _routes
    return _routes._bys360_legacy_mobile_performance_period_detail(*args, **kwargs)


def _period_scope(*args, **kwargs):
    """Delegated wrapper for _period_scope."""
    from app.api.mobile import performance_routes as _routes
    return _routes._bys360_legacy__period_scope(*args, **kwargs)


def _period_progress(*args, **kwargs):
    """Delegated wrapper for _period_progress."""
    from app.api.mobile import performance_routes as _routes
    return _routes._bys360_legacy__period_progress(*args, **kwargs)
