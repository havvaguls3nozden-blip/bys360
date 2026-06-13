from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""Communication required phase route bridge.

Faz 1I ile route manifest sadece bu bridge'i required katmanda yukler.
Optional phase route modulleri manifestte ayrica kalir. Bu dosya required
route tarafini tek sahipte toplar ve sonraki gercek govde eritmesi icin
hafif bir merkez saglar.
"""

from importlib import import_module

_REQUIRED = [
    ".phase1_routes",
    ".phase2_routes",
    ".phase3_routes",
    ".phase4_routes",
    ".phase5_routes",
]

LOADED_REQUIRED_PHASE_ROUTE_MODULES: list[str] = []

for module_name in _REQUIRED:
    import_module(module_name, __package__)
    LOADED_REQUIRED_PHASE_ROUTE_MODULES.append(module_name.rsplit(".", 1)[-1])


def load_optional_phase_routes(module_names: list[str]) -> tuple[list[str], dict[str, str]]:
    """Opsiyonel route modullerini isterse yukleyen yardimci.

    Route manifest optional modulleri ayri tuttugu icin bu helper sadece
    inspect veya smoke scriptlerinde gerekirse kullanilsin diye korunur.
    """
    loaded: list[str] = []
    failed: dict[str, str] = {}
    for module_name in module_names:
        try:
            import_module(f".{module_name}", __package__)
            loaded.append(module_name)
        except Exception as exc:  # pragma: no cover - runtime safety helper
            logger.exception("BYS360 V6C guarded exception | file=app/communication/phase_family_routes.py | line=42")
            failed[module_name] = str(exc)
    return loaded, failed


__all__ = [
    "LOADED_REQUIRED_PHASE_ROUTE_MODULES",
    "load_optional_phase_routes",
]
