from __future__ import annotations

from app import create_app
from app.extensions import db
from app.models import (
    ModuleSetting,
    PortalActivityLog,
    PortalCommentReaction,
    PortalGroup,
    PortalGroupMember,
    PortalModerationLog,
    PortalPinnedPost,
    PortalPost,
    PortalPostAttachment,
    PortalPostAudience,
    PortalPostComment,
    PortalPostReaction,
    PortalPostReport,
    PortalProfile,
    PortalSavedPost,
    RoleMenuDefault,
)

ALL_ROLES = ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]
MANAGER_ROLES = ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"]
MENU_KEYS = {
    "portal_feed": ALL_ROLES,
    "portal_profiles": ALL_ROLES,
    "portal_groups": ALL_ROLES,
    "portal_moderation": MANAGER_ROLES,
}
TABLES = [
    PortalProfile.__table__,
    PortalGroup.__table__,
    PortalGroupMember.__table__,
    PortalPost.__table__,
    PortalPostAudience.__table__,
    PortalPostAttachment.__table__,
    PortalPostReaction.__table__,
    PortalPostComment.__table__,
    PortalCommentReaction.__table__,
    PortalSavedPost.__table__,
    PortalPostReport.__table__,
    PortalModerationLog.__table__,
    PortalPinnedPost.__table__,
    PortalActivityLog.__table__,
]


def upsert_role_menu(role_name: str, menu_key: str, visible: bool) -> None:
    row = RoleMenuDefault.query.filter_by(role_name=role_name, menu_key=menu_key).first()
    if row is None:
        db.session.add(RoleMenuDefault(role_name=role_name, menu_key=menu_key, is_visible=visible, source_type="seed", note="BYS360 Kurumsal Portal V1"))
        return
    row.is_visible = visible
    row.source_type = row.source_type or "seed"
    row.note = "BYS360 Kurumsal Portal V1"


def upsert_module_setting(key: str, label: str, value: str, value_type: str = "string", description: str = "") -> None:
    row = ModuleSetting.query.filter_by(module_key="corporate_portal", setting_key=key).first()
    if row is None:
        db.session.add(ModuleSetting(module_key="corporate_portal", setting_key=key, label=label, value_text=value, value_type=value_type, description=description, is_active=True))
        return
    row.label = label
    row.value_text = value
    row.value_type = value_type
    row.description = description
    row.is_active = True


def main() -> int:
    app = create_app()
    with app.app_context():
        # Flask-SQLAlchemy surumleri arasinda db.create_all(tables=...) imzasi degisebildigi icin
        # portal tablolarini SQLAlchemy Table.create ile tek tek ve checkfirst=True olarak olusturuyoruz.
        for table in TABLES:
            table.create(bind=db.engine, checkfirst=True)
        for menu_key, visible_roles in MENU_KEYS.items():
            for role in ALL_ROLES:
                upsert_role_menu(role, menu_key, role in visible_roles)
        upsert_module_setting("enabled", "Kurumsal Portal Aktif", "true", "boolean", "Yayın akışı ve portal profillerini etkinleştirir.")
        upsert_module_setting("default_visibility", "Varsayılan Paylaşım Görünürlüğü", "public", "string", "Yeni paylaşımlarda varsayılan görünürlük kapsamı.")
        upsert_module_setting("allow_comments", "Yorumlar Aktif", "true", "boolean", "Portal paylaşımlarında yorum alanını etkinleştirir.")
        upsert_module_setting("allow_reactions", "Tepkiler Aktif", "true", "boolean", "Beğendim, tebrik, üzüldüm gibi geri bildirimleri etkinleştirir.")
        upsert_module_setting("moderation_required_for_social_groups", "Sosyal Grup Onayı", "true", "boolean", "Sosyal/ilgi grubu oluşturma süreçlerinde onay yaklaşımını tanımlar.")
        db.session.commit()
    print("BYS360_CORPORATE_PORTAL_V1_DB_APPLY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
