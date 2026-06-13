"""Admin yardımcı paket yapısı.

Bu paketin kendi `admin_bp` blueprint'i canlıda register edilmez. Ancak
`app.admin.routes` modülü paylaşılan `main_bp` üzerine admin ve personel
route ailelerini modüler olarak ekler.

Faz 1B ile import listesi `route_manifest.py` içine taşınmıştır.
"""

from flask import Blueprint

from app.route_family_loader import load_optional_modules, load_required_modules

from .route_manifest import OPTIONAL_ROUTE_MODULES, REQUIRED_ROUTE_MODULES, ROUTE_FAMILY

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

LOADED_ROUTE_MODULES = load_required_modules(__name__, REQUIRED_ROUTE_MODULES)
OPTIONAL_LOADED_ROUTE_MODULES, OPTIONAL_FAILED_ROUTE_MODULES = load_optional_modules(
    __name__, OPTIONAL_ROUTE_MODULES
)

__all__ = [
    "ROUTE_FAMILY",
    "admin_bp",
    "LOADED_ROUTE_MODULES",
    "OPTIONAL_LOADED_ROUTE_MODULES",
    "OPTIONAL_FAILED_ROUTE_MODULES",
]