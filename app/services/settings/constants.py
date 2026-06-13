"""BYS360 Ayarlar Servisi pasif sabitleri.

Faz 1 notu:
- Bu paket canlı ayarlar davranışını değiştirmez.
- app/services/settings_service.py içine import eklenmez.
- Amaç, sonraki fazlarda güvenli parçalama için ortak isimleri sabitlemektir.
"""
from __future__ import annotations


SETTINGS_DOMAIN = "settings"
SYSTEM_SETTINGS_TABLE = "system_settings"
MODULE_SETTINGS_TABLE = "module_settings"
CHANGE_LOG_TABLE = "settings_change_logs"

PROTECTED_SETTING_KEYS = frozenset(
    {
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URI",
        "SECRET_KEY",
        "SESSION_COOKIE_SECURE",
        "REMEMBER_COOKIE_SECURE",
        "TCKN_ENCRYPTION_KEY",
        "DEFAULT_FIRST_LOGIN_PASSWORD",
        "MAIL_PASSWORD",
        "MAIL_USERNAME",
    }
)

BOOLEAN_TRUE_VALUES = frozenset({"1", "true", "on", "yes", "evet", "aktif", "enabled"})
BOOLEAN_FALSE_VALUES = frozenset({"0", "false", "off", "no", "hayır", "hayir", "pasif", "disabled"})

MENU_SCOPE_KEYS = frozenset(
    {
        "user_menu_permissions",
        "role_menu_defaults",
        "unit_menu_profiles",
    }
)

AUDIT_REQUIRED_OPERATIONS = frozenset(
    {
        "read",
        "create",
        "update",
        "delete",
        "enable",
        "disable",
        "reset",
        "bulk_update",
    }
)
