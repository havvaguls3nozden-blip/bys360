# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Assistant service extraction target for mobile routes."""
from __future__ import annotations


# P1.9 V2.17.19 - mobil asistan route servis delegasyonu.
def delegate_mobile_b49_assistant_v2_ask(*args, **kwargs):
    """Mevcut davranışı koruyarak asistan route işlemini legacy gövdeye devreder."""
    from app.api.mobile import routes as mobile_routes
    legacy = mobile_routes._bys360_legacy_mobile_b49_assistant_v2_ask
    return legacy(*args, **kwargs)
