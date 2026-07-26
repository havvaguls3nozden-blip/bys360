from __future__ import annotations

import logging

import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError

from app.services.performance import (
    process_engine_phase6_president_approvals as approvals,
    v2_1_rule_engine as engine,
)

# BYS360 Phase 5 exception-debt wave 2: targeted coverage for the broad
# `except Exception` -> narrow-type conversions made in
# app/services/performance/v2_1_rule_engine.py and
# app/services/performance/process_engine_phase6_president_approvals.py.
# These tests assert the *narrowed* behavior is unchanged for the real
# failure modes each handler was written for, AND that an exception type
# outside that narrowed set is no longer silently swallowed.


class _FakeMappingResult:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def mappings(self) -> _FakeMappingResult:
        return self

    def first(self) -> dict | None:
        return self._row


# ---------------------------------------------------------------------------
# process_engine_phase6_president_approvals.py — transaction / rollback wave
# ---------------------------------------------------------------------------


def test_display_user_name_rolls_back_and_falls_back_on_sqlalchemy_error(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(approvals, "table_exists", lambda name: True)

    def raise_execute(*_args, **_kwargs):
        raise SQLAlchemyError("simulated db failure")

    monkeypatch.setattr(approvals.db.session, "execute", raise_execute)

    rollback_calls: list[bool] = []
    monkeypatch.setattr(approvals.db.session, "rollback", lambda: rollback_calls.append(True))

    log_calls: list[str] = []
    monkeypatch.setattr(
        approvals.logger, "exception", lambda msg, *a, **k: log_calls.append(msg)
    )

    with app.app_context():
        result = approvals._display_user_name(42)

    assert result == "Kullanıcı #42"
    assert rollback_calls == [True]
    assert len(log_calls) == 1


def test_delete_president_approval_record_rolls_back_and_returns_failure_on_commit_error(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    approval_id = 7
    monkeypatch.setattr(approvals, "can_delete_president_approval_records", lambda actor: True)
    monkeypatch.setattr(approvals, "table_exists", lambda name: name == "performance_president_approvals")

    row = {
        "id": approval_id,
        "flow_id": None,
        "evaluation_id": None,
        "employee_id": None,
        "status": "pending",
        "decision_status": "pending",
    }
    monkeypatch.setattr(
        approvals.db.session, "execute", lambda *a, **k: _FakeMappingResult(row)
    )

    def raise_commit():
        raise SQLAlchemyError("simulated commit failure")

    monkeypatch.setattr(approvals.db.session, "commit", raise_commit)

    rollback_calls: list[bool] = []
    monkeypatch.setattr(approvals.db.session, "rollback", lambda: rollback_calls.append(True))

    with app.app_context():
        result = approvals.delete_president_approval_record(approval_id, actor=object())

    # Rollback must run exactly once, and the function must report failure --
    # never a false success -- when the commit itself fails.
    assert rollback_calls == [True]
    assert result.ok is False
    assert "silinemedi" in result.message.lower()
    assert result.approval_id == approval_id


# ---------------------------------------------------------------------------
# v2_1_rule_engine.py — SQLAlchemy boundary (Wave 1) + calculation (Wave 3)
# ---------------------------------------------------------------------------


def test_has_module_settings_table_returns_false_on_sqlalchemy_error(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    def raise_inspect(*_args, **_kwargs):
        raise SQLAlchemyError("simulated inspection failure")

    # `_has_module_settings_table` does `from sqlalchemy import inspect` at
    # call time, so patching the attribute on the `sqlalchemy` module itself
    # (rather than a local reference) is what actually takes effect here.
    monkeypatch.setattr(sqlalchemy, "inspect", raise_inspect)

    with app.app_context():
        assert engine._has_module_settings_table() is False


def test_get_setting_float_recovers_from_invalid_default_and_raw_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine, "_has_module_settings_table", lambda: False)

    result = engine.get_setting_float("some_key", default="not-a-number")  # type: ignore[arg-type]

    assert result == 0.0


def test_get_setting_float_does_not_swallow_unexpected_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine, "_has_module_settings_table", lambda: False)

    class ExplodesOnFloat:
        def __float__(self) -> float:
            raise RuntimeError("boom - not a value/type error")

    # Before narrowing, this RuntimeError would have been silently caught by
    # `except Exception` and turned into a 0.0 fallback. After narrowing to
    # (TypeError, ValueError), it must propagate untouched.
    with pytest.raises(RuntimeError):
        engine.get_setting_float("some_key", default=ExplodesOnFloat())  # type: ignore[arg-type]


def test_normalize_raw_score_returns_none_for_invalid_value() -> None:
    assert engine.normalize_raw_score("not-a-number") is None
    assert engine.normalize_raw_score(None) is None
    assert engine.normalize_raw_score("4") == 4


def test_is_low_score_handles_non_numeric_score_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(engine, "get_setting_float", lambda *a, **k: 70.0)

    assert engine.is_low_score([1, 2, 3]) is False
    assert engine.is_low_score(65) is True
    assert engine.is_low_score(75) is False


def test_evaluation_final_score_skips_unparseable_attr_and_uses_next(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeEvaluation:
        final_total_100 = "not-a-number"
        final_score = 82.5

    with caplog.at_level(logging.ERROR, logger=engine.logger.name):
        assert engine.evaluation_final_score(FakeEvaluation()) == 82.5


def test_evaluation_final_score_returns_zero_when_all_attrs_unparseable() -> None:
    class FakeEvaluation:
        final_total_100 = "bad"
        final_score = "bad"
        score_100 = "bad"
        total_score = "bad"

    assert engine.evaluation_final_score(FakeEvaluation()) == 0.0
