"""BYS360 Faz 2 personel kategori ve grup altyapısı.

Revision ID: 2f6c1e9a2b30
Revises: 1f4b9c8d7e6a
Create Date: 2026-05-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "2f6c1e9a2b30"
down_revision = "1f4b9c8d7e6a"
branch_labels = None
depends_on = None

DEFAULT_CATEGORIES = (
    ("guvenlik", "Güvenlik", 10),
    ("temizlik", "Temizlik", 20),
    ("idari_personel", "İdari Personel", 30),
    ("teknik_personel", "Teknik Personel", 40),
    ("deneme_sureli_personel", "Deneme Süreli Personel", 50),
    ("diger", "Diğer", 60),
)


def _has_table(bind, table_name: str) -> bool:
    try:
        return inspect(bind).has_table(table_name)
    except Exception:
        return False


def _columns(bind, table_name: str) -> set[str]:
    try:
        return {column["name"] for column in inspect(bind).get_columns(table_name)}
    except Exception:
        return set()


def _fk_names(bind, table_name: str) -> set[str]:
    try:
        return {fk.get("name") for fk in inspect(bind).get_foreign_keys(table_name) if fk.get("name")}
    except Exception:
        return set()


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if not _has_table(bind, "personnel_categories"):
        op.create_table(
            "personnel_categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("code", sa.String(length=80), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("name", name="uq_personnel_categories_name"),
            sa.UniqueConstraint("code", name="uq_personnel_categories_code"),
        )
        op.create_index("ix_personnel_categories_name", "personnel_categories", ["name"])
        op.create_index("ix_personnel_categories_code", "personnel_categories", ["code"])
        op.create_index("ix_personnel_categories_is_active", "personnel_categories", ["is_active"])
        op.create_index("ix_personnel_categories_sort_order", "personnel_categories", ["sort_order"])

    user_columns = _columns(bind, "users")
    if "personnel_category" not in user_columns:
        op.add_column("users", sa.Column("personnel_category", sa.String(length=80), nullable=True, server_default="Diğer"))
        user_columns.add("personnel_category")
    if "performance_category_id" not in user_columns:
        op.add_column("users", sa.Column("performance_category_id", sa.Integer(), nullable=True))
        op.create_index("ix_users_performance_category_id", "users", ["performance_category_id"])

    for code, name, sort_order in DEFAULT_CATEGORIES:
        bind.execute(text("""
            INSERT INTO personnel_categories (code, name, description, sort_order, is_active, created_at, updated_at)
            SELECT :code, :name, :description, :sort_order, :is_active, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            WHERE NOT EXISTS (SELECT 1 FROM personnel_categories WHERE name = :name OR code = :code)
        """), {
            "code": code,
            "name": name,
            "description": f"{name} personel performans kategori grubu",
            "sort_order": sort_order,
            "is_active": True,
        })

    bind.execute(text("UPDATE users SET personnel_category = 'Diğer' WHERE personnel_category IS NULL OR TRIM(personnel_category) = ''"))
    bind.execute(text("""
        UPDATE users
           SET performance_category_id = pc.id
          FROM personnel_categories pc
         WHERE users.performance_category_id IS NULL
           AND users.personnel_category = pc.name
    """)) if dialect != "sqlite" else None

    if dialect == "sqlite":
        rows = bind.execute(text("SELECT id, name FROM personnel_categories")).fetchall()
        for row in rows:
            bind.execute(text("UPDATE users SET performance_category_id = :category_id WHERE performance_category_id IS NULL AND personnel_category = :name"), {"category_id": row[0], "name": row[1]})

    if dialect != "sqlite" and "fk_users_performance_category_id" not in _fk_names(bind, "users"):
        op.create_foreign_key(
            "fk_users_performance_category_id",
            "users",
            "personnel_categories",
            ["performance_category_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if _has_table(bind, "users") and "performance_category_id" in _columns(bind, "users"):
        if dialect != "sqlite" and "fk_users_performance_category_id" in _fk_names(bind, "users"):
            op.drop_constraint("fk_users_performance_category_id", "users", type_="foreignkey")
        try:
            op.drop_index("ix_users_performance_category_id", table_name="users")
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (migrations/versions/2f6c1e9a2b30_add_personnel_categories_phase2.py:127)")
        op.drop_column("users", "performance_category_id")
    if _has_table(bind, "personnel_categories"):
        op.drop_table("personnel_categories")
