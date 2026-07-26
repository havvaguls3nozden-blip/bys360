from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import app.api.mobile as mobile_pkg
from app.api.mobile.services import assistant_service as svc


@pytest.fixture()
def fake_assistant_chat(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    fake = types.ModuleType("app.api.mobile.domains.assistant_chat")
    monkeypatch.setitem(sys.modules, "app.api.mobile.domains.assistant_chat", fake)
    monkeypatch.setattr(mobile_pkg.domains, "assistant_chat", fake, raising=False)
    return fake


def _recording_legacy(return_value: Any):
    calls: list[dict[str, Any]] = []

    def legacy(*args: Any, **kwargs: Any) -> Any:
        calls.append({"args": args, "kwargs": kwargs})
        return return_value

    legacy.calls = calls  # type: ignore[attr-defined]
    return legacy


def test_delegate_mobile_b49_assistant_v2_ask_forwards_to_legacy(
    fake_assistant_chat: types.ModuleType,
) -> None:
    legacy = _recording_legacy({"answer": "ok"})
    fake_assistant_chat._bys360_legacy_mobile_b49_assistant_v2_ask = legacy

    result = svc.delegate_mobile_b49_assistant_v2_ask("hello", user_id=42)

    assert result == {"answer": "ok"}
    assert legacy.calls == [  # type: ignore[attr-defined]
        {"args": ("hello",), "kwargs": {"user_id": 42}}
    ]


def test_delegate_mobile_b49_assistant_v2_ask_raises_when_legacy_missing(
    fake_assistant_chat: types.ModuleType,
) -> None:
    with pytest.raises(AttributeError, match="_bys360_legacy_mobile_b49_assistant_v2_ask"):
        svc.delegate_mobile_b49_assistant_v2_ask()


def test_assistant_v2_ask_route_end_to_end(app, client) -> None:
    """Real /assistant/v2/ask endpoint must not 500 via the broken delegate lookup.

    Regression guard for the production bug where delegate_mobile_b49_assistant_v2_ask
    looked up the legacy handler on app.api.mobile.routes instead of
    app.api.mobile.domains.assistant_chat, where it actually lives.
    """
    from app.api.mobile.shared import _issue_token
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = db.session.query(User).filter_by(sicil_no="phase4al-assistant-test").one_or_none()
        if user is None:
            user = User(
                sicil_no="phase4al-assistant-test",
                email="phase4al-assistant-test@example.invalid",
                password_hash="x",
                ad="Test",
                soyad="User",
            )
            db.session.add(user)
            db.session.commit()
        token = _issue_token(user)

    response = client.post(
        "/api/mobile/assistant/v2/ask",
        json={"question": "performans dönemi nasıl oluşturulur?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["source"] == "bys360_mobile_assistant_v2_8_49"
