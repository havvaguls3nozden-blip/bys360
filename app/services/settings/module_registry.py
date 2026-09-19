"""BYS360 Settings Center V2 -- module/menu metadata registry.

Single source of truth for "what modules/system services exist and what do
they look like from the Settings Center" -- module_key, display name, icon,
route, whether a Settings Center page exists for it yet, and a coarse
permission/security classification.

This is deliberately NOT a rewrite of the existing menu-visibility RESOLUTION
pipeline (app/menu_registry.py, app/services/settings/effective_menu.py and
its effective_menu_parts/ submodules). That pipeline already correctly
determines, per user, which menu_key is visible -- it has simply accreted
~15 sequential policy-wrapper functions over many past fixes, each guarding a
specific real regression. Rewriting it wholesale to "consolidate" it would
risk silently changing which real users can see which real menu items, with
no way to exhaustively verify that against production data from a dev
environment. This module instead builds an ADDITIVE metadata catalog on top
of the existing declarative menu data (app.menu_registry.MENU_SECTIONS via
get_grouped_menu_definitions()) and adds explicit module-level rows the
sidebar data does not carry (module_key, settings_endpoint, settings_available,
permission_category, security_level) -- the fields Settings Center V2 needs
to render "one card per active module" and to prove completeness (Phase 14
tests: no missing Settings Center, no orphan/duplicate keys).

`MODULE_REGISTRY` below was populated from a mechanical, evidence-based
inventory of the real source tree (route files, blueprints, existing settings
pages) done in three parallel research passes -- not invented from the
project's hint-list of expected module names. Every module_key here maps to
real, existing code; a hint-list name with no real corresponding code was
deliberately left out (e.g. there is no standalone "Raporlama" blueprint --
reporting is fragmented across performance/institutional/AI reporting
routes, so no reporting module_key is registered here).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Permission / security classification vocabulary (Phase 10 / Phase 4)
# ---------------------------------------------------------------------------

PERMISSION_CATEGORY_STANDARD = "standard"        # any authenticated user the menu resolver allows
PERMISSION_CATEGORY_MANAGER = "manager"          # manager-tier roles (birim_sorumlusu and above)
PERMISSION_CATEGORY_ADMIN_ONLY = "admin_only"    # admin/system-admin roles only
PERMISSION_CATEGORY_SYSTEM_CRITICAL = "system_critical"  # admin only, touches security/audit/config

SECURITY_LEVEL_PUBLIC = "public"          # no secrets, safe to describe broadly
SECURITY_LEVEL_INTERNAL = "internal"      # institutional data, not secret but not public
SECURITY_LEVEL_SENSITIVE = "sensitive"    # personal data (KVKK/TCKN) or security-relevant config
SECURITY_LEVEL_CRITICAL = "critical"      # secrets/credentials adjacent -- never rendered

MODULE_TYPE_BUSINESS = "business_module"
MODULE_TYPE_SYSTEM = "system_service"
MODULE_TYPE_CROSS_CUTTING = "cross_cutting_service"


@dataclass(frozen=True)
class ModuleRegistryEntry:
    module_key: str
    display_name: str
    module_type: str
    description: str
    icon: str
    order: int
    route_endpoint: str | None
    settings_endpoint: str | None
    active: bool
    settings_available: bool
    permission_category: str
    security_level: str
    anchor_menu_key: str | None = None
    evidence: str = ""
    parent_key: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# The registry itself. `settings_endpoint` values that reference a
# `*.module_settings_*` endpoint name are the NEW Settings Center V2 routes
# this same change introduces (see app/settings_center/routes.py); they do
# not exist before this commit. `settings_endpoint=None` + `settings_available
# =False` rows below are the confirmed gaps this project exists to close.
# ---------------------------------------------------------------------------

MODULE_REGISTRY: list[ModuleRegistryEntry] = [
    ModuleRegistryEntry(
        module_key="personnel_hr",
        display_name="Personel / İK",
        module_type=MODULE_TYPE_BUSINESS,
        description="Personel özlük dosyaları, birim ve pozisyon yönetimi, izin/devamsızlık.",
        icon="fa-solid fa-user-group",
        order=10,
        route_endpoint="main.admin_users",
        settings_endpoint="main.settings_center_personnel_hr",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_SENSITIVE,
        anchor_menu_key="admin_users",
        evidence="app/institutional/ (hr_personnel_*_routes.py, hr_leave_attendance_routes.py)",
    ),
    ModuleRegistryEntry(
        module_key="performance_mgmt",
        display_name="Performans Yönetimi",
        module_type=MODULE_TYPE_BUSINESS,
        description="Dönem, kriter, değerlendirme, hiyerarşi ve yayın yönetimi.",
        icon="fa-solid fa-chart-simple",
        order=20,
        route_endpoint="main.performance_tasks",
        settings_endpoint="main.performance_hierarchy_settings",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_MANAGER,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="performance_hierarchy_assignments",
        evidence="app/performance/routes.py, v2_1_1_rule_settings_routes.py, engagement_mail_routes.py",
    ),
    ModuleRegistryEntry(
        module_key="portal",
        display_name="Portal",
        module_type=MODULE_TYPE_BUSINESS,
        description="Kurumsal portal akışı, profiller, gruplar, basında tarihi alan, moderasyon.",
        icon="fa-solid fa-stream",
        order=30,
        route_endpoint="main.portal_feed",
        settings_endpoint="main.settings_center_portal",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="portal_moderation",
        evidence="app/portal/routes.py; gate app/config/removed_modules.py REMOVED_MODULES['portal']=False",
    ),
    ModuleRegistryEntry(
        module_key="file_center",
        display_name="Dosya Merkezi",
        module_type=MODULE_TYPE_BUSINESS,
        description="Dosya paylaşımı, rol matrisi, kota ve güvenlik kısıtları.",
        icon="fa-solid fa-folder-open",
        order=40,
        route_endpoint="main.file_center_settings",
        settings_endpoint="main.file_center_settings",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_SENSITIVE,
        anchor_menu_key=None,  # File Center has no left-sidebar MENU_SECTIONS entry; reached via its own nav, gated by can_manage_file_center_settings() instead
        evidence="app/file_center/routes.py:975 (/file-center/settings), settings_service.py",
    ),
    ModuleRegistryEntry(
        module_key="communication",
        display_name="İletişim",
        module_type=MODULE_TYPE_BUSINESS,
        description="Duyurular, mesajlar, geri bildirim; günlük bilgilendirme e-postası ayarları.",
        icon="fa-solid fa-comments",
        order=50,
        route_endpoint="main.messages_inbox",
        settings_endpoint="main.settings_center_communication",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="daily_weather_mail",
        evidence="app/communication/ (announcements_routes.py, daily_weather_mail_routes.py:160)",
    ),
    ModuleRegistryEntry(
        module_key="surveys",
        display_name="Anketler",
        module_type=MODULE_TYPE_BUSINESS,
        description="Anket oluşturma, atama, sonuç görünürlüğü.",
        icon="fa-solid fa-square-poll-vertical",
        order=60,
        route_endpoint="main.surveys_list",
        settings_endpoint="main.settings_center_surveys",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="survey_manage",
        evidence="app/communication/surveys_routes.py (15 routes on main_bp)",
    ),
    ModuleRegistryEntry(
        module_key="support_help",
        display_name="Destek / Yardım Merkezi",
        module_type=MODULE_TYPE_BUSINESS,
        description="Destek talepleri, yardım merkezi içeriği.",
        icon="fa-solid fa-headset",
        order=70,
        route_endpoint="main.support_index",
        settings_endpoint="main.settings_center_support",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="support_all",
        evidence="app/support/routes.py, app/support/help_center_content.py",
    ),
    ModuleRegistryEntry(
        module_key="ai_decision_support",
        display_name="AI Karar Destek",
        module_type=MODULE_TYPE_BUSINESS,
        description="AI kontrol merkezi, sağlayıcı/governance ayarları.",
        icon="fa-solid fa-brain",
        order=80,
        route_endpoint="main.admin_ai_center",
        settings_endpoint="main.admin_ai_settings",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_CRITICAL,
        anchor_menu_key="ai_center",
        evidence="app/admin/ai_phase2_routes.py:32, ai_phase8_routes.py:34 (secrets never rendered, see app/services/ai/client.py:215)",
    ),
    ModuleRegistryEntry(
        module_key="virtual_assistant",
        display_name="BYS360 Sanal Asistan",
        module_type=MODULE_TYPE_BUSINESS,
        description="Asistan panel/bilgi/öğretim erişimi ve rol matrisi.",
        icon="fa-solid fa-robot",
        order=90,
        route_endpoint="main.ai_agent_panel",
        settings_endpoint="main.settings_center_virtual_assistant",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="ai_agent_panel",
        evidence="app/ai_agent/routes.py (/panel,/knowledge,/teaching-center); role matrix app/services/assistant_role_matrix_v10.py:74",
    ),
    ModuleRegistryEntry(
        module_key="dashboard",
        display_name="Dashboard",
        module_type=MODULE_TYPE_BUSINESS,
        description="Ana panel widget ve gösterge görünürlüğü.",
        icon="fa-solid fa-chart-line",
        order=100,
        route_endpoint="main.dashboard",
        settings_endpoint="main.settings_center_dashboard",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="dashboard",
        evidence="app/dashboard/routes.py",
    ),
    ModuleRegistryEntry(
        module_key="settings_auth",
        display_name="Sistem Ayarları / Yetkilendirme",
        module_type=MODULE_TYPE_SYSTEM,
        description="Bu merkezin kendisi: rol matrisi, birim profilleri, kullanıcı yetkileri, audit.",
        icon="fa-solid fa-sliders",
        order=0,
        route_endpoint="main.settings_page",
        settings_endpoint="main.settings_page",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_SYSTEM_CRITICAL,
        security_level=SECURITY_LEVEL_SENSITIVE,
        anchor_menu_key="settings",
        evidence="app/account/routes.py:27 (settings_page), account_settings_helpers.py (1487-line functional hub)",
    ),
    ModuleRegistryEntry(
        module_key="notifications",
        display_name="Bildirimler",
        module_type=MODULE_TYPE_CROSS_CUTTING,
        description="Bildirim listesi, okunmamış sayaç, toplu işlemler.",
        icon="fa-regular fa-bell",
        order=110,
        route_endpoint="main.notifications_list",
        settings_endpoint="main.settings_center_notifications",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="notifications",
        evidence="app/communication/notifications_routes.py:358-407 (8 routes); config NOTIFICATION_UNREAD_CACHE_TTL",
    ),
    ModuleRegistryEntry(
        module_key="email_automation",
        display_name="E-posta Otomasyonları",
        module_type=MODULE_TYPE_CROSS_CUTTING,
        description="Günlük bilgilendirme e-postası ve performans hatırlatma e-postaları.",
        icon="fa-solid fa-envelope-circle-check",
        order=120,
        route_endpoint="main.daily_weather_mail_settings",
        settings_endpoint="main.daily_weather_mail_settings",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_ADMIN_ONLY,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key="daily_weather_mail",
        evidence="app/communication/daily_weather_mail_routes.py:160-163; performance/engagement_mail_routes.py:45",
    ),
    ModuleRegistryEntry(
        module_key="scheduled_jobs",
        display_name="Zamanlanmış İşler",
        module_type=MODULE_TYPE_CROSS_CUTTING,
        description="Geri bildirim takip zamanlayıcısı ve arka plan görev durumu (yalnız görüntüleme).",
        icon="fa-solid fa-clock-rotate-left",
        order=130,
        route_endpoint=None,
        settings_endpoint="main.settings_center_scheduled_jobs",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_SYSTEM_CRITICAL,
        security_level=SECURITY_LEVEL_INTERNAL,
        anchor_menu_key=None,
        evidence="app/services/performance/feedback_followup_scheduler.py:39, env BYS360_FEEDBACK_FOLLOWUP_SCHEDULER",
    ),
    ModuleRegistryEntry(
        module_key="security_session",
        display_name="Güvenlik / CAPTCHA / Oturum",
        module_type=MODULE_TYPE_CROSS_CUTTING,
        description="CAPTCHA eşiği, oturum süresi, giriş kısıtları -- durum görünümü (ortam değişkeni yönetimli).",
        icon="fa-solid fa-shield-halved",
        order=140,
        route_endpoint=None,
        settings_endpoint="main.settings_center_security",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_SYSTEM_CRITICAL,
        security_level=SECURITY_LEVEL_CRITICAL,
        anchor_menu_key=None,
        evidence="app/security/captcha_guard.py:66 CAPTCHA_ENABLED, config.py:630-640 LOGIN_* (env-only, no prior UI)",
    ),
    ModuleRegistryEntry(
        module_key="audit",
        display_name="Audit / Değişiklik Geçmişi",
        module_type=MODULE_TYPE_CROSS_CUTTING,
        description="Ayar değişiklik günlüğü, geri alma (rollback) desteği.",
        icon="fa-solid fa-clock-rotate-left",
        order=150,
        route_endpoint="main.settings_page",
        settings_endpoint="main.settings_page",
        active=True,
        settings_available=True,
        permission_category=PERMISSION_CATEGORY_SYSTEM_CRITICAL,
        security_level=SECURITY_LEVEL_SENSITIVE,
        anchor_menu_key="settings",
        evidence="app/models/settings_models.py:89 SettingsChangeLog; app/services/settings/change_logs.py",
    ),
]

_REMOVED_MODULE_KEYS = {"repository", "education", "strategy"}
"""Intentionally disabled per app/config/removed_modules.py REMOVED_MODULES --
never registered here, never surfaced as a settings gap."""


def get_module_registry() -> list[ModuleRegistryEntry]:
    return list(MODULE_REGISTRY)


def get_module(module_key: str) -> ModuleRegistryEntry | None:
    for entry in MODULE_REGISTRY:
        if entry.module_key == module_key:
            return entry
    return None


def list_active_modules() -> list[ModuleRegistryEntry]:
    return [entry for entry in MODULE_REGISTRY if entry.active]


def list_modules_missing_settings_center() -> list[ModuleRegistryEntry]:
    return [entry for entry in MODULE_REGISTRY if entry.active and not entry.settings_available]


def find_duplicate_module_keys() -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for entry in MODULE_REGISTRY:
        if entry.module_key in seen:
            duplicates.append(entry.module_key)
        seen.add(entry.module_key)
    return duplicates


def find_orphan_settings_endpoints() -> list[str]:
    """Module rows claiming settings_available=True but with no endpoint name at all."""
    return [
        entry.module_key
        for entry in MODULE_REGISTRY
        if entry.settings_available and not entry.settings_endpoint
    ]


__all__ = [
    "ModuleRegistryEntry",
    "MODULE_REGISTRY",
    "PERMISSION_CATEGORY_STANDARD",
    "PERMISSION_CATEGORY_MANAGER",
    "PERMISSION_CATEGORY_ADMIN_ONLY",
    "PERMISSION_CATEGORY_SYSTEM_CRITICAL",
    "SECURITY_LEVEL_PUBLIC",
    "SECURITY_LEVEL_INTERNAL",
    "SECURITY_LEVEL_SENSITIVE",
    "SECURITY_LEVEL_CRITICAL",
    "MODULE_TYPE_BUSINESS",
    "MODULE_TYPE_SYSTEM",
    "MODULE_TYPE_CROSS_CUTTING",
    "get_module_registry",
    "get_module",
    "list_active_modules",
    "list_modules_missing_settings_center",
    "find_duplicate_module_keys",
    "find_orphan_settings_endpoints",
]
