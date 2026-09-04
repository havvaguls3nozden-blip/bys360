"""BYS360 H1F -- final fresh residual audit (coordinator-level, post all
H1F-A/B/C waves).

A repo-wide re-scan for str(exc)/f"...{exc}" outside the files any of the
3 H1F agents already touched found a whole family of AI Decision Support
JSON-API endpoints (app/ai/routes.py's shared `_run_json_service()` and
the near-identical `_run_faz3_json()` .. `_run_faz9_json()` helpers in
app/ai/decision_support_faz3_routes.py through faz9_routes.py) that
share one dispatcher pattern:

    except PermissionError as exc:
        ...
        return jsonify({"ok": False, "error": str(exc) or "<safe default>"}), 403
    except LookupError as exc:
        ...
        return jsonify({"ok": False, "error": str(exc) or "Kayit bulunamadi."}), 404
    except ValueError as exc:
        ...
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        ...
        return jsonify({"ok": False, "error": f"...: {exc}"}), 500

The generic `except Exception` branch is an unambiguous leak (it catches
anything -- a SQLAlchemy error, an AttributeError, a TypeError -- and
echoes it raw). The bare `LookupError`/`ValueError`/`PermissionError`
branches are subtler: repo-wide grep confirms NOTHING in
app/services/ai_decision/** or app/services/ai/** ever does
`raise ValueError(...)` or `raise LookupError(...)` with hand-authored
text -- the only intentionally-raised, safe-by-construction exceptions
in this call path are the four custom subclasses already isolated by
their own, earlier except clauses (AIServiceDisabled, AIAccessDenied,
AIResourceNotFound, AIInputError -- and AIDecisionPermissionDenied, a
PermissionError subclass, in the faz3-9 files). That means a bare
ValueError/LookupError/PermissionError reaching these fallback branches
can only be an organic, unplanned exception (a bug, an edge case) --
exactly the raw-technical-detail case Section 21 of the H1F brief
prohibits -- so their str(exc) was replaced with a fixed safe message
too, while the four custom-exception branches (whose raise sites were
individually verified to carry only hardcoded Turkish text) are left
showing str(exc) unchanged, preserving their genuinely useful detail.

Also fixed in the same pass: three "kalite kapisi" (quality gate)
service functions structurally identical to the five app/services/
performance/v2_1_2..6_*_gate.py functions H1F-B already closed, but
using different filenames that this agent's own grep sweep did not
happen to match: v2_1_7_period_management_center_gate.py,
v2_1_8_period_center_assignment_launch_gate.py, and v2_1_quality_gate.py
(the pre-existing v2.1.1 gate). Each appended a raw exception string
into an admin-facing quality-gate checks list/schema dict.

Writes NOTHING to any production source file.
"""
from __future__ import annotations

import logging

import pytest

_SENTINEL = "TECHNICAL_SENTINEL_DO_NOT_SHOW_9F3A"


def _raise_sentinel(*_args, **_kwargs):
    raise Exception(_SENTINEL)  # noqa: TRY002 - deliberately generic


def _raise_sentinel_value_error(*_args, **_kwargs):
    raise ValueError(_SENTINEL)


def _raise_sentinel_lookup_error(*_args, **_kwargs):
    raise LookupError(_SENTINEL)


def _raise_sentinel_permission_error(*_args, **_kwargs):
    raise PermissionError(_SENTINEL)


@pytest.fixture
def app():
    from app import create_app

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app


# ---------------------------------------------------------------------------
# app/ai/routes.py -- _run_json_service
# ---------------------------------------------------------------------------


def test_run_json_service_generic_exception_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.routes as ai_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger="app.ai.routes"):
        body, status = ai_routes._run_json_service(_raise_sentinel)

    assert status == 500
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "AI işleminde beklenmeyen bir hata oluştu."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_run_json_service_bare_value_error_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.routes as ai_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger="app.ai.routes"):
        body, status = ai_routes._run_json_service(_raise_sentinel_value_error)

    assert status == 400
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "Geçersiz istek parametresi."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_run_json_service_ai_input_error_still_shows_its_own_safe_message(app) -> None:
    import app.ai.routes as ai_routes
    from app.services.ai.guardrails import AIInputError

    def _raise_ai_input_error(*_a, **_k):
        raise AIInputError("Tanımsız AI özelliği.")

    with app.test_request_context("/"):
        body, status = ai_routes._run_json_service(_raise_ai_input_error)

    assert status == 400
    assert body.get_json()["error"] == "Tanımsız AI özelliği."


def test_run_json_service_bare_lookup_error_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.routes as ai_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger="app.ai.routes"):
        body, status = ai_routes._run_json_service(_raise_sentinel_lookup_error)

    assert status == 404
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "Kayıt bulunamadı."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_run_json_service_bare_permission_error_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.routes as ai_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger="app.ai.routes"):
        body, status = ai_routes._run_json_service(_raise_sentinel_permission_error)

    assert status == 403
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "Bu işlem için yetkiniz bulunmamaktadır."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


# ---------------------------------------------------------------------------
# app/ai/decision_support_faz5_routes.py -- _run_faz5_json (representative
# of the identical faz3/faz4/faz6/faz7/faz8/faz9 shape).
# ---------------------------------------------------------------------------


_FAZ5_LOGGER = "app.ai.decision_support_faz5_routes"


def test_run_faz5_json_generic_exception_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.decision_support_faz5_routes as faz5_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger=_FAZ5_LOGGER):
        body, status = faz5_routes._run_faz5_json(_raise_sentinel)

    assert status == 500
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "Karne karar destek kontrolünde beklenmeyen bir hata oluştu."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_run_faz5_json_bare_value_error_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.decision_support_faz5_routes as faz5_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger=_FAZ5_LOGGER):
        body, status = faz5_routes._run_faz5_json(_raise_sentinel_value_error)

    assert status == 400
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "Geçersiz istek parametresi."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_run_faz5_json_bare_lookup_error_never_leaks_raw_text(app, caplog) -> None:
    import app.ai.decision_support_faz5_routes as faz5_routes

    with app.test_request_context("/"), caplog.at_level(logging.ERROR, logger=_FAZ5_LOGGER):
        body, status = faz5_routes._run_faz5_json(_raise_sentinel_lookup_error)

    assert status == 404
    assert _SENTINEL not in body.get_json()["error"]
    assert body.get_json()["error"] == "Kayıt bulunamadı."
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_run_faz5_json_permission_denied_still_shows_its_own_safe_message(app) -> None:
    import app.ai.decision_support_faz5_routes as faz5_routes
    from app.services.ai_decision.permission_guard import AIDecisionPermissionDenied

    def _raise_denied(*_a, **_k):
        raise AIDecisionPermissionDenied("Bu performans karar destek kaydına erişim yetkiniz bulunmamaktadır.")

    with app.test_request_context("/"):
        body, status = faz5_routes._run_faz5_json(_raise_denied)

    assert status == 403
    assert body.get_json()["error"] == "Bu performans karar destek kaydına erişim yetkiniz bulunmamaktadır."


# ---------------------------------------------------------------------------
# Source-level regression guard for the other 6 structurally-identical
# faz files (faz3, faz4, faz6, faz7, faz8, faz9) -- a full behavioral
# test per file would only re-exercise the exact same fix already proven
# above for faz5; this locks in that none of them regressed back to the
# f"...: {exc}" / bare str(exc) shape.
# ---------------------------------------------------------------------------


def test_remaining_faz_files_no_longer_use_raw_exception_interpolation() -> None:
    import pathlib

    project_root = pathlib.Path(__file__).resolve().parents[2]
    for faz in ("faz3", "faz4", "faz6", "faz7", "faz8", "faz9"):
        source = (project_root / "app" / "ai" / f"decision_support_{faz}_routes.py").read_text(encoding="utf-8")
        assert "{exc}" not in source, f"{faz}: raw f-string exception interpolation found"
        assert '"error": str(exc)}), 400' not in source, f"{faz}: bare ValueError still echoes raw text"
        assert '"error": str(exc) or "Kayıt bulunamadı."' not in source, f"{faz}: bare LookupError still echoes raw text"


# ---------------------------------------------------------------------------
# Quality-gate siblings the H1F-B wave's grep sweep missed: v2_1_7, v2_1_8,
# and the pre-existing v2_1_1 gate (v2_1_quality_gate.py).
# ---------------------------------------------------------------------------


def test_v2_1_7_period_management_center_gate_exception_is_sanitized(monkeypatch, caplog) -> None:
    import app.services.performance.v2_1_7_period_management_center_gate as gate_mod

    monkeypatch.setattr(gate_mod, "_db", _raise_sentinel)

    with caplog.at_level(logging.ERROR, logger="app.services.performance.v2_1_7_period_management_center_gate"):
        result = gate_mod.run_v2_1_7_period_management_center_gate()

    assert result["ok"] is False
    assert _SENTINEL not in str(result)
    exception_checks = [c for c in result["checks"] if c["name"] == "exception"]
    assert exception_checks and "beklenmeyen bir hata oluştu" in exception_checks[0]["message"]
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_v2_1_8_period_center_assignment_launch_gate_exception_is_sanitized(monkeypatch, caplog) -> None:
    import app.services.performance.v2_1_8_period_center_assignment_launch_gate as gate_mod

    monkeypatch.setattr(gate_mod, "_db", _raise_sentinel)

    with caplog.at_level(logging.ERROR, logger="app.services.performance.v2_1_8_period_center_assignment_launch_gate"):
        result = gate_mod.run_v2_1_8_period_center_assignment_launch_gate()

    assert result["ok"] is False
    assert _SENTINEL not in str(result)
    exception_checks = [c for c in result["checks"] if c["name"] == "exception"]
    assert exception_checks and "beklenmeyen bir hata oluştu" in exception_checks[0]["message"]
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)


def test_v2_1_1_quality_gate_exception_is_sanitized(monkeypatch, caplog) -> None:
    import app.services.performance.v2_1_quality_gate as gate_mod
    import app.services.performance.v2_1_rule_engine as rule_engine_mod

    monkeypatch.setattr(rule_engine_mod, "build_rule_snapshot_dict", _raise_sentinel)

    with caplog.at_level(logging.ERROR, logger="app.services.performance.v2_1_quality_gate"):
        result = gate_mod.run_v2_1_1_quality_gate()

    assert result["ok"] is False
    assert _SENTINEL not in str(result)
    rule_engine_checks = [c for c in result["checks"] if c["name"] == "rule_engine_import"]
    assert rule_engine_checks and "beklenmeyen bir hata oluştu" in rule_engine_checks[0]["message"]
    assert any(r.exc_info and _SENTINEL in str(r.exc_info[1]) for r in caplog.records)
