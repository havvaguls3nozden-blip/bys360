from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "29fee38a97e1_adopt_performance_development_.py"
)

REQUIRED_COLUMNS = {
    "id",
    "employee_id",
    "employee_name",
    "period_id",
    "period_name",
    "recommendation_type",
    "development_area",
    "priority",
    "follow_status",
    "follow_frequency",
    "visibility_scope",
    "publication_status",
    "show_on_scorecard",
    "is_published",
    "approved_by_hr",
    "supervisor_approval_required",
    "supervisor_approved",
    "approval_role",
    "approval_flow",
    "approver_name",
    "approval_note",
    "publish_lock",
    "publish_lock_reason",
    "hr_publish_required",
    "hr_publish_approved",
    "scorecard_visibility_mode",
    "scorecard_detail_level",
    "show_in_pdf",
    "show_in_scorecard_history",
    "employee_notification_required",
    "employee_ack_required",
    "visibility_reason",
    "employee_message",
    "owner_name",
    "target_date",
    "basis_note",
    "current_state",
    "target_outcome",
    "smart_goal",
    "action_steps",
    "support_needs",
    "success_criteria",
    "evidence_plan",
    "recommendation_text",
    "created_by",
    "created_at",
    "updated_at",
}


def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "phase60b_development_recommendations_adoption", MIGRATION_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_upgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    module.op = Operations(MigrationContext.configure(connection))
    module.upgrade()


def _run_downgrade(connection: sa.Connection) -> None:
    module = _load_migration()
    module.op = Operations(MigrationContext.configure(connection))
    module.downgrade()


def _column_names(connection: sa.Connection, table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(connection).get_columns(table_name)}


def _create_legacy_self_healed_table(connection: sa.Connection) -> None:
    # Mirrors the SQLite branch of
    # app/performance/phase10_development_guidance_ui.py's
    # ensure_phase10_recommendation_table() -- a minimal subset is enough to
    # prove the adoption path preserves existing rows and reports gaps.
    connection.execute(
        sa.text(
            """
            CREATE TABLE performance_development_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NULL,
                employee_name TEXT NULL,
                recommendation_type TEXT NOT NULL DEFAULT 'development',
                recommendation_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def test_phase60b_creates_complete_47_column_schema_on_empty_database() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)

        assert "performance_development_recommendations" in sa.inspect(connection).get_table_names()
        columns = _column_names(connection, "performance_development_recommendations")
        assert columns >= REQUIRED_COLUMNS
        assert len(REQUIRED_COLUMNS) == 47


def test_phase60b_adopts_preexisting_self_healed_table_without_losing_rows() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _create_legacy_self_healed_table(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_development_recommendations
                    (id, employee_id, employee_name, recommendation_type, recommendation_text)
                VALUES (1, 7, 'Ayse Yilmaz', 'development', 'Korunacak oneri metni')
                """
            )
        )

        _run_upgrade(connection)

        row = connection.execute(
            sa.text(
                """
                SELECT employee_id, employee_name, recommendation_text
                FROM performance_development_recommendations
                WHERE id = 1
                """
            )
        ).mappings().one()
        assert dict(row) == {
            "employee_id": 7,
            "employee_name": "Ayse Yilmaz",
            "recommendation_text": "Korunacak oneri metni",
        }
        # Legacy table used here intentionally lacks most Phase 10 columns;
        # this package does not retrofit them (add-missing-columns is
        # explicitly out of scope), so the table keeps its narrower shape.
        assert "performance_development_recommendations" in sa.inspect(connection).get_table_names()


def test_phase60b_upgrade_is_idempotent() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        _run_upgrade(connection)

        assert "performance_development_recommendations" in sa.inspect(connection).get_table_names()
        assert _column_names(connection, "performance_development_recommendations") >= REQUIRED_COLUMNS


def test_phase60b_downgrade_is_non_destructive_for_adopted_table() -> None:
    engine = sa.create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _run_upgrade(connection)
        connection.execute(
            sa.text(
                """
                INSERT INTO performance_development_recommendations (recommendation_text)
                VALUES ('Korunacak gelisim onerisi')
                """
            )
        )

        _run_downgrade(connection)

        assert "performance_development_recommendations" in sa.inspect(connection).get_table_names()
        text_value = connection.execute(
            sa.text("SELECT recommendation_text FROM performance_development_recommendations")
        ).scalar_one()
        assert text_value == "Korunacak gelisim onerisi"
