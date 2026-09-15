"""BYS360 H1F -- mobile API + notification-generation raw exception leak fixes.

A repo-wide grep audit of app/api/mobile/**, app/api/mobile-adjacent
notification-GENERATION code (send_*_mail / notify_user / send_*_notification,
wherever it physically lives), and mobile_flutter/** flagged several places
where a caught backend exception's technical text (SMTP error, SQLAlchemy
error, or the raw Python exception class name) could reach a real end user's
screen -- instead of the short, safe, curated Turkish message every sibling
error path in this codebase already uses.

Fixed in this wave (each covered by a test below):

  1. app/api/mobile/domains/kpi_target_management.py -- both the KPI target
     *create* (POST /api/mobile/kpi/target-management) and *progress update*
     (POST /api/mobile/kpi/target-management/<id>/progress) except-blocks
     built their "message" with an f-string embedding
     ``{exc.__class__.__name__}`` (e.g. "...olusturulamadi: IntegrityError").
     Confirmed reachable: mobile_flutter's kpi_target_management_screen.dart
     shows this exact backend "message" field verbatim in a SnackBar via
     BYS360Copy.error() -- which does NOT strip a bare exception class name
     appended after a colon when the rest of the string already contains
     Turkish characters (its untranslated-text heuristic only fires on
     ASCII-only text). Fixed to a fixed safe Turkish message per branch, plus
     added the operator-logging call that was completely missing before
     (neither except block called logger/current_app.logger previously).

  2. app/api/mobile/services/performance_note_route_services.py -- the
     in-period-note create except-block built its message the same way
     (``f'... : {exc.__class__.__name__}'``). The one live mobile screen that
     calls this endpoint today (performance_period_notes_screen.dart) happens
     to always show a fixed local string on any catch, masking this specific
     leak in the *current* UI build -- but the raw class name is still the
     literal value of the wire-format "message" key returned to the device,
     which ApiClient's generic error path (api_client.dart _decode) reads for
     *every* mobile endpoint. Fixed the same way; operator logging already
     existed here (untouched).

  3. app/api/mobile/communication_v2_read_routes.py and
     app/api/mobile/domains/communication_v2_write.py -- three broad
     ``except Exception as exc`` fallbacks additionally shipped a raw
     ``str(exc)[:240]`` in a "warning" JSON key alongside an already-safe
     "message" key. No current mobile_flutter screen reads "warning" on these
     endpoints (grepped repo-wide), so today's shipped UI never paints it --
     but it is still transmitted to the caller's device on every failure,
     which is exactly the kind of technical-detail-in-a-mobile-API-response
     this initiative targets. Removed the "warning" key entirely; the
     existing safe "message" text and the HTTP status codes are untouched.
     NOTE (found, NOT fixed here -- flagged for the coordinator, out of this
     agent's editable scope / not a display-layer bug): the three
     communication-v2 *write* endpoints (send message, create-thread, list
     users) are wired through a delegate
     (app/api/mobile/services/communication_service.py) that resolves its
     legacy handler via ``getattr(app.api.mobile.routes, <name>, None)`` --
     but that name is never actually bound onto the `routes` module anywhere
     in the codebase (confirmed empirically: `hasattr(...)` is False after a
     real app boot). Every call to these three endpoints therefore currently
     raises RuntimeError before ever reaching the code this wave fixed, and
     that RuntimeError is caught by BYS360's app-wide error handler and
     turned into the generic "Sistem Hatasi" 500 page (so it does NOT itself
     leak -- verified with a real test-client POST below). The fix in this
     file is still correct/defensive for whenever that separate wiring bug is
     resolved; tests for finding #3's send/create-thread paths call the
     module-level legacy function directly (bypassing the broken delegate) to
     prove the fix at the unit level, and a dedicated test proves the
     endpoint's current live (broken-but-non-leaking) behavior.

  4. app/services/mail_core.py::send_email -- the shared low-level SMTP
     sender used by ~10 different notification-generation call sites across
     the codebase (mail_feedback.py, mail_performance_sender.py, etc.)
     returned ``(False, str(exc))`` on any SMTP failure. Confirmed reachable
     to a REAL end user (a manager, not an admin): a manager updating a
     feedback request's response triggers send_feedback_response_mail ->
     send_email, and app/performance/engagement_feedback_routes.py (a web
     route file, out of this agent's scope to edit) does
     ``flash(f"...e-posta gonderilemedi: {message}", ...)`` -- directly
     interpolating this raw exception text into a flash banner. Fixed at the
     shared root: send_email now returns a fixed safe Turkish message on SMTP
     failure (operator logging via logger.exception already existed and is
     untouched); this one fix automatically also sanitizes every other
     downstream consumer (mail_performance_sender.py's retry/dashboard
     surfaces, mail_feedback.py's failed_items, etc.) without touching those
     files individually.

  5. app/file_center/mail_service.py::send_file_center_email -- same
     ``log.error_message = str(exc)`` anti-pattern, with a code comment
     explicitly documenting the intent to show it to a user ("... icin
     kullaniciya gosterilecek kontrollu hata"). Confirmed reachable:
     app/file_center/routes.py (out of scope to edit) does
     ``flash(f"...Hata: {mail_log.error_message}", "danger")``. This one had
     NO operator logging at all before this fix -- added
     current_app.logger.exception(...) alongside the safe message.

  6. app/executive_summary/mail_engine.py::send_executive_summary_email --
     returned ``f"Gonderim hatasi: {exc}"`` in its result dict's "message".
     Reachable via POST /dashboard/yonetici-ozeti/test-mail (admin-only route,
     out of scope to edit) when called with an ``Accept: application/json``
     header, which returns the raw `result` dict verbatim as JSON. Fixed to a
     safe Turkish message; operator logging via logger.exception already
     existed and is untouched.

No JSON key names, HTTP status codes, function signatures, or DB
column/field names changed anywhere in this wave -- only the *value* of an
already-existing "message"/"error_message" string, plus two added operator
log calls where none existed before.
"""
from __future__ import annotations

import logging
import os
import tempfile
import uuid
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool

_SENTINEL = "TECHNICAL_SENTINEL_DO_NOT_SHOW_9F3A"

_TMP_DB_DIR = str(Path(tempfile.gettempdir()) / "bys360_pytest_tmp_h1f_mobile")

_PASSWORD = "H1FMobileLeakContractTest1!"
_FIRST_LOGIN_PASSWORD = "h1f-mobile-first-login-test-pw"

_user_counter = 0


# ---------------------------------------------------------------------------
# Shared Flask app / client fixtures (copied from the proven pattern used by
# tests/behavior/test_h1e_n3_mobile_api_ai_decision_display_contract.py).
# ---------------------------------------------------------------------------


def _make_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-h1f-mobile-contract")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", _FIRST_LOGIN_PASSWORD)
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER", "false")
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")

    os.makedirs(_TMP_DB_DIR, exist_ok=True)
    db_path = os.path.join(_TMP_DB_DIR, f"h1f_mobile_{uuid.uuid4().hex}.sqlite3")
    db_uri = "sqlite:///" + db_path.replace("\\", "/")
    monkeypatch.setenv("DATABASE_URL", db_uri)

    from app import create_app
    from config import Config

    monkeypatch.setattr(Config, "APP_ENV", "testing")
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", db_uri)
    monkeypatch.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
    )

    from app.extensions import db

    with flask_app.app_context():
        from sqlalchemy import event

        @event.listens_for(db.engine, "connect")
        def _disable_pysqlite_implicit_begin(dbapi_connection, connection_record):  # noqa: ARG001
            dbapi_connection.isolation_level = None

        @event.listens_for(db.engine, "begin")
        def _explicit_begin(conn):
            conn.exec_driver_sql("BEGIN")

        db.create_all()

    return flask_app


@pytest.fixture
def app(monkeypatch):
    return _make_app(monkeypatch)


@pytest.fixture
def client(app):
    return app.test_client()


def _next_suffix() -> int:
    global _user_counter
    _user_counter += 1
    return _user_counter


def _create_user(app, *, role="personel", password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    suffix = _next_suffix()
    with app.app_context():
        user = User(
            sicil_no=f"H1FMOB{suffix:06d}",
            email=f"h1f-mobile-{suffix}@bys360.test",
            ad="H1F",
            soyad=f"User{suffix}",
            role=role,
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _auth_headers(app, user_id):
    from app.api.mobile.shared import _issue_token
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None
        token = _issue_token(user)
        return {"Authorization": f"Bearer {token}"}


# ===========================================================================
# Finding 1: KPI target create + progress-update except-blocks.
# ===========================================================================


def test_kpi_target_create_commit_failure_returns_safe_message_no_class_name(app, client, monkeypatch, caplog):
    user_id = _create_user(app)
    headers = _auth_headers(app, user_id)

    from app.extensions import db

    def _raise_on_commit():
        raise Exception(_SENTINEL)

    monkeypatch.setattr(db.session, "commit", _raise_on_commit)

    with caplog.at_level(logging.ERROR):
        resp = client.post(
            "/api/mobile/kpi/target-management",
            json={"target_name": "H1F Contract Hedefi", "target_value": 100, "current_value": 10},
            headers=headers,
        )

    monkeypatch.undo()

    assert resp.status_code == 500
    body = resp.get_json()
    assert body is not None
    message = body.get("message", "")

    assert _SENTINEL not in message
    assert "Exception" not in message
    assert "Error" not in message  # no *Error class-name leak either
    assert message == "KPI hedef kartı oluşturulamadı. Lütfen bilgileri kontrol edip tekrar deneyin."

    # Operator log must still capture the real exception for diagnostics.
    assert any(
        record.exc_info and _SENTINEL in str(record.exc_info[1])
        for record in caplog.records
    )


def test_kpi_target_progress_commit_failure_returns_safe_message_no_class_name(app, client, monkeypatch, caplog):
    user_id = _create_user(app)
    headers = _auth_headers(app, user_id)

    from app.extensions import db
    from app.modules.strategic_performance.models import PerformanceTarget

    with app.app_context():
        target = PerformanceTarget(
            target_code=f"H1F-{uuid.uuid4().hex[:10]}",
            target_name="H1F Contract Progress Hedefi",
            target_type="personnel",
            target_value=100,
            current_value=0,
            completion_rate=0,
            status="ongoing",
            risk_level="low",
            owner_user_id=user_id,
            created_by=user_id,
        )
        db.session.add(target)
        db.session.commit()
        target_id = target.id

    def _raise_on_commit():
        raise Exception(_SENTINEL)

    monkeypatch.setattr(db.session, "commit", _raise_on_commit)

    with caplog.at_level(logging.ERROR):
        resp = client.post(
            f"/api/mobile/kpi/target-management/{target_id}/progress",
            json={"current_value": 55},
            headers=headers,
        )

    monkeypatch.undo()

    assert resp.status_code == 500
    body = resp.get_json()
    assert body is not None
    message = body.get("message", "")

    assert _SENTINEL not in message
    assert "Exception" not in message
    assert message == "KPI gerçekleşme değeri güncellenemedi. Lütfen tekrar deneyin."

    assert any(
        record.exc_info and _SENTINEL in str(record.exc_info[1])
        for record in caplog.records
    )


# ===========================================================================
# Finding 2: in-period note creation except-block.
# ===========================================================================


def test_in_period_note_create_db_failure_returns_safe_message_no_class_name(app, client, monkeypatch, caplog):
    user_id = _create_user(app)
    headers = _auth_headers(app, user_id)

    from app.extensions import db

    def _raise_on_commit():
        raise Exception(_SENTINEL)

    monkeypatch.setattr(db.session, "commit", _raise_on_commit)

    with caplog.at_level(logging.ERROR):
        resp = client.post(
            "/api/mobile/performance/in-period-notes/v2",
            json={"note": "H1F contract test notu", "note_type": "genel_gozlem"},
            headers=headers,
        )

    monkeypatch.undo()

    assert resp.status_code == 500
    body = resp.get_json()
    assert body is not None
    message = body.get("message", "")

    assert _SENTINEL not in message
    assert "Exception" not in message
    assert message == "Dönem içi not kaydedilemedi. Lütfen tekrar deneyin."

    assert any(
        record.exc_info and _SENTINEL in str(record.exc_info[1])
        for record in caplog.records
    )


# ===========================================================================
# Finding 3: communication v2 "warning" key leaks.
# ===========================================================================


def test_communication_v2_threads_list_failure_has_no_warning_key_or_sentinel(app, client, monkeypatch):
    """GET /api/mobile/communication/v2/threads is a live, directly-wired
    route (not affected by the broken write-delegate). Force its internal
    query to fail and prove the "warning" key (which used to carry
    str(exc)[:240]) is gone, and no exception text leaks anywhere in the body."""
    user_id = _create_user(app)
    headers = _auth_headers(app, user_id)

    import app.api.mobile.communication_v2_read_routes as read_routes_module

    class _BoomQuery:
        def join(self, *a, **kw):
            raise Exception(_SENTINEL)

    monkeypatch.setattr(read_routes_module, "MessageThread", type("MT", (), {"query": _BoomQuery()}))

    resp = client.get("/api/mobile/communication/v2/threads", headers=headers)
    monkeypatch.undo()

    assert resp.status_code == 200
    body = resp.get_json()
    assert body is not None

    assert "warning" not in body
    body_text = str(body)
    assert _SENTINEL not in body_text
    assert body["message"] == "Mesajlaşma kayıtları şu anda yüklenemedi. Sunucu logu kontrol edilmelidir."


def test_communication_v2_write_endpoints_currently_500_via_error_handler_without_leaking(app, client):
    """Documents + proves the pre-existing (unrelated) delegate-wiring bug:
    these write endpoints cannot currently reach the code this wave patched,
    because the delegate raises RuntimeError first. This is NOT a leak --
    BYS360's app-wide error handler intercepts it and renders the generic
    safe error page -- but it means the fix below is verified at the
    function level (next two tests), not via this HTTP path. Flagged for the
    coordinator as a DEAD_ORPHANED_PATH finding, out of this agent's scope
    to fix (service/route wiring, not a display-layer leak)."""
    user_id = _create_user(app)
    headers = _auth_headers(app, user_id)

    resp = client.post(
        "/api/mobile/communication/v2/create-thread",
        json={"participant_user_ids": [user_id], "body": "hi"},
        headers=headers,
    )

    assert resp.status_code == 500
    text = resp.get_data(as_text=True)
    # The generic BYS360 500 page, not the RuntimeError's own message text.
    assert "communication legacy handler not found" not in text
    assert "RuntimeError" not in text


def test_communication_v2_send_message_legacy_function_has_no_warning_key_or_sentinel(app, monkeypatch):
    """Calls the module-level legacy function directly, bypassing the broken
    delegate lookup, to prove the fix in
    app/api/mobile/domains/communication_v2_write.py is correct for when
    that separate wiring bug is resolved."""
    user_id = _create_user(app)

    import app.api.mobile.domains.communication_v2_write as write_module
    from app.core.datetime_utils import utc_now
    from app.extensions import db
    from app.models import MessageThread, MessageThreadParticipant, User

    with app.app_context():
        thread = MessageThread(thread_type="direct", subject="H1F test", is_active=True, last_message_at=utc_now(), created_by_user_id=user_id)
        db.session.add(thread)
        db.session.flush()
        db.session.add(MessageThreadParticipant(thread_id=thread.id, user_id=user_id, joined_at=utc_now(), is_archived=False))
        db.session.commit()
        thread_id = thread.id
        user = db.session.get(User, user_id)
        assert user is not None

        def _raise_on_flush():
            raise Exception(_SENTINEL)

        monkeypatch.setattr(db.session, "flush", _raise_on_flush)

        with app.test_request_context(
            f"/api/mobile/communication/v2/threads/{thread_id}/send",
            method="POST",
            json={"body": "H1F contract test message"},
        ):
            response = write_module._bys360_legacy_mobile_b48_communication_v2_send(user, thread_id)

        monkeypatch.undo()

        resp_obj, status_code = response
        assert status_code == 500
        body = resp_obj.get_json()

        assert "warning" not in body
        assert _SENTINEL not in str(body)
        assert body["message"] == "Mesaj gönderilemedi. Lütfen tekrar deneyin."


def test_communication_v2_create_thread_legacy_function_has_no_warning_key_or_sentinel(app, monkeypatch):
    user_id = _create_user(app)
    recipient_id = _create_user(app)

    import app.api.mobile.domains.communication_v2_write as write_module
    from app.extensions import db
    from app.models import User

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user is not None

        def _raise_on_flush():
            raise Exception(_SENTINEL)

        monkeypatch.setattr(db.session, "flush", _raise_on_flush)

        with app.test_request_context(
            "/api/mobile/communication/v2/create-thread",
            method="POST",
            json={"participant_user_ids": [recipient_id], "body": "H1F contract test message"},
        ):
            response = write_module._bys360_legacy_mobile_b48_communication_v2_create_thread(user)

        monkeypatch.undo()

        resp_obj, status_code = response
        assert status_code == 500
        body = resp_obj.get_json()

        assert "warning" not in body
        assert _SENTINEL not in str(body)
        assert body["message"] == "Konuşma başlatılamadı. Lütfen tekrar deneyin."


# ===========================================================================
# Finding 4: app/services/mail_core.py::send_email shared SMTP sender.
# ===========================================================================


def test_send_email_smtp_failure_returns_safe_message_and_logs_operator_detail(monkeypatch, caplog):
    import app.services.mail_core as mail_core

    monkeypatch.setattr(
        mail_core,
        "get_smtp_settings",
        lambda: {
            "host": "smtp.h1f-contract.test",
            "port": 587,
            "username": "",
            "password": "",
            "use_tls": True,
            "default_sender": "noreply@h1f-contract.test",
            "app_base_url": "http://localhost",
            "app_name": "BYS360",
            "institution_name": "H1F Test Kurumu",
        },
    )

    class _BoomSMTP:
        def __init__(self, *a, **kw):
            raise Exception(_SENTINEL)

    monkeypatch.setattr(mail_core.smtplib, "SMTP", _BoomSMTP)

    with caplog.at_level(logging.ERROR):
        ok, message = mail_core.send_email("user@h1f-contract.test", "H1F Test Subject", "H1F test body")

    assert ok is False
    assert _SENTINEL not in message
    assert message == "E-posta gönderilemedi. Sunucu logları kontrol edilmelidir."

    assert any(
        record.exc_info and _SENTINEL in str(record.exc_info[1])
        for record in caplog.records
    )


def test_send_email_message_is_never_shown_raw_by_a_downstream_flash_style_caller(monkeypatch):
    """Regression guard for the confirmed leak chain: a manager-facing route
    (app/performance/engagement_feedback_routes.py, out of scope to edit)
    interpolates send_email's returned message directly into a flash banner
    via an f-string. This proves that even a naive downstream caller doing
    exactly that can no longer surface technical detail."""
    import app.services.mail_core as mail_core

    monkeypatch.setattr(
        mail_core,
        "get_smtp_settings",
        lambda: {
            "host": "smtp.h1f-contract.test",
            "port": 587,
            "username": "",
            "password": "",
            "use_tls": True,
            "default_sender": "noreply@h1f-contract.test",
            "app_base_url": "http://localhost",
            "app_name": "BYS360",
            "institution_name": "H1F Test Kurumu",
        },
    )

    class _BoomSMTP:
        def __init__(self, *a, **kw):
            raise Exception(_SENTINEL)

    monkeypatch.setattr(mail_core.smtplib, "SMTP", _BoomSMTP)

    ok, message = mail_core.send_email("user@h1f-contract.test", "Subject", "Body")
    flashed = f"Talep güncellendi ancak e-posta gönderilemedi: {message}" if not ok else "ok"

    assert _SENTINEL not in flashed


# ===========================================================================
# Finding 5: app/file_center/mail_service.py::send_file_center_email.
# ===========================================================================


def test_send_file_center_email_smtp_failure_logs_and_returns_safe_error(app, monkeypatch, caplog):
    import app.file_center.mail_service as mail_service

    class _BoomSMTP:
        def __init__(self, *a, **kw):
            raise Exception(_SENTINEL)

    monkeypatch.setattr(mail_service.smtplib, "SMTP", _BoomSMTP)
    monkeypatch.setenv("FILE_CENTER_MAIL_ENABLED", "true")
    monkeypatch.setenv("FILE_CENTER_SMTP_HOST", "smtp.h1f-contract.test")
    monkeypatch.setenv("FILE_CENTER_MAIL_FROM", "noreply@h1f-contract.test")

    with app.app_context():
        with caplog.at_level(logging.ERROR):
            log = mail_service.send_file_center_email(
                recipient_email="user@h1f-contract.test",
                subject="H1F Test",
                body="H1F test body",
                purpose="manual_reminder",
            )

        assert log.status == "failed"
        assert _SENTINEL not in (log.error_message or "")
        assert log.error_message == "E-posta gönderilemedi. Sunucu logları kontrol edilmelidir."

        # This except-block had NO operator logging at all before this fix.
        assert any(
            record.exc_info and _SENTINEL in str(record.exc_info[1])
            for record in caplog.records
        )


# ===========================================================================
# Finding 6: app/executive_summary/mail_engine.py::send_executive_summary_email.
# ===========================================================================


def test_send_executive_summary_email_smtp_failure_returns_safe_message(monkeypatch, caplog):
    import app.executive_summary.mail_engine as mail_engine

    fixed_payload = {
        "generated_date": "04.09.2026",
        "generated_at": "04.09.2026 09:00",
        "executive_note": "H1F contract test note.",
        "weather": {
            "location": "Çanakkale",
            "status": "Açık",
            "temperature": "20C",
            "humidity": "%50",
            "wind": "10 km/h",
            "rain": "%0",
        },
        "metrics": {
            "pending_feedback": 0,
            "open_support": 0,
            "pending_performance_tasks": 0,
            "pending_approvals": 0,
            "active_surveys": 0,
        },
    }
    monkeypatch.setattr(mail_engine, "build_executive_summary_payload", lambda report_type: fixed_payload)
    monkeypatch.setattr(mail_engine, "get_default_recipients", lambda: ["ops@h1f-contract.test"])
    monkeypatch.setenv("MAIL_SERVER", "smtp.h1f-contract.test")
    monkeypatch.setenv("MAIL_DEFAULT_SENDER", "noreply@h1f-contract.test")
    os.makedirs(_TMP_DB_DIR, exist_ok=True)
    monkeypatch.setenv("BYS360_LOG_DIR", _TMP_DB_DIR)

    class _BoomSMTP:
        def __init__(self, *a, **kw):
            raise Exception(_SENTINEL)

    monkeypatch.setattr(mail_engine.smtplib, "SMTP", _BoomSMTP)

    with caplog.at_level(logging.ERROR):
        result = mail_engine.send_executive_summary_email(report_type="morning", manual=True)

    assert result["ok"] is False
    assert _SENTINEL not in result["message"]
    assert result["message"] == "Gönderim hatası: e-posta sunucusuna ulaşılamadı. Sistem loglarını kontrol edin."

    assert any(
        record.exc_info and _SENTINEL in str(record.exc_info[1])
        for record in caplog.records
    )
