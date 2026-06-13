
"""Ayar ve yetki omurgasi modelleri.

Faz 1 ile Ayarlar ekraninin kullanici bazli menu gorunurlugunun otesine gecip
rol varsayilanlari, modül davranislari ve genel sistem ayarlari icin kalici bir
veri katmani olusturmasi hedeflenir.
"""
from __future__ import annotations

from .base import TimestampMixin, db


class RoleMenuDefault(TimestampMixin, db.Model):
    __tablename__ = "role_menu_defaults"

    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False, index=True)
    menu_key = db.Column(db.String(100), nullable=False, index=True)
    is_visible = db.Column(db.Boolean, nullable=False, default=False)
    source_type = db.Column(db.String(30), nullable=False, default="seed")
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("role_name", "menu_key", name="uq_role_menu_default_role_menu"),
    )

    def __repr__(self):
        return f"<RoleMenuDefault role={self.role_name} key={self.menu_key} visible={self.is_visible}>"


class SystemSetting(TimestampMixin, db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(120), nullable=False, unique=True, index=True)
    group_key = db.Column(db.String(50), nullable=False, default="general", index=True)
    label = db.Column(db.String(150), nullable=False)
    value_text = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), nullable=False, default="string")
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    def __repr__(self):
        return f"<SystemSetting key={self.setting_key} active={self.is_active}>"


class ModuleSetting(TimestampMixin, db.Model):
    __tablename__ = "module_settings"

    id = db.Column(db.Integer, primary_key=True)
    module_key = db.Column(db.String(60), nullable=False, index=True)
    setting_key = db.Column(db.String(120), nullable=False, index=True)
    label = db.Column(db.String(150), nullable=False)
    value_text = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), nullable=False, default="string")
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    __table_args__ = (
        db.UniqueConstraint("module_key", "setting_key", name="uq_module_setting_module_key"),
    )

    def __repr__(self):
        return f"<ModuleSetting module={self.module_key} key={self.setting_key} active={self.is_active}>"


class UnitMenuProfile(TimestampMixin, db.Model):
    __tablename__ = "unit_menu_profiles"

    id = db.Column(db.Integer, primary_key=True)
    unit_name = db.Column(db.String(150), nullable=False, index=True)
    menu_key = db.Column(db.String(100), nullable=False, index=True)
    is_visible = db.Column(db.Boolean, nullable=False, default=False)
    source_type = db.Column(db.String(30), nullable=False, default="manual")
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    note = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("unit_name", "menu_key", name="uq_unit_menu_profile_unit_menu"),
    )

    def __repr__(self):
        return f"<UnitMenuProfile unit={self.unit_name} key={self.menu_key} visible={self.is_visible}>"


class SettingsChangeLog(TimestampMixin, db.Model):
    __tablename__ = "settings_change_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_role_name = db.Column(db.String(50), nullable=True, index=True)
    target_unit_name = db.Column(db.String(150), nullable=True, index=True)
    change_scope = db.Column(db.String(50), nullable=False, index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    summary = db.Column(db.String(255), nullable=True)
    previous_state_json = db.Column(db.Text, nullable=True)
    new_state_json = db.Column(db.Text, nullable=True)
    reverted_from_log_id = db.Column(db.Integer, db.ForeignKey("settings_change_logs.id", ondelete="SET NULL"), nullable=True, index=True)
    is_rollback = db.Column(db.Boolean, nullable=False, default=False, index=True)

    actor = db.relationship("User", foreign_keys=[actor_user_id])
    target_user = db.relationship("User", foreign_keys=[target_user_id])
    reverted_from = db.relationship("SettingsChangeLog", remote_side=[id], foreign_keys=[reverted_from_log_id])

    def __repr__(self):
        return f"<SettingsChangeLog id={self.id} scope={self.change_scope} action={self.action_type}>"