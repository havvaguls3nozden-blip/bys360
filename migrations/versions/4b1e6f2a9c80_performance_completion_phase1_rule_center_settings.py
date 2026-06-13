"""BYS360 Performans Tamamlama Faz 1 kural merkezi ayarlari.

Revision ID: 4b1e6f2a9c80
Revises: 3a9d2f1c8b70
Create Date: 2026-05-04

Bu migration module_settings icindeki performans kural ayarlarini kalici hale getirir.
Model degisikligi olmadan bile deploy oncesi alembic disiplini icin Faz 1 ayar sozlesmesi
migration ile izlenebilir hale getirilir.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "4b1e6f2a9c80"
down_revision = "3a9d2f1c8b70"
branch_labels = None
depends_on = None

BYS360_PERFORMANCE_COMPLETION_PHASE1_RULE_CENTER_SETTINGS = True

PHASE1_SETTINGS = (
    ("performance_scoring", "require_comment_for_score_1", "1 puanda açıklama zorunlu", "bool", "True", "1 verilen değerlendirme kriterlerinde açıklama alanını zorunlu tutar."),
    ("performance_scoring", "require_comment_for_score_5", "5 puanda açıklama zorunlu", "bool", "True", "5 verilen değerlendirme kriterlerinde açıklama alanını zorunlu tutar."),
    ("performance_scoring", "require_general_comment_below_70", "70 altı genel görüş zorunlu", "bool", "True", "Nihai puan 70 altında kaldığında ayrıntılı genel görüş ister."),
    ("performance_scoring", "require_general_comment_above_90", "90 üstü genel görüş zorunlu", "bool", "True", "Nihai puan 90 üstüne çıktığında ayrıntılı genel görüş ister."),
    ("performance_flow", "low_score_requires_president_approval", "70 altı Başkan/Üst Onay zorunlu", "bool", "True", "70 altı sonuçların kesinleşmeden önce Başkan/Üst Onay sürecine düşmesini sağlar."),
    ("performance_flow", "low_score_publish_lock", "70 altı yayın kilidi aktif", "bool", "True", "70 altı karne Başkan/Üst Onay tamamlanmadan personele yayınlanamaz."),
    ("performance_flow", "status_language_mode", "Statü dili", "string", "institutional_tr", "Teknik statü kodlarının kullanıcıya kurumsal Türkçe gösterilmesini sağlar."),
    ("performance_flow", "publish_preflight_uses_rule_center", "Yayın ön kontrol kural merkezini kullansın", "bool", "True", "Yayın öncesi kontrolün merkezi performans kural motorundan beslenmesini zorunlu tutar."),
    ("performance_flow", "personnel_support_publish_preapproval_required", "Yayın öncesi Personel ve Destek ön onayı zorunlu", "bool", "True", "Nihai yayın öncesinde Personel ve Destek Hizmetleri Grup Başkanı ön onay adımını açık tutar."),
)


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

    for module_key, setting_key, label, value_type, default, description in PHASE1_SETTINGS:
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
                .values(
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


def downgrade() -> None:
    if not _table_exists("module_settings"):
        return
    bind = op.get_bind()
    meta = sa.MetaData()
    module_settings = sa.Table("module_settings", meta, autoload_with=bind)
    for module_key, setting_key, *_ in PHASE1_SETTINGS:
        bind.execute(
            module_settings.delete().where(
                module_settings.c.module_key == module_key,
                module_settings.c.setting_key == setting_key,
            )
        )

# BYS360_PHASE4_ALEMBIC_PHASE_MARKER_ALIAS_FIX
# Alembic disiplin gate marker aliasları:
# performance_phase1

