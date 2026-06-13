"""BYS360 Performans Tamamlama Faz 2 personel kategori ve grup altyapisi.

Revision ID: 5c2d7a8e9f11
Revises: 4b1e6f2a9c80
Create Date: 2026-05-04

Bu migration, Faz 2 kategori/grup sozlesmesini Faz 1 kural merkezi sonrasina baglar.
Eski v55 zincirinde personnel_categories zaten olusmus olabilir; bu dosya idempotent calisir.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision = "5c2d7a8e9f11"
down_revision = "4b1e6f2a9c80"
branch_labels = None
depends_on = None

BYS360_PERFORMANCE_COMPLETION_PHASE2_PERSONNEL_CATEGORY_GROUPS = True

DEFAULT_CATEGORIES = (
    ("guvenlik", "Güvenlik", 10),
    ("temizlik", "Temizlik", 20),
    ("idari_personel", "İdari Personel", 30),
    ("teknik_personel", "Teknik Personel", 40),
    ("deneme_sureli_personel", "Deneme Süreli Personel", 50),
    ("diger", "Diğer", 60),
)

PHASE2_SETTINGS = (
    ("performance_categories", "categories_enabled", "Personel kategori altyapısı aktif", "bool", "True", "Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel ve Diğer kategorilerini performans süreçlerinde etkin tutar."),
    ("performance_categories", "personnel_card_category_required", "Personel kartında kategori alanı zorunlu", "bool", "True", "Personel ekleme/düzenleme ekranlarında kategori alanının kurumsal veri olarak tutulmasını sağlar."),
    ("performance_categories", "import_category_column_enabled", "Toplu personel import kategori sütununu desteklesin", "bool", "True", "Excel/toplu aktarımda kategori/personel kategorisi sütunlarının okunmasını sağlar."),
    ("performance_reporting", "category_filter_enabled", "Performans raporlarında kategori filtresi aktif", "bool", "True", "Raporlarda personel/grup kategorisine göre filtreleme yapılmasını sağlar."),
    ("performance_reporting", "category_average_privacy_no_detail", "Kategori ortalaması kişi detayı göstermeden hesaplansın", "bool", "True", "Personel yalnızca kendi kategori ortalamasını görür; kategori içindeki kişi detayları gösterilmez."),
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


def _indexes(bind, table_name: str) -> set[str]:
    try:
        return {idx.get("name") for idx in inspect(bind).get_indexes(table_name) if idx.get("name")}
    except Exception:
        return set()


def _fk_names(bind, table_name: str) -> set[str]:
    try:
        return {fk.get("name") for fk in inspect(bind).get_foreign_keys(table_name) if fk.get("name")}
    except Exception:
        return set()


def _ensure_personnel_categories(bind) -> None:
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
    indexes = _indexes(bind, "personnel_categories")
    for name, column in (
        ("ix_personnel_categories_name", "name"),
        ("ix_personnel_categories_code", "code"),
        ("ix_personnel_categories_is_active", "is_active"),
        ("ix_personnel_categories_sort_order", "sort_order"),
    ):
        if name not in indexes:
            op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON personnel_categories ({column})")


def _ensure_users_category_columns(bind) -> None:
    if not _has_table(bind, "users"):
        return
    columns = _columns(bind, "users")
    if "personnel_category" not in columns:
        op.add_column("users", sa.Column("personnel_category", sa.String(length=80), nullable=True, server_default="Diğer"))
        columns.add("personnel_category")
    if "performance_category_id" not in columns:
        op.add_column("users", sa.Column("performance_category_id", sa.Integer(), nullable=True))
        columns.add("performance_category_id")
    indexes = _indexes(bind, "users")
    if "ix_users_personnel_category" not in indexes:
        op.execute("CREATE INDEX IF NOT EXISTS ix_users_personnel_category ON users (personnel_category)")
    if "ix_users_performance_category_id" not in indexes:
        op.execute("CREATE INDEX IF NOT EXISTS ix_users_performance_category_id ON users (performance_category_id)")


def _seed_categories(bind) -> None:
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


def _backfill_users(bind) -> None:
    if not _has_table(bind, "users"):
        return
    bind.execute(text("UPDATE users SET personnel_category = 'Diğer' WHERE personnel_category IS NULL OR TRIM(personnel_category) = ''"))
    if bind.dialect.name == "sqlite":
        rows = bind.execute(text("SELECT id, name FROM personnel_categories")).fetchall()
        for row in rows:
            bind.execute(text("UPDATE users SET performance_category_id = :category_id WHERE performance_category_id IS NULL AND personnel_category = :name"), {"category_id": row[0], "name": row[1]})
    else:
        bind.execute(text("""
            UPDATE users
               SET performance_category_id = pc.id
              FROM personnel_categories pc
             WHERE users.performance_category_id IS NULL
               AND users.personnel_category = pc.name
        """))
        if "fk_users_performance_category_id" not in _fk_names(bind, "users"):
            try:
                op.create_foreign_key(
                    "fk_users_performance_category_id",
                    "users",
                    "personnel_categories",
                    ["performance_category_id"],
                    ["id"],
                    ondelete="SET NULL",
                )
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (migrations/versions/5c2d7a8e9f11_performance_completion_phase2_personnel_category_groups.py:154)")


def _ensure_module_settings(bind) -> None:
    if not _has_table(bind, "module_settings"):
        op.create_table(
            "module_settings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("module_key", sa.String(length=60), nullable=False, index=True),
            sa.Column("setting_key", sa.String(length=120), nullable=False, index=True),
            sa.Column("label", sa.String(length=150), nullable=False),
            sa.Column("value_text", sa.Text(), nullable=True),
            sa.Column("value_type", sa.String(length=20), nullable=False, server_default="string"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("module_key", "setting_key", name="uq_module_setting_module_key"),
        )
    columns = _columns(bind, "module_settings")
    if "value_text" not in columns:
        op.add_column("module_settings", sa.Column("value_text", sa.Text(), nullable=True))
    if "value_type" not in columns:
        op.add_column("module_settings", sa.Column("value_type", sa.String(length=20), nullable=False, server_default="string"))
    if "description" not in columns:
        op.add_column("module_settings", sa.Column("description", sa.Text(), nullable=True))
    if "is_active" not in columns:
        op.add_column("module_settings", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))


def _seed_phase2_settings(bind) -> None:
    meta = sa.MetaData()
    module_settings = sa.Table("module_settings", meta, autoload_with=bind)
    for module_key, setting_key, label, value_type, default, description in PHASE2_SETTINGS:
        existing = bind.execute(
            sa.select(module_settings.c.id).where(
                module_settings.c.module_key == module_key,
                module_settings.c.setting_key == setting_key,
            )
        ).first()
        if existing:
            bind.execute(
                module_settings.update().where(module_settings.c.id == existing[0]).values(
                    label=label,
                    value_type=value_type,
                    description=description,
                    is_active=True,
                )
            )
        else:
            bind.execute(
                module_settings.insert().values(
                    module_key=module_key,
                    setting_key=setting_key,
                    label=label,
                    value_text=default,
                    value_type=value_type,
                    description=description,
                    is_active=True,
                )
            )


def upgrade() -> None:
    bind = op.get_bind()
    _ensure_personnel_categories(bind)
    _ensure_users_category_columns(bind)
    _seed_categories(bind)
    _backfill_users(bind)
    _ensure_module_settings(bind)
    _seed_phase2_settings(bind)


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "module_settings"):
        meta = sa.MetaData()
        module_settings = sa.Table("module_settings", meta, autoload_with=bind)
        for module_key, setting_key, *_ in PHASE2_SETTINGS:
            bind.execute(
                module_settings.delete().where(
                    module_settings.c.module_key == module_key,
                    module_settings.c.setting_key == setting_key,
                )
            )

# BYS360_PHASE4_ALEMBIC_PHASE_MARKER_ALIAS_FIX
# Alembic disiplin gate marker aliasları:
# performance_phase2

