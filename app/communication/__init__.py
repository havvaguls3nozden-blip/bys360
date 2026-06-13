"""Communication package bootstrap.

Faz 1B ile route ailesi yükleme listesi `route_manifest.py` içine taşındı.
Amaç davranışı değiştirmek değil; import sahipliğini tek dosyada görünür hale
getirmek ve sonraki fazlarda phase dosyalarını güvenli biçimde eritmek.
"""

from app.route_family_loader import load_optional_modules, load_required_modules

from .route_manifest import OPTIONAL_ROUTE_MODULES, REQUIRED_ROUTE_MODULES, ROUTE_FAMILY

LOADED_ROUTE_MODULES = load_required_modules(__name__, REQUIRED_ROUTE_MODULES)
OPTIONAL_LOADED_ROUTE_MODULES, OPTIONAL_FAILED_ROUTE_MODULES = load_optional_modules(
    __name__, OPTIONAL_ROUTE_MODULES
)

__all__ = [
    "ROUTE_FAMILY",
    "LOADED_ROUTE_MODULES",
    "OPTIONAL_LOADED_ROUTE_MODULES",
    "OPTIONAL_FAILED_ROUTE_MODULES",
]