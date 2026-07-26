from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.services.performance import (
    process_engine_phase6_president_approvals as approvals,
)

# BYS360 Phase 5 exception-debt wave 3: `decide_president_approval` had no
# try/except at all around its writes + final commit(). Any SQLAlchemyError
# propagated uncaught; the only safety net was the global Flask
# `teardown_request` guard in app/bootstrap/operational_guards.py, which
# rolls back but returns no domain result, no flash message, and no
# Phase6ActionResult -- diverging from the sibling functions in this same
# file (`delete_president_approval_record`, `_display_user_name`) that
# already catch SQLAlchemyError, rollback, log, and return a friendly
# failure result. These tests pin down: (1) the pre-existing successful
# behavior is unchanged, (2) a commit failure now rolls back exactly once
# and returns a domain failure result instead of propagating, and (3) a
# genuine programming error is NOT swallowed by the new narrow handler.


class _FakeMappingResult:
    def __init__(self, row: dict | None) -> None:
        self._row = row

    def mappings(self) -> _FakeMappingResult:
        return self

    def first(self) -> dict | None:
        return self._row


def test_decide_president_approval_success_updates_decision_and_commits_once(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    approval_id = 55
    row = {"id": approval_id, "flow_id": 900, "evaluation_id": 12, "status": "pending"}

    monkeypatch.setattr(approvals, "can_view_president_approvals", lambda actor: True)
    monkeypatch.setattr(approvals.db.session, "execute", lambda *a, **k: _FakeMappingResult(row))
    monkeypatch.setattr(approvals, "table_exists", lambda name: True)
    monkeypatch.setattr(
        approvals,
        "_table_columns",
        lambda name: {
            "current_status", "current_stage", "current_owner_user_id",
            "current_owner_name", "last_action_title", "last_action_at",
            "president_approval_status", "flow_summary", "process_version",
            "updated_by_engine_at",
        },
    )

    insert_calls: list[dict] = []
    monkeypatch.setattr(
        approvals, "_insert_step_for_decision", lambda **kwargs: insert_calls.append(kwargs)
    )

    commit_calls: list[bool] = []
    monkeypatch.setattr(approvals.db.session, "commit", lambda: commit_calls.append(True))
    rollback_calls: list[bool] = []
    monkeypatch.setattr(approvals.db.session, "rollback", lambda: rollback_calls.append(True))

    actor = SimpleNamespace(id=101)

    with app.app_context():
        result = approvals.decide_president_approval(
            approval_id, actor, "approved", note="Onaylandı, teşekkürler"
        )

    assert result.ok is True
    assert result.message == "Başkan onayı kaydedildi."
    assert result.approval_id == approval_id
    assert commit_calls == [True]
    assert rollback_calls == []
    assert insert_calls == [
        {
            "approval_id": approval_id,
            "flow_id": 900,
            "evaluation_id": 12,
            "actor": actor,
            "action": "approved",
            "note": "Onaylandı, teşekkürler",
        }
    ]


def test_decide_president_approval_return_action_success_message(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    approval_id = 56
    row = {"id": approval_id, "flow_id": None, "evaluation_id": None, "status": "pending"}

    monkeypatch.setattr(approvals, "can_view_president_approvals", lambda actor: True)
    monkeypatch.setattr(approvals.db.session, "execute", lambda *a, **k: _FakeMappingResult(row))
    monkeypatch.setattr(approvals, "_insert_step_for_decision", lambda **kwargs: None)
    monkeypatch.setattr(approvals.db.session, "commit", lambda: None)

    actor = SimpleNamespace(id=101)
    with app.app_context():
        result = approvals.decide_president_approval(approval_id, actor, "returned", note="İade")

    assert result.ok is True
    assert result.message == "Süreç iade edildi."


def test_decide_president_approval_rejects_unauthorized_actor_without_touching_db(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_if_called(*_a, **_k):
        raise AssertionError("db.session.execute should not be called for an unauthorized actor")

    monkeypatch.setattr(approvals, "can_view_president_approvals", lambda actor: False)
    monkeypatch.setattr(approvals.db.session, "execute", fail_if_called)

    with app.app_context():
        result = approvals.decide_president_approval(1, SimpleNamespace(id=1), "approved")

    assert result.ok is False
    assert result.message == "Bu işlem için Başkan veya yetkili yönetici rolü gerekir."


def test_decide_president_approval_rolls_back_and_returns_failure_on_commit_error(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    approval_id = 61
    row = {"id": approval_id, "flow_id": None, "evaluation_id": None, "status": "pending"}

    monkeypatch.setattr(approvals, "can_view_president_approvals", lambda actor: True)
    monkeypatch.setattr(approvals.db.session, "execute", lambda *a, **k: _FakeMappingResult(row))
    monkeypatch.setattr(approvals, "_insert_step_for_decision", lambda **kwargs: None)

    def raise_commit():
        raise SQLAlchemyError("simulated commit failure - internal detail")

    monkeypatch.setattr(approvals.db.session, "commit", raise_commit)

    rollback_calls: list[bool] = []
    monkeypatch.setattr(approvals.db.session, "rollback", lambda: rollback_calls.append(True))

    log_calls: list[str] = []
    monkeypatch.setattr(
        approvals.logger, "exception", lambda msg, *a, **k: log_calls.append(msg)
    )

    actor = SimpleNamespace(id=5)
    with app.app_context():
        result = approvals.decide_president_approval(approval_id, actor, "approved", note="x")

    # Rollback exactly once; no false success; no leaked exception internals;
    # a single log record for the failure.
    assert rollback_calls == [True]
    assert result.ok is False
    assert result.approval_id == approval_id
    assert "simulated commit failure" not in result.message
    assert "internal detail" not in result.message
    assert len(log_calls) == 1


def test_decide_president_approval_does_not_swallow_unexpected_runtime_error(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    approval_id = 71
    row = {"id": approval_id, "flow_id": None, "evaluation_id": None, "status": "pending"}

    monkeypatch.setattr(approvals, "can_view_president_approvals", lambda actor: True)
    monkeypatch.setattr(approvals.db.session, "execute", lambda *a, **k: _FakeMappingResult(row))

    def explode(**_kwargs):
        raise RuntimeError("unexpected programming failure")

    monkeypatch.setattr(approvals, "_insert_step_for_decision", explode)

    rollback_calls: list[bool] = []
    monkeypatch.setattr(approvals.db.session, "rollback", lambda: rollback_calls.append(True))

    actor = SimpleNamespace(id=9)
    with app.app_context(), pytest.raises(RuntimeError):
        approvals.decide_president_approval(approval_id, actor, "approved", note=None)

    # The narrow `except SQLAlchemyError` must not catch this. Cleanup for a
    # genuine programming error is intentionally left to the application-level
    # `teardown_request` guard (app/bootstrap/operational_guards.py), which is
    # the layer that already owns rollback-on-unhandled-exception for every
    # request in this app -- not this service function.
    assert rollback_calls == []
