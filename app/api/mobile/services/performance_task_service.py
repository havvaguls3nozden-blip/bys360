# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Performance task/scoring service extraction target for mobile performance routes."""
from __future__ import annotations


# P3.2 V2.17.36 - route URL/endpoint degistirmeden helper delegasyonu
def delegate_v2835_score_form_payload(*args, **kwargs):
    # Import local tutulur; blueprint kayit sirasini etkilemez.
    from app.api.mobile import performance_routes as _routes
    legacy = getattr(_routes, "_bys360_legacy__v2835_score_form_payload", None)
    if legacy is None:
        raise RuntimeError("_bys360_legacy__v2835_score_form_payload bulunamadi; P3.2 delegasyon eksik veya geri alinmis olabilir.")
    return legacy(*args, **kwargs)

def _v2837_action_capabilities(*args, **kwargs):
    from app.api.mobile import performance_routes as _bys360_performance_routes
    return _bys360_performance_routes._bys360_legacy__v2837_action_capabilities(*args, **kwargs)


def _v2837_find_return_target(*args, **kwargs):
    from app.api.mobile import performance_routes as _bys360_performance_routes
    return _bys360_performance_routes._bys360_legacy__v2837_find_return_target(*args, **kwargs)

def _v2837_return_assignment(*args, **kwargs):
    from app.api.mobile import performance_routes as _bys360_performance_routes
    return _bys360_performance_routes._bys360_legacy__v2837_return_assignment(*args, **kwargs)


def _v2837_withdraw_assignment(*args, **kwargs):
    from app.api.mobile import performance_routes as _bys360_performance_routes
    return _bys360_performance_routes._bys360_legacy__v2837_withdraw_assignment(*args, **kwargs)

