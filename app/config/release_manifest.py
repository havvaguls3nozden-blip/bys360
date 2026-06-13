
"""BYS360 canlı kapsam ve son kabul manifesti.

Bu dosya Faz 6 ile birlikte canlıya çıkacak çekirdek yapıyı tek merkezde
okunur hale getirir. Çalışan sistemi değiştirmek için değil, son kabul
araçlarının aynı kapsamı konuşmasını sağlamak için tutulur.
"""
from __future__ import annotations

ACTIVE_LIVE_MODULES: tuple[str, ...] = (
    "dashboard",
    "personnel",
    "organization",
    "performance",
    "leave_delegation",
    "communication",
    "support",
    "account",
    "settings",
    "ai_center",
)

REMOVED_LIVE_MODULES: tuple[str, ...] = (
    "repository",
    "education",
    "strategy",
    "portal",
)

REQUIRED_CORE_ENDPOINTS: tuple[str, ...] = (
    "main.dashboard",
    "main.personnel_list",
    "main.admin_org_units",
    "main.performance_tasks",
    "main.performance_scorecard",
    "main.performance_criteria",
    "main.performance_periods",
    "main.performance_reports",
    "main.account",
    "main.settings_page",
    "main.logout",
)

OPTIONAL_LIVE_ENDPOINTS: tuple[str, ...] = (
    "main.messages_inbox",
    "main.announcements_list",
    "main.support_index",
    "main.admin_ai_center",
)

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/go_live/FAZ1_OVERLAY_NOTLARI.md",
    "docs/go_live/FAZ2_OVERLAY_NOTLARI.md",
    "docs/go_live/FAZ3_OVERLAY_NOTLARI.md",
    "docs/go_live/FAZ4_OVERLAY_NOTLARI.md",
    "docs/go_live/FAZ5_OVERLAY_NOTLARI.md",
)

REQUIRED_PHASE_CHECKS: tuple[str, ...] = (
    "scripts/check_live_scope_quarantine.py",
    "scripts/check_dashboard_report_surface.py",
    "scripts/check_phase4_rule_matrix.py",
    "scripts/check_phase5_security.py",
)

RECOMMENDED_ENV_KEYS: tuple[str, ...] = (
    "APP_ENV",
    "APP_BASE_URL",
    "SECRET_KEY",
    "DATABASE_URL",
    "DEFAULT_FIRST_LOGIN_PASSWORD",
    "TCKN_ENCRYPTION_KEY",
    "UPLOAD_FOLDER",
    "REPORT_FOLDER",
    "LOG_FOLDER",
    "BACKUP_ROOT",
    "SESSION_COOKIE_HTTPONLY",
    "SESSION_COOKIE_SAMESITE",
    "SESSION_COOKIE_SECURE",
    "REMEMBER_COOKIE_SECURE",
    "WTF_CSRF_TIME_LIMIT",
    "LOGIN_CAPTCHA_THRESHOLD",
)


def as_dict() -> dict[str, tuple[str, ...]]:
    return {
        "active_live_modules": ACTIVE_LIVE_MODULES,
        "removed_live_modules": REMOVED_LIVE_MODULES,
        "required_core_endpoints": REQUIRED_CORE_ENDPOINTS,
        "optional_live_endpoints": OPTIONAL_LIVE_ENDPOINTS,
        "required_docs": REQUIRED_DOCS,
        "required_phase_checks": REQUIRED_PHASE_CHECKS,
        "recommended_env_keys": RECOMMENDED_ENV_KEYS,
    }
