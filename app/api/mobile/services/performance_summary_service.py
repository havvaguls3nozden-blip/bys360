# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Performance summary service extraction target for mobile performance routes."""
from __future__ import annotations


# P2.1 V2.17.25 - safe read-only delegation shim
def delegate_mobile_performance_summary(user, legacy_func):
    """Delegate mobile performance summary without changing route contract."""
    return legacy_func(user)




def delegate_mobile_performance_full_feature_summary(legacy_func, *args, **kwargs):
    """mobile_performance_full_feature_summary icin guvenli servis delegasyonu."""
    return legacy_func(*args, **kwargs)


def _delegate_to_legacy(name, legacy_func, *args, **kwargs):
    if legacy_func is None:
        raise RuntimeError(f'Mobil performans servis delegasyonu legacy fonksiyonu bulunamadi: {name}')
    return legacy_func(*args, **kwargs)


def mobile_performance_reports(*args, legacy_func=None, **kwargs):
    return _delegate_to_legacy('mobile_performance_reports', legacy_func, *args, **kwargs)


def mobile_performance_risk_analysis_v2852(*args, legacy_func=None, **kwargs):
    return _delegate_to_legacy('mobile_performance_risk_analysis_v2852', legacy_func, *args, **kwargs)


def mobile_performance_history_archive(*args, legacy_func=None, **kwargs):
    return _delegate_to_legacy('mobile_performance_history_archive', legacy_func, *args, **kwargs)


def delegate_mobile_performance_reports(legacy_func, *args, **kwargs):
    """Delegate performance reports endpoint while preserving legacy behavior."""
    return legacy_func(*args, **kwargs)



def mobile_performance_risk_analysis_v2852_delegate(legacy_func, user):
    """Servis delegasyonu: mobil performans risk analizi.

    URL, endpoint ve blueprint adi korunur; is mantigi legacy fonksiyon
    uzerinden aynen calistirilir. Legacy govde stabil olduktan sonra
    bu servis icine tasinabilir.
    """
    return legacy_func(user)


def mobile_performance_development_suggestions_delegate(user):
    """Delegate wrapper for mobile_performance_development_suggestions; keeps route URL and endpoint stable."""
    from app.api.mobile import performance_routes as _legacy_routes
    return _legacy_routes._bys360_legacy_mobile_performance_development_suggestions(user)

