# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest


CRITICAL_ROUTES = [
    "/dashboard",
    "/dashboard/heavy-panels",
    "/settings",
    "/performance/feedback-pipeline",
    "/performance/feedback-corporate-cleanup",
    "/performance/process-tracking",
    "/performance/process-reports",
    "/performance/president-approvals/1/card",
    "/performance/feedback-aftercare",
    "/performance/feedback-final-gate",
]


@pytest.fixture(autouse=True)
def _v58_disable_login(app):
    app.config["LOGIN_DISABLED"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["CSRF_ENABLED"] = False


def test_v58_assistant_context_processors_are_registered(app):
    keys = {}
    with app.test_request_context("/dashboard"):
        for processor in app.template_context_processors.get(None, []):
            try:
                keys.update(processor() or {})
            except Exception:
                # Context processor hatası template render aşamasında 500'e döner; bu testte açık yakalanır.
                raise

    assert "assistant_module_visibility_payload" in keys
    assert "assistant_module_visibility_payload_json" in keys
    assert "assistant_shortcut_visibility_map" in keys
    assert "assistant_shortcut_visibility_json" in keys


@pytest.mark.parametrize("path", CRITICAL_ROUTES)
def test_v58_critical_routes_never_return_500(client, path):
    response = client.get(path)
    assert response.status_code != 500


def test_v58_smoke_route_count_contract():
    assert len(CRITICAL_ROUTES) >= 10
