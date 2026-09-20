"""BYS360 Assistant V2 -- Settings Center V2 integration contract.

Proves the `/settings-center/ai-agent` page (settings_center_virtual_assistant)
renders real, native "BYS360 AI Core" status facts (capability counts,
module coverage, cross-module intelligence count) for an authorized admin,
and that no provider/API-key/model-endpoint language survives on the page
-- the BYS360 Native AI Only architecture has no external provider to
report on, so the page must not imply one exists.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Settings_Test_Pw_1!"

_FORBIDDEN_PROVIDER_STRINGS = (
    "API Key", "api_key", "AI_API_KEY", "AI_BASE_URL", "OpenAI", "openai_compatible",
    "Bearer ", "model endpoint", "provider_mode",
)


def _create_user(app, *, sicil_no, role, password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User.query.filter_by(sicil_no=sicil_no).first()
        if existing is not None:
            return existing.id
        user = User(
            sicil_no=sicil_no,
            email=f"{sicil_no}@ktb.gov.tr",
            ad="SettingsIntegration",
            soyad="Test",
            role=role,
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, sicil_no, password=_PASSWORD):
    # Explicit logout first: the `client` fixture is session-scoped and
    # shared across every test function in this file, so a prior test's
    # authenticated session must be cleared before switching users.
    client.get("/logout", follow_redirects=False)
    response = client.post("/login", data={"sicil_or_email": sicil_no, "password": password}, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" not in response.headers.get("Location", "")
    return response


def test_virtual_assistant_settings_page_shows_native_ai_core_facts(app, client):
    _create_user(app, sicil_no="av2_settings_admin", role="admin")
    _login(client, "av2_settings_admin")

    response = client.get("/settings-center/ai-agent")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    assert "BYS360 AI Core" in body
    assert "Yerli niyet motoru" in body
    assert "49 yetenek" in body
    assert "Modüller arası zekâ" in body
    assert "Kullanım rehberleri" in body
    assert "Web arka ucu" in body
    assert "Mobil arka uç" in body
    assert "Assistant V2" in body
    assert "Tekil zekâ motoru" in body


def test_virtual_assistant_settings_page_has_no_provider_or_secret_language(app, client):
    """BYS360 Native AI Only: the page must never mention a provider, API
    key, or model endpoint -- there is none to configure."""
    _create_user(app, sicil_no="av2_settings_admin_noprovider", role="admin")
    _login(client, "av2_settings_admin_noprovider")

    response = client.get("/settings-center/ai-agent")
    assert response.status_code == 200
    body = response.get_data(as_text=True)

    for forbidden in _FORBIDDEN_PROVIDER_STRINGS:
        assert forbidden not in body, f"forbidden provider/secret-adjacent string found on page: {forbidden!r}"


def test_virtual_assistant_settings_page_denied_for_non_admin(app, client):
    _create_user(app, sicil_no="av2_settings_personel", role="personel")
    _login(client, "av2_settings_personel")

    response = client.get("/settings-center/ai-agent")
    assert response.status_code == 403
