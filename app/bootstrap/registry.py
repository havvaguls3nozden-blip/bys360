
"""Geriye donuk bootstrap registry uyumluluk katmani.

Core Refactor Faz 2 sonrasinda blueprint kayit akisi route_bootstrap modulune
alinmistir. Eski register_core_blueprints / attach_runtime_route_manifest
cagrilari bozulmasin diye bu dosya ince wrapper olarak korunur.
"""
from __future__ import annotations

from flask import Flask

from app.bootstrap.route_bootstrap import (
    attach_runtime_route_manifest,
    configure_route_bootstrap,
    register_application_blueprints,
)


def register_core_blueprints(app: Flask) -> None:
    """Eski isim: core blueprintleri yeni route bootstrap katmani ile kaydeder."""
    register_application_blueprints(app)


__all__ = [
    "attach_runtime_route_manifest",
    "configure_route_bootstrap",
    "register_application_blueprints",
    "register_core_blueprints",
]
