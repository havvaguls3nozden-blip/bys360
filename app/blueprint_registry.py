
"""BYS360 blueprint kayıt ara katmanı.

Core Refactor Faz 2 ile gerçek blueprint/route bootstrapping sozlesmesi
app.bootstrap.route_bootstrap dosyasina tasindi. Bu modul geriye donuk uyumluluk
icin ayni isimleri disari verir; eski importlar calismaya devam eder.
"""
from __future__ import annotations

from app.bootstrap.route_bootstrap import (
    CORE_BLUEPRINT_SEQUENCE,
    BlueprintRegistration,
    collect_blueprint_snapshot,
    configure_route_bootstrap,
    register_application_blueprints,
)

__all__ = [
    "BlueprintRegistration",
    "CORE_BLUEPRINT_SEQUENCE",
    "collect_blueprint_snapshot",
    "configure_route_bootstrap",
    "register_application_blueprints",
]
