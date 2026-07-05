"""Add settings foundation phase1 tables

Revision ID: f103a9d7c2b1
Revises: b7f4e2a1c9d0, e8c3f1a9b4d0
Create Date: 2026-04-07 11:20:00
"""

from alembic import op

revision = "f103a9d7c2b1"
down_revision = ("b7f4e2a1c9d0", "e8c3f1a9b4d0")
branch_labels = None
depends_on = None


def _sqlite_column_exists(table_name, column_name):
    bind = op.get_bind()
    rows = bind.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


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


def _bys360_sqlite_compatible_statements(stmt):
    normalized = " ".join(stmt.strip().split()).upper()

    if normalized.startswith(
        "ALTER TABLE USER_MENU_PERMISSIONS ADD COLUMN IF NOT EXISTS SOURCE_TYPE "
    ):
        if _sqlite_column_exists("user_menu_permissions", "source_type"):
            return []
        return [_bys360_sqlite_ddl_sql(stmt.replace("ADD COLUMN IF NOT EXISTS", "ADD COLUMN"))]

    if normalized.startswith(
        "ALTER TABLE USER_MENU_PERMISSIONS DROP COLUMN IF EXISTS SOURCE_TYPE"
    ):
        if not _sqlite_column_exists("user_menu_permissions", "source_type"):
            return []
        return [_bys360_sqlite_ddl_sql(stmt.replace("DROP COLUMN IF EXISTS", "DROP COLUMN"))]

    return [_bys360_sqlite_ddl_sql(stmt)]


def _exec_many(statements):
    for stmt in statements:
        if op.get_bind().dialect.name == "sqlite":
            for sqlite_stmt in _bys360_sqlite_compatible_statements(stmt):
                op.execute(sqlite_stmt)
        else:
            op.execute(stmt)


def upgrade():
    _exec_many([
        "ALTER TABLE user_menu_permissions ADD COLUMN IF NOT EXISTS source_type VARCHAR(30) NOT NULL DEFAULT 'user_override'",
        """
        CREATE TABLE IF NOT EXISTS role_menu_defaults (
            id SERIAL PRIMARY KEY,
            role_name VARCHAR(50) NOT NULL,
            menu_key VARCHAR(100) NOT NULL,
            is_visible BOOLEAN NOT NULL DEFAULT FALSE,
            source_type VARCHAR(30) NOT NULL DEFAULT 'seed',
            updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            note VARCHAR(255) NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_role_menu_default_role_menu UNIQUE (role_name, menu_key)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_role_menu_defaults_role_name ON role_menu_defaults(role_name)",
        "CREATE INDEX IF NOT EXISTS ix_role_menu_defaults_menu_key ON role_menu_defaults(menu_key)",
        "CREATE INDEX IF NOT EXISTS ix_role_menu_defaults_updated_by_user_id ON role_menu_defaults(updated_by_user_id)",
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            id SERIAL PRIMARY KEY,
            setting_key VARCHAR(120) NOT NULL UNIQUE,
            group_key VARCHAR(50) NOT NULL DEFAULT 'general',
            label VARCHAR(150) NOT NULL,
            value_text TEXT NULL,
            value_type VARCHAR(20) NOT NULL DEFAULT 'string',
            description TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_system_settings_group_key ON system_settings(group_key)",
        "CREATE INDEX IF NOT EXISTS ix_system_settings_is_active ON system_settings(is_active)",
        "CREATE INDEX IF NOT EXISTS ix_system_settings_updated_by_user_id ON system_settings(updated_by_user_id)",
        """
        CREATE TABLE IF NOT EXISTS module_settings (
            id SERIAL PRIMARY KEY,
            module_key VARCHAR(60) NOT NULL,
            setting_key VARCHAR(120) NOT NULL,
            label VARCHAR(150) NOT NULL,
            value_text TEXT NULL,
            value_type VARCHAR(20) NOT NULL DEFAULT 'string',
            description TEXT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_module_setting_module_key UNIQUE (module_key, setting_key)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_module_settings_module_key ON module_settings(module_key)",
        "CREATE INDEX IF NOT EXISTS ix_module_settings_setting_key ON module_settings(setting_key)",
        "CREATE INDEX IF NOT EXISTS ix_module_settings_is_active ON module_settings(is_active)",
        "CREATE INDEX IF NOT EXISTS ix_module_settings_updated_by_user_id ON module_settings(updated_by_user_id)",
    ])


def downgrade():
    _exec_many([
        "DROP INDEX IF EXISTS ix_module_settings_updated_by_user_id",
        "DROP INDEX IF EXISTS ix_module_settings_is_active",
        "DROP INDEX IF EXISTS ix_module_settings_setting_key",
        "DROP INDEX IF EXISTS ix_module_settings_module_key",
        "DROP TABLE IF EXISTS module_settings",
        "DROP INDEX IF EXISTS ix_system_settings_updated_by_user_id",
        "DROP INDEX IF EXISTS ix_system_settings_is_active",
        "DROP INDEX IF EXISTS ix_system_settings_group_key",
        "DROP TABLE IF EXISTS system_settings",
        "DROP INDEX IF EXISTS ix_role_menu_defaults_updated_by_user_id",
        "DROP INDEX IF EXISTS ix_role_menu_defaults_menu_key",
        "DROP INDEX IF EXISTS ix_role_menu_defaults_role_name",
        "DROP TABLE IF EXISTS role_menu_defaults",
        "ALTER TABLE user_menu_permissions DROP COLUMN IF EXISTS source_type",
    ])
