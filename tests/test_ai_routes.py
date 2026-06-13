from __future__ import annotations

from flask import Blueprint

from app.ai.routes import _run_json_service
from app.services.ai.guardrails import AIAccessDenied, AIServiceDisabled


def test_run_json_service_success(app):
    with app.test_request_context('/ai/test'):
        response, status = _run_json_service(lambda: {'ok': True}, commit=False)
        assert status == 200
        assert response.get_json()['ok'] is True


def test_run_json_service_maps_403(app):
    with app.test_request_context('/ai/test'):
        response, status = _run_json_service(lambda: (_ for _ in ()).throw(AIAccessDenied('yasak')), commit=False)
        assert status == 403
        assert response.get_json()['ok'] is False


def test_run_json_service_maps_503(app):
    with app.test_request_context('/ai/test'):
        response, status = _run_json_service(lambda: (_ for _ in ()).throw(AIServiceDisabled('kapali')), commit=False)
        assert status == 503
        assert response.get_json()['ok'] is False
