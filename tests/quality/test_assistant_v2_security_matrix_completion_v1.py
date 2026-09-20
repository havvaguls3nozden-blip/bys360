"""BYS360 Assistant V2 -- remaining security matrix items (mandate Phase K):
horizontal access/IDOR, disabled capability, malformed/SQL-like query
safety, and audit-content inspection (no secrets, no full payload).
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
            sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Sec", soyad="Test",
            role=role, is_active=True, must_change_password=False, must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _get_user(app, user_id):
    from app.models import User

    return User.query.get(user_id)


def _login(client, sicil_no, password=_PASSWORD):
    client.get("/logout", follow_redirects=False)
    response = client.post("/login", data={"sicil_or_email": sicil_no, "password": password}, follow_redirects=False)
    assert response.status_code == 302
    return response


# ---------------------------------------------------------------------------
# Horizontal access / IDOR / different user same role
# ---------------------------------------------------------------------------


def test_horizontal_access_user_cannot_read_another_users_ticket(app):
    """IDOR: a support ticket created by user A must not be readable by
    user B via support_help_read_ticket_detail, even though both hold the
    same role and both are independently authorized for the capability
    itself -- the adapter's own ownership/assignee scoping must enforce
    this, not just the capability-level menu_key gate."""
    from app.extensions import db
    from app.models.support_models import SupportTicket
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    user_a_id = _create_user(app, sicil_no="av2_sec_idor_a", role="personel")
    user_b_id = _create_user(app, sicil_no="av2_sec_idor_b", role="personel")

    with app.app_context():
        ticket = SupportTicket.query.filter_by(ticket_no="AV2-SEC-IDOR-1").first()
        if ticket is None:
            ticket = SupportTicket(
                ticket_no="AV2-SEC-IDOR-1", title="A'nin bileti", description="test",
                ticket_type="general", module_name="assistant_v2_test", created_by_user_id=user_a_id, status="open", priority="normal",
            )
            db.session.add(ticket)
            db.session.commit()
        ticket_id = ticket.id

    with app.app_context():
        user_b = _get_user(app, user_b_id)
        result = invoke_capability(user_b, "support_help_read_ticket_detail", ticket_id=ticket_id)

    # The capability itself allows personel (support_my_tickets is
    # self-scoped, so status must not be ACCESS_DENIED at the capability
    # gate) -- but the returned data must not be user A's ticket.
    assert result.status is not AssistantResultStatus.ACCESS_DENIED
    assert result.data is None or (isinstance(result.data, dict) and result.data.get("id") != ticket_id)


def test_different_user_same_role_gets_independently_scoped_self_data(app):
    """Two different personel-role users asking for 'my tickets' must each
    see only their own tickets -- proving the self-scope filter uses the
    LIVE request's user, not a cached/shared value."""
    from app.extensions import db
    from app.models.support_models import SupportTicket
    from app.services.assistant_v2.capability_dispatcher import invoke_capability

    user_a_id = _create_user(app, sicil_no="av2_sec_sameRole_a", role="personel")
    user_b_id = _create_user(app, sicil_no="av2_sec_sameRole_b", role="personel")

    with app.app_context():
        if SupportTicket.query.filter_by(ticket_no="AV2-SEC-SAMEROLE-A").first() is None:
            db.session.add(SupportTicket(
                ticket_no="AV2-SEC-SAMEROLE-A", title="A ticket", description="t",
                ticket_type="general", module_name="assistant_v2_test", created_by_user_id=user_a_id, status="open", priority="normal",
            ))
            db.session.commit()

    with app.app_context():
        user_b = _get_user(app, user_b_id)
        result_b = invoke_capability(user_b, "support_help_list_my_tickets")

    tickets_b = result_b.data or []
    assert all(t.get("ticket_no") != "AV2-SEC-SAMEROLE-A" for t in tickets_b)


# ---------------------------------------------------------------------------
# Disabled capability
# ---------------------------------------------------------------------------


def test_disabled_capability_is_unavailable_even_for_admin(app, monkeypatch):
    from dataclasses import replace

    from app.services.assistant_v2 import capability_dispatcher
    from app.services.assistant_v2.capability_registry import get_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    real_entry = get_capability("communication_list_active_announcements")
    assert real_entry is not None
    disabled_entry = replace(real_entry, active=False)
    monkeypatch.setattr(
        capability_dispatcher, "get_capability",
        lambda key: disabled_entry if key == "communication_list_active_announcements" else get_capability(key),
    )

    admin_id = _create_user(app, sicil_no="av2_sec_disabled_cap", role="admin")
    with app.app_context():
        admin = _get_user(app, admin_id)
        result = capability_dispatcher.invoke_capability(admin, "communication_list_active_announcements")
    assert result.status is AssistantResultStatus.CAPABILITY_UNAVAILABLE


# ---------------------------------------------------------------------------
# Malformed / SQL-like / arbitrary record ID injection
# ---------------------------------------------------------------------------


def test_malformed_query_never_crashes_the_api(app, client):
    _create_user(app, sicil_no="av2_sec_malformed", role="admin")
    _login(client, "av2_sec_malformed")

    for garbage in ("", "   ", "\x00\x01\x02", "{{{[[[", "' OR '1'='1", "%00%00", "a" * 5000):
        response = client.post("/ai-agent/api/v2/ask", json={"question": garbage})
        assert response.status_code == 200


def test_sql_like_text_is_treated_as_inert_query_text(app, client):
    _create_user(app, sicil_no="av2_sec_sqllike", role="admin")
    _login(client, "av2_sec_sqllike")

    response = client.post(
        "/ai-agent/api/v2/ask",
        json={"question": "'; DROP TABLE users; -- aktif duyurulari listele"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] in ("DATA_FOUND", "NO_DATA", "AMBIGUOUS_REQUEST", "OUT_OF_SCOPE", "CONVERSATIONAL_RESPONSE")


def test_missing_required_parameter_is_ambiguous_not_a_crash(app, client):
    """'sicil kaydını göster' routes to personnel_hr_read_personnel_record,
    which requires sicil_no -- free text alone never supplies it. The
    dispatcher must recognize the parameter is unfulfillable BEFORE
    invoking the handler and return a clarification, never a raw
    SYSTEM_ERROR/crash from a handler called with missing arguments
    (mandate security matrix item 13: missing required parameter)."""
    _create_user(app, sicil_no="av2_sec_missing_param", role="admin")
    _login(client, "av2_sec_missing_param")

    response = client.post("/ai-agent/api/v2/ask", json={"question": "sicil kaydını göster"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "AMBIGUOUS_REQUEST"
    assert body["clarification"]["reason"] == "missing_required_parameter"


def test_arbitrary_record_id_injection_via_follow_up_returns_no_data_not_someone_elses_record(app, client):
    """A follow-up resolving to an entity id that was never actually in the
    stored conversation state (a forged/edited id) must not silently return
    real data for that id -- _narrow_to_entity only ever narrows within the
    FRESH, already-authorized result set, never trusts a client-supplied id
    directly."""
    from app.services.assistant_v2.service import _narrow_to_entity

    fresh_authorized_data = [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]
    forged_id = 999999
    narrowed = _narrow_to_entity(fresh_authorized_data, forged_id)
    assert narrowed == []


# ---------------------------------------------------------------------------
# Audit content inspection
# ---------------------------------------------------------------------------


def test_audit_log_call_never_contains_secrets_or_full_payload(app, monkeypatch):
    """Inspects the ACTUAL kwargs passed to insert_agent_request_log --
    proves the audit write never includes a raw record payload or anything
    secret-shaped, only the bounded summary/intent/status fields the
    dispatcher already builds."""
    from app.services.assistant_v2 import capability_dispatcher
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    captured = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(capability_dispatcher, "insert_agent_request_log", _capture)

    admin_id = _create_user(app, sicil_no="av2_sec_audit_admin", role="admin")
    with app.app_context():
        admin = _get_user(app, admin_id)
        result = capability_dispatcher.invoke_capability(admin, "personnel_hr_list_personnel")

    assert result.status is not AssistantResultStatus.ACCESS_DENIED
    assert captured, "expected insert_agent_request_log to have been called"
    full_dump = str(captured)
    assert "password" not in full_dump.lower()
    assert "secret" not in full_dump.lower()
    assert "api_key" not in full_dump.lower()
    # response_summary must be a short, bounded status string -- never a
    # dump of the actual returned personnel rows.
    assert len(captured.get("response_summary", "")) < 500
    assert "sicil_no" not in captured.get("response_summary", "")
