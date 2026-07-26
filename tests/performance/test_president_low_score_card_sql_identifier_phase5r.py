from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.performance import (
    president_low_score_card_routes as routes,
)


class _FakeIdentifierPreparer:
    def quote(
        self,
        value: str,
    ) -> str:
        return f'"{value}"'


class _FakeDialect:
    identifier_preparer = (
        _FakeIdentifierPreparer()
    )


class _FakeEngine:
    dialect = _FakeDialect()


@dataclass
class _FakeResult:
    rows: list[dict[str, object]]

    def mappings(
        self,
    ) -> _FakeResult:
        return self

    def all(
        self,
    ) -> list[dict[str, object]]:
        return list(
            self.rows
        )


class _FakeSession:
    def __init__(
        self,
        rows: list[dict[str, object]] | None = None,
    ) -> None:
        self.rows = list(
            rows
            or []
        )
        self.calls: list[
            tuple[
                str,
                dict[str, object] | None,
            ]
        ] = []
        self.rollback_count = 0

    def execute(
        self,
        statement,
        params=None,
    ) -> _FakeResult:
        self.calls.append(
            (
                str(
                    statement
                ),
                params,
            )
        )

        return _FakeResult(
            self.rows
        )

    def rollback(
        self,
    ) -> None:
        self.rollback_count += 1


class _FakeDb:
    def __init__(
        self,
        rows: list[dict[str, object]] | None = None,
    ) -> None:
        self.engine = _FakeEngine()
        self.session = _FakeSession(
            rows
        )


def _prepare(
    monkeypatch,
    *,
    columns: set[str],
    rows: list[dict[str, object]] | None = None,
) -> _FakeDb:
    fake_db = _FakeDb(
        rows
    )

    monkeypatch.setattr(
        routes,
        "db",
        fake_db,
    )
    monkeypatch.setattr(
        routes,
        "_table_exists",
        lambda table_name: True,
    )
    monkeypatch.setattr(
        routes,
        "_columns",
        lambda table_name: set(
            columns
        ),
    )

    return fake_db


def test_fetch_history_quotes_identifiers_and_binds_value(
    monkeypatch,
) -> None:
    fake_db = _prepare(
        monkeypatch,
        columns={
            "id",
            "evaluation_id",
            "score_value",
            "action_at",
            "created_at",
        },
        rows=[
            {
                "id": 1,
                "evaluation_id": 42,
                "score_value": 91,
            }
        ],
    )

    rows = routes._fetch_history(
        "performance_scoring_history",
        42,
        "action_at",
    )

    assert rows == [
        {
            "id": 1,
            "evaluation_id": 42,
            "score_value": 91,
        }
    ]

    assert fake_db.session.calls == [
        (
            (
                'SELECT "id", "evaluation_id", '
                '"score_value", "action_at", '
                '"created_at" '
                'FROM "performance_scoring_history" '
                'WHERE "evaluation_id" = :evaluation_id '
                'ORDER BY "action_at" ASC NULLS LAST, '
                '"id" ASC LIMIT 200'
            ),
            {
                "evaluation_id": 42
            },
        )
    ]


def test_fetch_history_rejects_unknown_or_unsafe_table(
    monkeypatch,
) -> None:
    fake_db = _prepare(
        monkeypatch,
        columns={
            "id",
            "evaluation_id",
            "action_at",
        },
    )

    invalid_tables = (
        "other_history_table",
        (
            "performance_scoring_history; "
            "DROP TABLE users"
        ),
        "public.performance_scoring_history",
    )

    for table_name in invalid_tables:
        with pytest.raises(
            ValueError
        ):
            routes._fetch_history(
                table_name,
                42,
                "action_at",
            )

    assert fake_db.session.calls == []


def test_fetch_history_rejects_unknown_order_and_falls_back_safely(
    monkeypatch,
) -> None:
    rejection_db = _prepare(
        monkeypatch,
        columns={
            "id",
            "evaluation_id",
            "created_at",
        },
    )

    for order_name in (
        "updated_at",
        "action_at DESC",
    ):
        with pytest.raises(
            ValueError
        ):
            routes._fetch_history(
                "performance_process_flow_steps",
                7,
                order_name,
            )

    assert rejection_db.session.calls == []

    fallback_db = _prepare(
        monkeypatch,
        columns={
            "id",
            "evaluation_id",
            "status",
            "created_at",
        },
        rows=[
            {
                "id": 9,
                "evaluation_id": 7,
                "status": "done",
            }
        ],
    )

    rows = routes._fetch_history(
        "performance_process_flow_steps",
        7,
        "action_at",
    )

    assert rows == [
        {
            "id": 9,
            "evaluation_id": 7,
            "status": "done",
        }
    ]

    sql, params = (
        fallback_db.session.calls[0]
    )

    assert (
        'FROM "performance_process_flow_steps"'
        in sql
    )
    assert (
        'ORDER BY "created_at" ASC NULLS LAST, '
        '"id" ASC'
        in sql
    )
    assert params == {
        "evaluation_id": 7
    }
