"""Add unit menu profiles for settings phase2

Revision ID: a9f2b7c4d001
Revises: f103a9d7c2b1
Create Date: 2026-04-07 12:15:00
"""

from alembic import op

revision = "a9f2b7c4d001"
down_revision = "f103a9d7c2b1"
branch_labels = None
depends_on = None


def _bys360_sqlite_ddl_sql(stmt):
    """SQLite lokal geliştirme için PostgreSQL DDL ifadelerini güvenli dönüştürür.

    PostgreSQL ortamında migration davranışı değişmez.
    """
    sql = stmt
    sql = sql.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")
    sql = sql.replace("BOOLEAN NOT NULL DEFAULT FALSE", "INTEGER NOT NULL DEFAULT 0")
    sql = sql.replace("BOOLEAN NOT NULL DEFAULT TRUE", "INTEGER NOT NULL DEFAULT 1")
    sql = sql.replace("BOOLEAN DEFAULT FALSE", "INTEGER DEFAULT 0")
    sql = sql.replace("BOOLEAN DEFAULT TRUE", "INTEGER DEFAULT 1")
    sql = sql.replace("DEFAULT NOW()", "DEFAULT CURRENT_TIMESTAMP")
    return sql


def _exec_many(statements):
    for stmt in statements:
        if op.get_bind().dialect.name == "sqlite":
            op.execute(_bys360_sqlite_ddl_sql(stmt))
        else:
            op.execute(stmt)


def upgrade():
    _exec_many([
        """
        CREATE TABLE IF NOT EXISTS unit_menu_profiles (
            id SERIAL PRIMARY KEY,
            unit_name VARCHAR(150) NOT NULL,
            menu_key VARCHAR(100) NOT NULL,
            is_visible BOOLEAN NOT NULL DEFAULT FALSE,
            source_type VARCHAR(30) NOT NULL DEFAULT 'manual',
            updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            note VARCHAR(255) NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_unit_menu_profile_unit_menu UNIQUE (unit_name, menu_key)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_unit_menu_profiles_unit_name ON unit_menu_profiles(unit_name)",
        "CREATE INDEX IF NOT EXISTS ix_unit_menu_profiles_menu_key ON unit_menu_profiles(menu_key)",
        "CREATE INDEX IF NOT EXISTS ix_unit_menu_profiles_updated_by_user_id ON unit_menu_profiles(updated_by_user_id)",
    ])


def downgrade():
    _exec_many([
        "DROP INDEX IF EXISTS ix_unit_menu_profiles_updated_by_user_id",
        "DROP INDEX IF EXISTS ix_unit_menu_profiles_menu_key",
        "DROP INDEX IF EXISTS ix_unit_menu_profiles_unit_name",
        "DROP TABLE IF EXISTS unit_menu_profiles",
    ])
