"""BYS360 H1E-N -- final fresh residual audit found ONE more genuine
USER_VISIBLE_RAW_MACHINE_VALUE leak after the N1/N2/N3 sub-waves and the
coordinator's own risk.py/admin_dashboard.html/team_compare_service.py/
5-sibling-shape fixes had already landed.

app/templates/performance_feedback_request.html's "Talep ozeti" (request
summary) sidebar showed the employee's own PerformanceEvaluation.status
via the plain cosmetic `{{ evaluation.status|replace('_', ' ')|title }}`
chain -- the exact anti-pattern this whole H1E initiative targets. Any
future/unmapped PerformanceEvaluation.status value would render as a
title-cased but still machine-shaped string (e.g. an English slug) to a
real employee submitting a feedback request, instead of a safe Turkish
label.

This is the SAME PerformanceEvaluation.status field/vocabulary that
H1E-I already fixed in performance_reports_print.html via the
`phase5_4_status_label` Jinja filter (registered globally by
phase5_4_register_filters() in app/template_safety.py, called from
create_app() -- confirmed available on every real app instance, not
just this one template). The fix here only swaps the filter chain to
reuse that existing, already-safe, already-extensively-tested function
-- no new dict, no new helper.

Rather than re-building this route's full dependency graph (period,
employee, three-level manager chain) just to prove one filter swap, this
test renders the EXACT Jinja expression now used in the template
(`evaluation.status|phase5_4_status_label`) through the real app's
Jinja environment -- the same registration path a real request uses --
against a lightweight stand-in evaluation object. This proves the
template's actual runtime behavior for known and unmapped values without
needing to fabricate an authenticated three-manager feedback chain.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

_TEST_DB_ROOT = Path(__file__).resolve().parents[2] / "tests" / "_tmp_dbs" / "h1e_n_feedback_request_status_label"


def _make_app(monkeypatch):
    _TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_ROOT / f"{uuid.uuid4().hex}.sqlite3"

    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-h1e-n-feedback-request-status-contract")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "h1e-n-feedback-request-status-first-login-test-pw")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + db_path.as_posix())
    monkeypatch.setenv("MAIL_SUPPRESS_SEND", "true")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")
    monkeypatch.setenv("LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER", "false")

    from app import create_app
    from config import Config

    monkeypatch.setattr(Config, "APP_ENV", "testing")
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///" + db_path.as_posix())
    monkeypatch.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI="sqlite:///" + db_path.as_posix())
    return app


def test_template_source_no_longer_uses_raw_cosmetic_filter_chain() -> None:
    project_root = Path(__file__).resolve().parents[2]
    source = (project_root / "app" / "templates" / "performance_feedback_request.html").read_text(encoding="utf-8")
    assert "evaluation.status|replace('_', ' ')|title" not in source
    assert "evaluation.status|phase5_4_status_label" in source


def test_evaluation_status_fragment_known_value_shows_turkish_label(monkeypatch) -> None:
    app = _make_app(monkeypatch)
    evaluation = SimpleNamespace(status="bekliyor")
    with app.app_context():
        template = app.jinja_env.from_string("{{ evaluation.status|phase5_4_status_label }}")
        rendered = template.render(evaluation=evaluation).strip()
    assert rendered == "Bekliyor"


def test_evaluation_status_fragment_unmapped_future_value_never_leaks_raw(monkeypatch) -> None:
    app = _make_app(monkeypatch)
    unmapped = "future_evaluation_status_v9"
    evaluation = SimpleNamespace(status=unmapped)
    with app.app_context():
        template = app.jinja_env.from_string("{{ evaluation.status|phase5_4_status_label }}")
        rendered = template.render(evaluation=evaluation).strip()
    assert unmapped not in rendered
    assert rendered == "-"
    # The stored value itself is never touched by rendering.
    assert evaluation.status == unmapped


def test_evaluation_status_fragment_second_known_value(monkeypatch) -> None:
    app = _make_app(monkeypatch)
    evaluation = SimpleNamespace(status="tamamlandi")
    with app.app_context():
        template = app.jinja_env.from_string("{{ evaluation.status|phase5_4_status_label }}")
        rendered = template.render(evaluation=evaluation).strip()
    assert rendered == "Tamamlandı"
