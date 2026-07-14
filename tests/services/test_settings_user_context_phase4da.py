from __future__ import annotations

import importlib
import logging
from types import SimpleNamespace

import app.services.settings.effective_menu_parts.user_context as target


class _Field:
    def __eq__(self, other):
        return ("eq", other)

    def desc(self):
        return ("desc",)


class _Query:
    def __init__(
        self,
        surveys,
        *,
        fail_filter=False,
    ):
        self.surveys = list(surveys)
        self.fail_filter = fail_filter
        self.calls = []

    def filter(self, *args):
        self.calls.append(("filter", args))

        if self.fail_filter:
            raise RuntimeError("query failure")

        return self

    def order_by(self, *args):
        self.calls.append(("order_by", args))
        return self

    def limit(self, value):
        self.calls.append(("limit", value))
        return self

    def all(self):
        self.calls.append(("all", None))
        return list(self.surveys)


class _Assignments:
    def __init__(self, rows):
        self.rows = list(rows)

    def all(self):
        return list(self.rows)


class _BrokenAssignments:
    def all(self):
        raise RuntimeError("assignment failure")


class _FakeLogger:
    def __init__(self):
        self.messages = []

    def exception(self, message):
        self.messages.append(message)


def _install_survey(
    monkeypatch,
    surveys,
    *,
    fail_filter=False,
):
    models = importlib.import_module(
        "app.models"
    )

    query = _Query(
        surveys,
        fail_filter=fail_filter,
    )

    class Survey:
        status = _Field()
        id = _Field()

    Survey.query = query

    monkeypatch.setattr(
        models,
        "Survey",
        Survey,
    )

    return query


def _install_matcher(
    monkeypatch,
    matcher,
):
    message_service = importlib.import_module(
        "app.services.message_service"
    )

    monkeypatch.setattr(
        message_service,
        "user_matches_assignment",
        matcher,
    )


def _authenticated_user():
    return SimpleNamespace(
        is_authenticated=True,
        id=7,
    )


def test_rejects_missing_and_unauthenticated_users():
    assert (
        target._user_has_any_assigned_survey(
            None
        )
        is False
    )

    assert (
        target._user_has_any_assigned_survey(
            SimpleNamespace(
                is_authenticated=False,
            )
        )
        is False
    )


def test_empty_survey_query_returns_false(
    monkeypatch,
):
    query = _install_survey(
        monkeypatch,
        [],
    )

    _install_matcher(
        monkeypatch,
        lambda row, user: False,
    )

    assert (
        target._user_has_any_assigned_survey(
            _authenticated_user()
        )
        is False
    )

    assert [
        item[0]
        for item in query.calls
    ] == [
        "filter",
        "order_by",
        "limit",
        "all",
    ]


def test_missing_assignments_and_no_match(
    monkeypatch,
):
    rows_seen = []

    surveys = [
        SimpleNamespace(
            assignments=None,
        ),
        SimpleNamespace(
            assignments=_Assignments(
                ["row-a", "row-b"]
            ),
        ),
    ]

    _install_survey(
        monkeypatch,
        surveys,
    )

    def matcher(row, user):
        rows_seen.append(
            (row, user.id)
        )
        return False

    _install_matcher(
        monkeypatch,
        matcher,
    )

    assert (
        target._user_has_any_assigned_survey(
            _authenticated_user()
        )
        is False
    )

    assert rows_seen == [
        ("row-a", 7),
        ("row-b", 7),
    ]


def test_matching_assignment_returns_true(
    monkeypatch,
):
    _install_survey(
        monkeypatch,
        [
            SimpleNamespace(
                assignments=_Assignments(
                    ["no", "yes", "unused"]
                ),
            ),
        ],
    )

    _install_matcher(
        monkeypatch,
        lambda row, user: (
            row == "yes"
            and user.id == 7
        ),
    )

    assert (
        target._user_has_any_assigned_survey(
            _authenticated_user()
        )
        is True
    )


def test_assignment_query_failure_logs_and_continues(
    monkeypatch,
):
    _install_survey(
        monkeypatch,
        [
            SimpleNamespace(
                assignments=_BrokenAssignments(),
            ),
        ],
    )

    _install_matcher(
        monkeypatch,
        lambda row, user: False,
    )

    fake_logger = _FakeLogger()

    with monkeypatch.context() as scoped:
        scoped.setattr(
            logging,
            "getLogger",
            lambda *args, **kwargs: (
                fake_logger
            ),
        )

        result = (
            target
            ._user_has_any_assigned_survey(
                _authenticated_user()
            )
        )

    assert result is False
    assert len(fake_logger.messages) == 1
    assert (
        "effective menu"
        in fake_logger.messages[0]
    )


def test_outer_failure_rolls_back_and_returns_false(
    monkeypatch,
):
    _install_survey(
        monkeypatch,
        [],
        fail_filter=True,
    )

    _install_matcher(
        monkeypatch,
        lambda row, user: False,
    )

    calls = []

    def rollback_hook():
        calls.append("hook")

    def fake_rollback(hook):
        calls.append("rollback")

        if hook is not None:
            hook()

    monkeypatch.setattr(
        target,
        "_rollback",
        fake_rollback,
    )

    assert (
        target._user_has_any_assigned_survey(
            _authenticated_user(),
            rollback=rollback_hook,
        )
        is False
    )

    assert calls == [
        "rollback",
        "hook",
    ]
