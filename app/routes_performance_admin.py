"""Legacy performance-admin route shim.

Personel notu: Bunlari bilerek silmedim. Canli kod artik burada degil ama bazen
gece 03.00'te "bu nereden kalmisti" diye donup bakiyorum.
"""
from __future__ import annotations

LEGACY_SHIM = True
LEGACY_RUNTIME_STATUS = "archived_reference_only"
LEGACY_ARCHIVE_MODULE = "app.legacy_routes_archive.routes_performance_admin"
LEGACY_ROUTE_FAMILY = "performance_admin"
LEGACY_NOTE = (
    "Bu modül canlı route kaynağı değildir. Eski/paralel route implementasyonu "
    "app.legacy_routes_archive altında korunmuştur. Canlı akış app.routes ve "
    "app.route_registry.main_bp üzerinden yürür."
)

__all__ = [
    "LEGACY_SHIM",
    "LEGACY_RUNTIME_STATUS",
    "LEGACY_ARCHIVE_MODULE",
    "LEGACY_ROUTE_FAMILY",
    "LEGACY_NOTE",
]