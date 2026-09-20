"""BYS360 Assistant V2 -- web conversation_id integration contract (mandate
Phase B/C): the legacy-shaped `/ai-agent/api/ask` endpoint (the one the real
web widget/panel actually call) now accepts and returns `conversation_id`,
closing the gap where the feature was fully built and tested at the
AssistantV2Service/API-v2 layer but never actually reachable from the live
web UI because that UI's own endpoint silently dropped it.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"


def _create_user(app, *, sicil_no, role, password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User.query.filter_by(sicil_no=sicil_no).first()
        if existing is not None:
            return existing.id
        user = User(
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Conv", soyad="Test",
            role=role, is_active=True, must_change_password=False, must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _set_role(app, user_id, role):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = User.query.get(user_id)
        user.role = role
        db.session.commit()


def _login(client, sicil_no, password=_PASSWORD):
    client.get("/logout", follow_redirects=False)
    response = client.post("/login", data={"sicil_or_email": sicil_no, "password": password}, follow_redirects=False)
    assert response.status_code == 302
    return response


def _ask(client, question, conversation_id=None):
    payload = {"question": question}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    response = client.post("/ai-agent/api/ask", json=payload)
    assert response.status_code == 200
    return response.get_json()


def _create_active_announcement(app, *, title="AV2 Web Conv Test Duyuru"):
    from app.extensions import db
    from app.models.announcement_popup_models import Announcement

    with app.app_context():
        existing = Announcement.query.filter_by(title=title).first()
        if existing is not None:
            return existing.id
        announcement = Announcement(title=title, body="test body", is_active=True)
        db.session.add(announcement)
        db.session.commit()
        return announcement.id


def test_first_question_returns_a_conversation_id(app, client):
    _create_user(app, sicil_no="av2_webconv_first", role="admin")
    _login(client, "av2_webconv_first")

    body = _ask(client, "merhaba")
    assert body.get("conversation_id")


def test_second_question_reusing_conversation_id_keeps_same_conversation(app, client):
    _create_user(app, sicil_no="av2_webconv_reuse", role="admin")
    _login(client, "av2_webconv_reuse")

    turn1 = _ask(client, "merhaba")
    cid = turn1["conversation_id"]
    assert cid

    turn2 = _ask(client, "teşekkür ederim", conversation_id=cid)
    assert turn2["conversation_id"] == cid


def test_follow_up_ilkini_goster_resolves_through_legacy_web_endpoint(app, client):
    """Real mechanically-valid pair already proven at the service layer
    (test_assistant_v2_conversation_and_service_contract_v1.py) -- proves
    it ALSO works through the exact endpoint the live web widget calls,
    which is the actual gap this phase closes."""
    _create_active_announcement(app)
    _create_user(app, sicil_no="av2_webconv_followup", role="admin")
    _login(client, "av2_webconv_followup")

    turn1 = _ask(client, "aktif duyurulari listele")
    cid = turn1["conversation_id"]
    assert cid
    assert turn1["answer"]

    turn2 = _ask(client, "ilkini göster", conversation_id=cid)
    assert turn2["conversation_id"] == cid
    assert turn2["answer"]
    # Never AMBIGUOUS ("no previous list") -- proves the follow-up genuinely
    # resolved against turn 1's real, server-side conversation state.
    assert "tam olarak anlayamadım" not in turn2["answer"].lower()


def test_permission_revoked_between_web_turns_denies_and_does_not_replay(app, client):
    """Same property already proven at the service layer, now proven
    through the actual web-facing endpoint."""
    admin_id = _create_user(app, sicil_no="av2_webconv_revoke", role="admin")
    _login(client, "av2_webconv_revoke")

    turn1 = _ask(client, "personel sicil kaydini oku")
    cid = turn1["conversation_id"]
    assert cid

    _set_role(app, admin_id, "personel")

    turn2 = _ask(client, "ilkini göster", conversation_id=cid)
    assert turn2["conversation_id"] == cid
    # A genuine denial or a safe re-ambiguation -- never a replay of
    # turn 1's (now-unauthorized) content.
    assert "erişim yetkisi" in turn2["answer"].lower() or "tam olarak anlayamadım" in turn2["answer"].lower()


def test_foreign_conversation_id_is_never_honored_across_users(app, client):
    _create_user(app, sicil_no="av2_webconv_usera", role="admin")
    _create_user(app, sicil_no="av2_webconv_userb", role="admin")

    _login(client, "av2_webconv_usera")
    turn1 = _ask(client, "merhaba")
    cid = turn1["conversation_id"]

    _login(client, "av2_webconv_userb")
    turn2 = _ask(client, "merhaba", conversation_id=cid)
    assert turn2["conversation_id"] != cid


def test_conversation_id_field_is_a_string_or_absent_never_leaks_internal_shape(app, client):
    _create_user(app, sicil_no="av2_webconv_shape", role="admin")
    _login(client, "av2_webconv_shape")

    body = _ask(client, "merhaba")
    assert isinstance(body.get("conversation_id"), str)
