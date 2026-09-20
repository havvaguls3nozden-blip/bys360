"""BYS360 Assistant V2 -- mobile backend cutover contract (mandate Phase H/I/P).

The live mobile endpoint `/api/mobile/assistant/v2/ask` now answers via
AssistantV2Service + MobilePresentationAdapter instead of the independent
rule-based engine. Bearer auth, HTTP status behavior, and the exact JSON
field names the live Flutter AssistantScreen reads (answer, module,
route_hint, required_roles, steps, warnings, control_items,
suggested_questions, intent) are preserved.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"

_MOBILE_FIELDS = (
    "answer", "module", "route_hint", "required_roles", "steps",
    "warnings", "control_items", "suggested_questions", "intent",
)


def _create_user(app, *, sicil_no, role, password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User.query.filter_by(sicil_no=sicil_no).first()
        if existing is not None:
            return existing.id
        user = User(
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Mobile", soyad="Test",
            role=role, is_active=True, must_change_password=False, must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _mobile_token(app, user_id):
    from app.api.mobile.shared import _issue_token
    from app.models import User

    with app.app_context():
        user = User.query.get(user_id)
        return _issue_token(user)


def _ask_mobile(client, token, question):
    # The session-scoped `client` fixture is shared across every test file
    # in a full run -- an earlier assistant_v2 web test may have left a
    # Flask-Login session cookie behind, which can interfere with a mobile
    # bearer-auth request. Clearing it first keeps this file's assertions
    # independent of test execution order (same convention already used by
    # every other assistant_v2 test file's `_login` helper).
    client.get("/logout", follow_redirects=False)
    return client.post(
        "/api/mobile/assistant/v2/ask",
        json={"question": question},
        headers={"Authorization": f"Bearer {token}"},
    )


# ---------------------------------------------------------------------------
# Auth preserved
# ---------------------------------------------------------------------------


def test_mobile_endpoint_requires_bearer_token(client):
    client.get("/logout", follow_redirects=False)
    response = client.post("/api/mobile/assistant/v2/ask", json={"question": "merhaba"})
    assert response.status_code in (401, 403)


def test_mobile_endpoint_accepts_valid_bearer_token(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_auth_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "merhaba")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Engine + schema
# ---------------------------------------------------------------------------


def test_mobile_endpoint_uses_assistant_v2_service(app, client, monkeypatch):
    from app.services.assistant_v2 import service as service_module

    called = {"value": False}
    real_ask = service_module.AssistantV2Service.ask

    def _tracking_ask(self, *args, **kwargs):
        called["value"] = True
        return real_ask(self, *args, **kwargs)

    monkeypatch.setattr(service_module.AssistantV2Service, "ask", _tracking_ask)

    admin_id = _create_user(app, sicil_no="av2_mobile_engine_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "merhaba")
    assert response.status_code == 200
    assert called["value"] is True


def test_mobile_response_has_exact_flutter_schema(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_schema_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "merhaba")
    body = response.get_json()
    for field in _MOBILE_FIELDS:
        assert field in body, f"missing field {field!r}"
    assert isinstance(body["required_roles"], list)
    assert isinstance(body["steps"], list)
    assert isinstance(body["warnings"], list)
    assert isinstance(body["control_items"], list)
    assert isinstance(body["suggested_questions"], list)


def test_mobile_response_never_leaks_internal_status_or_capability_key(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_noleak_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "personel nasıl eklenir")
    body = response.get_json()
    assert "status" not in body
    assert "capability_key" not in body
    assert "conversation_id" not in body


# ---------------------------------------------------------------------------
# Authorization: denial never leaks data, route_hint only when authorized
# ---------------------------------------------------------------------------


def test_mobile_unauthorized_capability_denies_without_leaking_data(app, client):
    from app.route_support import can_access_menu
    from app.services.assistant_v2.capability_registry import ASSISTANT_CAPABILITY_REGISTRY

    personel_id = _create_user(app, sicil_no="av2_mobile_denied_personel", role="personel")
    with app.test_request_context():
        from app.models import User

        personel = User.query.get(personel_id)
        denied_entry = next(
            (
                e for e in ASSISTANT_CAPABILITY_REGISTRY
                if e.permission_key and not e.is_self_describing and not can_access_menu(personel, e.permission_key)
            ),
            None,
        )
    assert denied_entry is not None
    token = _mobile_token(app, personel_id)

    response = _ask_mobile(client, token, denied_entry.intent_tags[0])
    assert response.status_code == 200
    body = response.get_json()
    assert body["intent"] in ("ACCESS_DENIED", "AMBIGUOUS_REQUEST")
    assert body["route_hint"] == ""
    assert body["required_roles"] == [] or not denied_entry.permission_key or denied_entry.permission_key not in str(body)


def test_mobile_route_hint_only_present_when_user_authorized(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_routehint_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "personel nasıl eklenir")
    body = response.get_json()
    assert body["intent"] == "PROCEDURAL_GUIDE"
    assert body["route_hint"]  # authorized admin -> real, resolved URL


def test_mobile_route_hint_empty_when_user_not_authorized_for_guide(app, client):
    personel_id = _create_user(app, sicil_no="av2_mobile_routehint_personel", role="personel")
    token = _mobile_token(app, personel_id)

    response = _ask_mobile(client, token, "personel nasıl eklenir")
    body = response.get_json()
    assert body["intent"] == "ACCESS_DENIED"
    assert body["route_hint"] == ""


# ---------------------------------------------------------------------------
# Procedural steps populated correctly
# ---------------------------------------------------------------------------


def test_mobile_procedural_question_returns_real_steps(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_steps_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "destek talebi nasıl açılır")
    body = response.get_json()
    assert body["intent"] == "PROCEDURAL_GUIDE"
    assert len(body["steps"]) >= 3
    assert body["module"] == "Destek / Yardım Merkezi"


def test_mobile_data_question_never_carries_guide_steps(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_nosteps_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "merhaba")
    body = response.get_json()
    assert body["steps"] == []
    assert body["warnings"] == []


# ---------------------------------------------------------------------------
# Backend error safety + contract stability
# ---------------------------------------------------------------------------


def test_mobile_endpoint_malformed_question_never_crashes(app, client):
    admin_id = _create_user(app, sicil_no="av2_mobile_malformed_admin", role="admin")
    token = _mobile_token(app, admin_id)

    for garbage in ("", "   ", "\x00\x01", "{{{[[[", "a" * 5000):
        response = _ask_mobile(client, token, garbage)
        assert response.status_code == 200


def test_mobile_endpoint_handler_exception_returns_safe_response_not_500(app, client, monkeypatch):
    from app.services.assistant_v2 import service as service_module

    def _boom(self, *args, **kwargs):
        raise RuntimeError("simulated internal failure")

    monkeypatch.setattr(service_module.AssistantV2Service, "ask", _boom)

    admin_id = _create_user(app, sicil_no="av2_mobile_crash_admin", role="admin")
    token = _mobile_token(app, admin_id)

    response = _ask_mobile(client, token, "merhaba")
    assert response.status_code == 200
    body = response.get_json()
    assert body["intent"] == "SYSTEM_ERROR"
    assert body["source"] == "bys360_mobile_assistant_v2_8_49"
