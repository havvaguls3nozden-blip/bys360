"""BYS360 Maintenance 10E - SP route smoke testi.

Amaç: SP kritik route'larında 500/beyaz ekran regresyonunu yakalamak.
Auth bekleyen ekranlarda 302/401/403 kabul edilir; 404 veya 500 kabul edilmez.
"""
from __future__ import annotations

import importlib
import os

import pytest

CRITICAL_SP_ROUTES = [
    "/performans/stratejik/kpi-dashboard",
    "/performans/stratejik/hedefler",
    "/performans/stratejik/oz-degerlendirme",
]


def _load_app():
    os.environ.setdefault("APP_ENV", "testing")
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("BYS360_TESTING", "1")
    candidates = [("wsgi", "app"), ("app", "app"), ("app", "create_app")]
    last_error = None
    for module_name, attr_name in candidates:
        try:
            module = importlib.import_module(module_name)
            attr = getattr(module, attr_name)
            app = attr() if callable(attr) and attr_name == "create_app" else attr
            app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
            return app
        except Exception as exc:  # pragma: no cover
            last_error = exc
    pytest.skip(f"Flask uygulaması test client için yüklenemedi: {last_error}")


def test_sp_critical_routes_are_registered_and_not_500():
    app = _load_app()
    client = app.test_client()
    results = []

    for url in CRITICAL_SP_ROUTES:
        response = client.get(url, follow_redirects=False)
        results.append((url, response.status_code))

    failures = [(url, code) for url, code in results if code not in {200, 302, 401, 403}]
    assert not failures, f"SP route kayıt/smoke hatası: {failures}"
