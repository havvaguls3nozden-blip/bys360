# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Profile service extraction target for mobile routes."""
from __future__ import annotations

def _run_legacy_route(legacy_fn, *args, **kwargs):
    """Run an extracted legacy route implementation without changing endpoint behavior."""
    return legacy_fn(*args, **kwargs)

def delegate_mobile_profile(legacy_fn, *args, **kwargs):
    """Delegate wrapper for mobile_profile; keeps route endpoint and URL stable."""
    return _run_legacy_route(legacy_fn, *args, **kwargs)

def delegate_mobile_profile_update(legacy_fn, *args, **kwargs):
    """Delegate wrapper for mobile_profile_update; keeps route endpoint and URL stable."""
    return _run_legacy_route(legacy_fn, *args, **kwargs)

def delegate_mobile_profile_me(legacy_fn, *args, **kwargs):
    """Delegate wrapper for mobile_profile_me; keeps route endpoint and URL stable."""
    return _run_legacy_route(legacy_fn, *args, **kwargs)

