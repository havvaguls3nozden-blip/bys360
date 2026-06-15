# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Personnel service extraction target for mobile routes."""
from __future__ import annotations


def _routes_module():
    from app.api.mobile import routes as _mobile_routes
    return _mobile_routes


def _personnel_domain_module():
    from app.api.mobile.domains import personnel_write_all as _domain
    return _domain


def mobile_personnel_all(*args, **kwargs):
    return getattr(_routes_module(), "_bys360_legacy_mobile_personnel_all")(*args, **kwargs)


def mobile_personnel_create(*args, **kwargs):
    return getattr(_personnel_domain_module(), "_bys360_legacy_mobile_personnel_create")(*args, **kwargs)


def _mobile_created_personnel_row(*args, **kwargs):
    return getattr(_personnel_domain_module(), "_bys360_legacy__mobile_created_personnel_row")(*args, **kwargs)
