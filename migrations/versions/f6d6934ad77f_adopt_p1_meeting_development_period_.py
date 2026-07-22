"""Adopt P1 meeting development period scope columns into Alembic ownership.

Revision ID: f6d6934ad77f
Revises: f5e19f9107d7
Create Date: 2026-07-22 21:31:22.866816

Faz 7 P1 toplanti gelistirme servisi
(``app/services/performance/meeting_p1_scope.py``) bu 5 kolonu eskiden
calisma zamaninda ``ALTER TABLE`` ile ekliyordu. ``performance_periods``
tablosu zaten cok sayida onceki migration tarafindan yonetiliyor; bu
migration sadece eksik kalan 5 uyum kolonunu ekler.

``scope_type`` kolonuna kasitli olarak DOKUNULMAZ: o kolon zaten
``v58a1c2d3e4f_add_period_scope_type_safety.py`` ve
``b8e2d4c6f901_performance_completion_phase8_period_scope.py``
migrationlari tarafindan (farkli bir "phase8" kapsam ozelligi icin,
``VARCHAR(64)`` olarak) sahiplenilmis durumda; ayni isimli ikinci bir
sahiplik burada tanimlanmaz.
"""

from __future__ import annotations

from collections.abc import Iterable

import sqlalchemy as sa
from alembic import op

revision = "f6d6934ad77f"
down_revision = "f5e19f9107d7"
branch_labels = None
depends_on = None


_TABLE_NAME = "performance_periods"


def _table_exists(bind: sa.engine.Connection, table_name: str) -> bool:
    return table_name in sa.inspect(bind).get_table_names()


def _column_names(bind: sa.engine.Connection, table_name: str) -> set[str]:
    if not _table_exists(bind, table_name):
        return set()
    return {column["name"] for column in sa.inspect(bind).get_columns(table_name)}


def _p1_scope_columns() -> tuple[sa.Column, ...]:
    return (
        sa.Column("scope_unit_label", sa.String(length=255), nullable=True),
        sa.Column("scope_category_label", sa.String(length=255), nullable=True),
        sa.Column("scope_personnel_filter", sa.Text(), nullable=True),
        sa.Column(
            "level_3_column_visible",
            sa.Boolean(),
            nullable=True,
            server_default=sa.false(),
        ),
        sa.Column(
            "scorecard_readability_mode",
            sa.String(length=40),
            nullable=True,
            server_default=sa.text("'kurumsal'"),
        ),
    )


def _add_missing_columns(
    bind: sa.engine.Connection,
    columns: Iterable[sa.Column],
) -> None:
    existing = _column_names(bind, _TABLE_NAME)
    missing = [column for column in columns if column.name not in existing]
    if not missing:
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(_TABLE_NAME, recreate="always") as batch_op:
            for column in missing:
                batch_op.add_column(column)
        return

    for column in missing:
        op.add_column(_TABLE_NAME, column)


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, _TABLE_NAME):
        # performance_periods bu repoda 7+ onceki migration tarafindan
        # yonetiliyor; asla olusmamis olmasi beklenmez. Sessizce atlamak
        # yerine anlasilir bir hata vererek eksik/bozuk bir zincire karsi
        # erken uyari veriyoruz.
        raise RuntimeError(
            "performance_periods tablosu bulunamadi; P1 kapsam kolonlari "
            "eklenemedi. Onceki migrationlarin (performance_periods "
            "tablosunu olusturan) uygulanmis oldugundan emin olun."
        )

    _add_missing_columns(bind, _p1_scope_columns())


def downgrade() -> None:
    """Preserve the adopted P1 scope columns and their data.

    The migration cannot safely know whether each column existed before
    Alembic ownership was introduced, and live period rows may already carry
    scope data set through the legacy runtime path. Downgrade is
    intentionally a no-op.
    """
