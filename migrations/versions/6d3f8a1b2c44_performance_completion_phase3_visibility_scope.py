"""BYS360 Performans Tamamlama Faz 3 gorunurluk ve yetki kapsam ayarlari.

Revision ID: 6d3f8a1b2c44
Revises: 5c2d7a8e9f11
Create Date: 2026-05-04

Bu migration Faz 3 gorunurluk/yetki sozlesmesini Faz 2 kategori altyapisi sonrasina baglar.
Menu gorunurlugu ile backend route/query korumasinin birlikte calismasi icin module_settings
uzerinden kalici ayar izleri olusturur.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "6d3f8a1b2c44"
down_revision = "5c2d7a8e9f11"
branch_labels = None
depends_on = None

BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_SCOPE_SETTINGS = True
BYS360_PERFORMANCE_COMPLETION_PHASE3_BACKEND_ROUTE_QUERY_GUARD = True

PHASE3_SETTINGS = (
    ("performance_visibility", "backend_route_guard_enabled", "Backend route görünürlük kilidi aktif", "bool", "True", "Menü gizlense bile URL ile erişimde yetki/kapsam kontrolünü zorunlu tutar."),
    ("performance_visibility", "employee_own_scorecard_only", "Personel yalnızca kendi karnesini görür", "bool", "True", "Personel rolündeki kullanıcıların başka personel karne/detay kayıtlarına erişmesini engeller."),
    ("performance_visibility", "employee_category_average_no_detail", "Personel kategori ortalamasını kişi detaysız görür", "bool", "True", "Personelin kendi kategori/grup ortalamasını kişi isimleri ve detayları olmadan görmesini sağlar."),
    ("performance_visibility", "coordinator_scope_only", "Koordinatör yalnızca kendi kapsamını görür", "bool", "True", "Koordinatörün çalışma grubu/kapsam dışı performans verisi görmesini engeller."),
    ("performance_visibility", "group_head_scope_only", "Grup Başkanı yalnızca kendi grup/üst birim kapsamını görür", "bool", "True", "Grup başkanı kapsamını kendi organizasyon alanıyla sınırlar."),
    ("performance_visibility", "president_admin_global_visibility", "Başkan ve Admin kurum geneli görünürlük alır", "bool", "True", "Kurum geneli görünürlüğü Başkan ve Admin/Sistem Yöneticisi seviyesine bağlar."),
    ("performance_visibility", "corporate_access_denied_page", "Kurumsal erişim engeli ekranı kullanılsın", "bool", "True", "Yetkisiz erişimde beyaz sayfa yerine Türkçe kurumsal erişim engeli cevabı üretir."),
    ("performance_visibility", "menu_backend_permission_sync", "Menü görünürlüğü backend yetkiyle birlikte kontrol edilsin", "bool", "True", "Menüde saklama ile route/query kontrolünün aynı Faz 3 görünürlük sözleşmesine bağlanmasını sağlar."),
    ("performance_visibility", "category_average_person_detail_block", "Kategori ortalamasında kişi detayı engellensin", "bool", "True", "Personel ve yetkisiz kullanıcılar için kategori ortalamasında kişi bazlı detay döndürülmesini engeller."),
)

# Gate alias marker'ları:
# performance.phase3.backend_route_guard_enabled
# performance.phase3.employee_own_scorecard_only
# performance.phase3.coordinator_scope_only
# performance.phase3.group_head_scope_only
# performance.phase3.president_admin_global_visibility
# performance.phase3.corporate_access_denied_page
# performance.phase3.category_average_person_detail_block


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        return table_name in set(inspector.get_table_names())
    except Exception:
        return False


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    try:
        return {col["name"] for col in inspector.get_columns(table_name)}
    except Exception:
        return set()


def _ensure_module_settings_table() -> None:
    if _table_exists("module_settings"):
        return
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


def _ensure_columns() -> None:
    cols = _columns("module_settings")
    if "value_text" not in cols:
        op.add_column("module_settings", sa.Column("value_text", sa.Text(), nullable=True))
    if "value_type" not in cols:
        op.add_column("module_settings", sa.Column("value_type", sa.String(length=20), nullable=False, server_default="string"))
    if "description" not in cols:
        op.add_column("module_settings", sa.Column("description", sa.Text(), nullable=True))
    if "is_active" not in cols:
        op.add_column("module_settings", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))


def upgrade() -> None:
    _ensure_module_settings_table()
    _ensure_columns()
    bind = op.get_bind()
    meta = sa.MetaData()
    module_settings = sa.Table("module_settings", meta, autoload_with=bind)
    for module_key, setting_key, label, value_type, default, description in PHASE3_SETTINGS:
        existing = bind.execute(
            sa.select(module_settings.c.id).where(
                module_settings.c.module_key == module_key,
                module_settings.c.setting_key == setting_key,
            )
        ).first()
        if existing:
            bind.execute(
                module_settings.update()
                .where(module_settings.c.id == existing[0])
                .values(label=label, value_type=value_type, description=description, is_active=True)
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


def downgrade() -> None:
    if not _table_exists("module_settings"):
        return
    bind = op.get_bind()
    meta = sa.MetaData()
    module_settings = sa.Table("module_settings", meta, autoload_with=bind)
    for module_key, setting_key, *_ in PHASE3_SETTINGS:
        bind.execute(
            module_settings.delete().where(
                module_settings.c.module_key == module_key,
                module_settings.c.setting_key == setting_key,
            )
        )

# BYS360_PHASE4_ALEMBIC_PHASE_MARKER_ALIAS_FIX
# Alembic disiplin gate marker aliasları:
# performance_phase3

