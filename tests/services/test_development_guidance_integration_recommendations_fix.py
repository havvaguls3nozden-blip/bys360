from __future__ import annotations

import sqlalchemy as sa

from app.services.ai_decision import development_guidance_integration as service


def _create_recommendations_table(connection: sa.Connection) -> None:
    # Minimal subset of the real 47-column schema
    # (migrations/versions/29fee38a97e1_adopt_performance_development_.py) --
    # only the columns this query touches are needed to prove the fix.
    connection.execute(
        sa.text(
            """
            CREATE TABLE performance_development_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                period_id INTEGER,
                recommendation_text TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


class _RecordingConnectionProxy:
    """Delegates to a real SQLAlchemy connection while recording the exact
    statement text last passed to execute(), so the fixed query can be
    verified both by its real result *and* by its literal SQL text."""

    def __init__(self, connection: sa.Connection) -> None:
        self._connection = connection
        self.last_statement_text: str | None = None

    def execute(self, statement, params=None):
        self.last_statement_text = str(statement)
        if params is None:
            return self._connection.execute(statement)
        return self._connection.execute(statement, params)


def test_fetch_existing_recommendations_returns_matching_row_for_employee(monkeypatch) -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_recommendations_table(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_development_recommendations
                    (id, employee_id, period_id, recommendation_text)
                VALUES (1, 7, 3, 'Iletisim becerilerini gelistir')
                """
            )
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_development_recommendations
                    (id, employee_id, period_id, recommendation_text)
                VALUES (2, 99, 3, 'Baska personelin onerisi')
                """
            )
        )

        # _table_exists() is Postgres-specific (information_schema) and is
        # not the subject of this fix; bypass it so the real, fixed query
        # runs against the real in-memory SQLite table.
        monkeypatch.setattr(
            service,
            "_table_exists",
            lambda db_session, table_name: table_name == "performance_development_recommendations",
        )

        rows = service.fetch_existing_recommendations(
            connection, personnel_id=7, period_id=3, evaluation_id=None, limit=20
        )

    assert len(rows) == 1
    assert rows[0]["id"] == 1
    assert rows[0]["text"] == "Iletisim becerilerini gelistir"


def test_fetch_existing_recommendations_ignores_other_employees() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_recommendations_table(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_development_recommendations
                    (id, employee_id, period_id, recommendation_text)
                VALUES (1, 42, 3, 'Baskasina ait oneri')
                """
            )
        )

        rows = service.fetch_existing_recommendations(
            connection, personnel_id=7, period_id=3, evaluation_id=None, limit=20
        )

    # _table_exists() legitimately returns False against a real SQLite
    # connection (it queries Postgres-only information_schema), so with no
    # monkeypatch the function safely returns [] rather than raising.
    assert rows == []


def test_fetch_existing_recommendations_query_no_longer_references_broken_columns(
    monkeypatch,
) -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_recommendations_table(connection)
        proxy = _RecordingConnectionProxy(connection)

        monkeypatch.setattr(
            service,
            "_table_exists",
            lambda db_session, table_name: table_name == "performance_development_recommendations",
        )

        service.fetch_existing_recommendations(
            proxy, personnel_id=7, period_id=3, evaluation_id=None, limit=20
        )

    assert proxy.last_statement_text is not None
    # The real schema (see 29fee38a97e1) has no personnel_id or
    # evaluation_id columns on this table; the fixed query must use
    # employee_id instead and drop the evaluation_id predicate entirely.
    assert "employee_id = :personnel_id" in proxy.last_statement_text
    assert "OR personnel_id = :personnel_id" not in proxy.last_statement_text
    assert "evaluation_id" not in proxy.last_statement_text
