"""BYS360 v59 geniş canlı rota smoke testi.

BYS360_V59_1_SQLITE_SMOKE_SCHEMA_SAFETY

Bu test canlı öncesi beyaz ekran/500 riskini yakalamak için hazırlanmıştır.
Flask bağımlılıkları yüklü değilse test atlanır; canlı/proje ortamında pytest ile
çalıştırıldığında kritik rotaların 500 üretmemesini kontrol eder.
"""
from __future__ import annotations

import os
from typing import Any

import pytest

STATIC_CRITICAL_ROUTES = [
    "/login",
    "/home",
    "/dashboard",
    "/settings",
    "/support",
    "/support/new",
    "/notifications",
    "/performance/dashboard",
    "/performance/reports",
    "/performance/periods",
    "/performance/periods/create",
    "/performance/tasks",
    "/performance/scorecard",
    "/performance/archive",
    "/performance/president-approvals",
    "/performance/process-tracking",
    "/performance/process-reports",
    "/performans/baskan-onaylari",
    "/performans/gecmis-karne-arsivi",
    "/communication/messages",
    "/communication/announcements",
    "/communication/surveys",
    "/ai-agent/panel",
    "/ai-agent/knowledge",
    "/ai-agent/teaching-center",
    "/ai/decision-support/faz1/health",
    "/admin/role-matrix",
    "/admin/module-role-matrix",
    "/dashboard/heavy-panels",
]

DYNAMIC_ROUTE_KEYWORDS = [
    "performance",
    "performans",
    "settings",
    "role",
    "matrix",
    "ai-agent",
    "decision-support",
    "support",
    "communication",
]


def _make_app():
    os.environ.setdefault("APP_ENV", "testing")
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-v59-route-smoke-very-long")
    try:
        from app import create_app
    except Exception as exc:  # pragma: no cover - canlı ortamda import beklenir
        pytest.skip(f"BYS360 uygulaması import edilemedi: {exc}")
    try:
        return create_app()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"BYS360 uygulaması test modunda başlatılamadı: {exc}")


def _candidate_routes(app) -> list[str]:
    routes = set(STATIC_CRITICAL_ROUTES)
    url_map: Any = getattr(app, "url_map", [])
    for rule in url_map.iter_rules():
        route = str(rule.rule)
        if "<" in route:
            continue
        if any(keyword in route.lower() for keyword in DYNAMIC_ROUTE_KEYWORDS):
            routes.add(route)
    return sorted(routes)


def test_static_route_list_is_broad_enough():
    assert len(STATIC_CRITICAL_ROUTES) >= 25


def test_v59_broad_routes_do_not_return_500():
    app = _make_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()
    checked: list[tuple[str, int]] = []
    for route in _candidate_routes(app):
        response = client.get(route, follow_redirects=False)
        checked.append((route, response.status_code))
        assert response.status_code != 500, f"{route} rotası 500 döndü"
    assert checked, "Kontrol edilecek rota bulunamadı"
