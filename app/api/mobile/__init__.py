from __future__ import annotations



from flask import Blueprint

mobile_api_bp = Blueprint("mobile_api", __name__, url_prefix="/api/mobile")

# Route import is intentionally after blueprint creation.
from . import routes  # noqa: E402,F401
from . import performance_routes  # noqa: E402,F401


def _exempt_mobile_api_from_csrf() -> None:
    """Mobile API uses JSON + Bearer token auth; it must not require browser CSRF tokens."""
    try:
        from app.extensions import csrf
        csrf.exempt(mobile_api_bp)
    except Exception:
        # Some test/import contexts may not initialize Flask-WTF yet.
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/__init__.py:19)")


def register_mobile_api_real_v1(app):
    """Register BYS360 native mobile API blueprint once and exempt it from CSRF."""
    _exempt_mobile_api_from_csrf()
    if "mobile_api" not in app.blueprints:
        app.register_blueprint(mobile_api_bp)
    try:
        from app.extensions import csrf
        csrf.exempt(mobile_api_bp)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/__init__.py)")
    return app
