
"""BYS360 template helper kayıt merkezi.

Bootstrap katmanını sade tutmak için şablon yardımcıları burada toplanır.
BYS360_MAINTENANCE_V13_P1_TEMPLATE_HELPERS
"""
from __future__ import annotations

from flask import Flask

from app.template_helpers.category_average import register_category_average_helpers
from app.template_helpers.development_guidance import register_development_guidance_helpers


def register_template_helpers(app: Flask) -> None:
    """Tüm BYS360 şablon yardımcılarını tek çağrıyla bağlar."""
    register_category_average_helpers(app)
    register_development_guidance_helpers(app)


__all__ = ["register_template_helpers"]
