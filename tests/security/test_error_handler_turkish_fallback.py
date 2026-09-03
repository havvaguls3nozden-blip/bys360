"""BYS360 generic HTTPException fallback -- Turkish-only user message contract (H1).

Root cause (verified empirically against a real Flask app + test client, not
just read from source): `app/error_handlers.py`'s `render_error_page` renders
`errors/<status_code>.html` when that template exists (400/401/403/404/405/
413/429/500/503 all have one and are already fully Turkish, hardcoded --
those templates do not even interpolate the `title`/`message` arguments).
For any other HTTP status code with no dedicated template (e.g. 409, 422),
`render_template` raises `TemplateNotFound` and `render_error_page` falls
back to an inline HTML snippet that DOES interpolate `title`/`message`
directly. Before this fix, `handle_http_exception` (the generic
`@app.errorhandler(HTTPException)` catch-all) passed Werkzeug's own
`error.name`/`error.description` into that fallback -- which are raw English
by default (e.g. "Conflict" / "A conflict happened while processing the
request..."). No production code currently raises such a code (confirmed:
`app/` only ever calls `abort(401|403|404|503)`, all of which have dedicated
Turkish handling), so this was a *latent* leak, not an actively-triggered
one -- but it is real and reproducible the moment any future `abort(422)` or
similar is added anywhere in the codebase, or a third-party library raises
an uncommon `HTTPException` subclass.

This file registers `app.error_handlers.register_error_handlers` on its own
small, throwaway Flask app -- deliberately NOT the shared, session-scoped
`app` fixture from `tests/conftest.py`. That fixture is reused by thousands
of other tests across the full suite; once any of them causes it to handle
its first request, Flask permanently forbids registering new routes on it
("The setup method 'route' can no longer be called..."), which makes
lazy per-test probe-route registration order-dependent and unsafe outside
of a single isolated file. A dedicated minimal app avoids that entirely and
is also faster and more clearly scoped to the unit under test.

Writes NOTHING to any production source file.
"""
from __future__ import annotations

import logging

import pytest
from flask import Flask, abort

from app.error_handlers import register_error_handlers

_TEMPLATES_DIR = "app/templates"

# Werkzeug's real default English text for these codes -- used as a negative
# assertion (must NEVER appear in the response body).
_RAW_ENGLISH_409 = "conflict happened while processing"
_RAW_ENGLISH_422 = "well-formed but was unable to be followed"


@pytest.fixture()
def probe_app():
    app = Flask(__name__, template_folder=_TEMPLATES_DIR)
    app.config.update(TESTING=True, SECRET_KEY="test-only-error-handler-probe-app")
    register_error_handlers(app)

    @app.route("/probe-409")
    def _probe_409():
        abort(409)

    @app.route("/probe-422")
    def _probe_422():
        abort(422)

    return app


@pytest.fixture()
def probe_client(probe_app):
    return probe_app.test_client()


# ---------------------------------------------------------------------------
# Negative regression: codes with no dedicated errors/<code>.html template
# must show a safe, generic Turkish message -- never Werkzeug's raw English.
# ---------------------------------------------------------------------------


def test_untemplated_409_shows_safe_turkish_message_not_raw_english(probe_client) -> None:
    response = probe_client.get("/probe-409")
    body = response.get_data(as_text=True)

    assert response.status_code == 409, "Status code must be preserved unchanged."
    assert _RAW_ENGLISH_409 not in body.lower(), (
        f"Raw Werkzeug English leaked to the user: {body!r}"
    )
    assert "İşlem Tamamlanamadı" in body
    assert "İsteğiniz işlenirken bir sorun oluştu" in body


def test_untemplated_422_shows_safe_turkish_message_not_raw_english(probe_client) -> None:
    """Proves the fix is a general fallback, not a one-off special case for 409."""
    response = probe_client.get("/probe-422")
    body = response.get_data(as_text=True)

    assert response.status_code == 422, "Status code must be preserved unchanged."
    assert _RAW_ENGLISH_422 not in body.lower(), (
        f"Raw Werkzeug English leaked to the user: {body!r}"
    )
    assert "İşlem Tamamlanamadı" in body


# ---------------------------------------------------------------------------
# Positive regression: codes that already had a dedicated Turkish template
# (401/403/404/...) must render exactly as before -- this fix must not touch
# their content, since those templates never used the generic handler's
# title/message arguments in the first place.
# ---------------------------------------------------------------------------


def test_404_dedicated_template_unaffected(probe_client) -> None:
    response = probe_client.get("/this-route-does-not-exist-404-probe")
    body = response.get_data(as_text=True)

    assert response.status_code == 404
    assert "İstediğiniz sayfa sistemde bulunamadı" in body, (
        "404 must keep using its own dedicated errors/404.html content."
    )
    assert "İşlem Tamamlanamadı" not in body, (
        "404 must not fall through to the generic untemplated-code fallback text."
    )


# ---------------------------------------------------------------------------
# Operator visibility: the real Werkzeug exception name/detail must still
# reach the existing safe log channel unchanged, even though the user-facing
# text is now always Turkish.
# ---------------------------------------------------------------------------


def test_operator_log_still_contains_real_exception_detail(probe_client, caplog) -> None:
    with caplog.at_level(logging.WARNING):
        response = probe_client.get("/probe-409")
    assert response.status_code == 409

    matching = [r for r in caplog.records if "HTTP hata yakalandi" in r.getMessage()]
    assert matching, "Expected an operator warning log line for the 409 probe."
    combined = " ".join(r.getMessage() for r in matching)
    assert "kod=409" in combined
    assert "Conflict" in combined, (
        "Operator log must still carry the real Werkzeug exception name "
        "even though the user-facing page is now a safe Turkish fallback."
    )
