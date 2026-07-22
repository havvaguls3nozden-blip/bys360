from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.services.performance import process_engine_phase5_notifications as service


class _FakeIdentifierPreparer:
    def quote(self, value: str) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = _FakeIdentifierPreparer()


class _FakeEngine:
    dialect = _FakeDialect()


@dataclass
class _FakeResult:
    scalar_value: object = None

    def scalar(self):
        return self.scalar_value


class _FakeSession:
    def __init__(self, scalar_value: object = None) -> None:
        self.scalar_value = scalar_value
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    def execute(self, statement, params=None) -> _FakeResult:
        self.calls.append((str(statement), params))
        return _FakeResult(self.scalar_value)


class _FakeDb:
    def __init__(self, scalar_value: object = None) -> None:
        self.engine = _FakeEngine()
        self.session = _FakeSession(scalar_value)


def test_insert_if_columns_quotes_closed_table_and_column_sets(
    monkeypatch,
) -> None:
    fake_db = _FakeDb(71)
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(
        service,
        "_table_columns",
        lambda table_name: {
            "id",
            "user_id",
            "title",
            "created_at",
            "unsafe_column; DROP TABLE users",
        },
    )

    inserted_id = service._insert_if_columns(
        "notifications",
        {
            "user_id": 7,
            "title": "Bekleyen değerlendirme",
            "created_at": "2026-07-22T12:00:00",
            "unsafe_column; DROP TABLE users": "ignored",
        },
    )

    assert inserted_id == 71
    assert fake_db.session.calls == [
        (
            (
                'INSERT INTO "notifications" '
                '("user_id", "title", "created_at") '
                'VALUES (:user_id, :title, :created_at) RETURNING id'
            ),
            {
                "user_id": 7,
                "title": "Bekleyen değerlendirme",
                "created_at": "2026-07-22T12:00:00",
            },
        )
    ]


def test_insert_if_columns_rejects_unknown_or_unsafe_table(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(service, "_table_columns", lambda table_name: set())

    for table_name in (
        "other_notifications",
        "notifications; DROP TABLE users",
        "public.notifications",
    ):
        with pytest.raises(ValueError):
            service._insert_if_columns(table_name, {"title": "x"})

    assert fake_db.session.calls == []


def test_update_process_notification_quotes_allowlisted_assignments(
    monkeypatch,
) -> None:
    fake_db = _FakeDb()
    monkeypatch.setattr(service, "db", fake_db)
    monkeypatch.setattr(
        service,
        "_table_columns",
        lambda table_name: {
            "app_notification_id",
            "updated_at",
            "unsafe_column; DROP TABLE users",
        },
    )

    service._update_process_notification(
        19,
        {
            "app_notification_id": 71,
            "updated_at": "2026-07-22T12:00:00",
            "unsafe_column; DROP TABLE users": "ignored",
        },
    )

    assert fake_db.session.calls == [
        (
            (
                "UPDATE performance_process_notifications SET "
                '"app_notification_id" = :app_notification_id, '
                '"updated_at" = :updated_at '
                "WHERE id = :notification_id"
            ),
            {
                "app_notification_id": 71,
                "updated_at": "2026-07-22T12:00:00",
                "notification_id": 19,
            },
        )
    ]
