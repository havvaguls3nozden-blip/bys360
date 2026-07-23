"""BYS360 menu registry data bridge module.

Performans menü varsayılanları ve performans ana switch rol politikası.

Bu dosya P11-D2 kapsamında app/menu_registry.py içindeki büyük ve güvenli
top-level veri bloklarını aynı içerikle taşımak için oluşturulmuştur.
menu_key değerleri ve veri içerikleri değiştirilmemelidir.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

ROLE_MENU_DEFAULTS = {  # noqa: F821 - dynamic menu registry global
    "admin": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "my_performance_comparison",
        "performance_reports",
        "admin_users",
        "org_units",
        "performance_criteria",
        "performance_periods",
        "performance_period_management_center",
        "performance_evaluator_reminder_center",
        "performance_evaluation_tasks",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "performance_task_management",
        "performance_team_compare",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "performance_hierarchy_tree",
        "performance_hierarchy_assignments",
        "performance_publish",
                                        "messages",
        "notifications",
        "surveys",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "survey_manage",
        "survey_results",
        "announcements",
        "account",
        "settings",
        "db_check",
        "ai_center",
        "logout",        "performance_president_approvals",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",

},
    "baskan": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "my_performance_comparison",
        "performance_reports",
        "performance_period_management_center",
        "performance_evaluation_tasks",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "performance_team_compare",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "performance_hierarchy_tree",
                        "messages",
        "notifications",
        "surveys",
        "survey_manage",
        "survey_results",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",        "performance_president_approvals",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",

},
    "baskan_yardimcisi": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "my_performance_comparison",
        "performance_reports",
        "performance_period_management_center",
        "performance_evaluation_tasks",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "performance_team_compare",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "performance_hierarchy_tree",
                        "messages",
        "notifications",
        "surveys",
        "survey_manage",
        "survey_results",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",
},
    "grup_baskani": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "my_performance_comparison",
        "performance_reports",
        "performance_period_management_center",
        "performance_evaluation_tasks",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "performance_team_compare",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "performance_hierarchy_tree",
                        "messages",
        "notifications",
        "surveys",
        "survey_manage",
        "survey_results",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",
},
    "mali_musavir": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "my_performance_comparison",
        "performance_reports",
        "performance_period_management_center",
        "performance_evaluation_tasks",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "performance_team_compare",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "performance_hierarchy_tree",
                        "messages",
        "notifications",
        "surveys",
        "survey_manage",
        "survey_results",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",
},
    "birim_sorumlusu": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "my_performance_comparison",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "messages",
        "notifications",
        "surveys",
        "survey_manage",
        "survey_results",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",
        "performance_kpi_dashboard",
        "performance_competency_library",
        "performance_self_assessment",
},
    "koordinator": {

        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "performance_meeting_p3_reminders",
        "performance_interim_notes",
        "performance_development_guidance",
        "my_performance_comparison",
        "performance_feedback_meetings",
        "team_performance_comparison_history",
        "messages",
        "notifications",
        "surveys",
        "survey_manage",
        "survey_results",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",
        "performance_kpi_dashboard",
        "performance_kpi_management",
        "performance_competency_library",
        "performance_self_assessment",
        "performance_kpi_analysis",
},
    "personel": {
        "dashboard",
        "support_index",
        "support_new",
        "support_my_tickets",
        "support_assigned",
        "support_all",
        "performance_tasks",
        "performance_scorecard",
        "my_performance_comparison",
        "performance_feedback_meetings",
        "messages",
        "notifications",
        "surveys",
        "feedback_dashboard",
        "feedback_pulse",
        "feedback_campaigns",
        "feedback_results",
        "feedback_actions",
        "feedback_manager",
        "feedback_admin",
        "announcements",
        "account",
        "logout",
},
}

_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY = {
    'performance_module': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'performance_management': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'performans_yonetimi': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'performance_tasks': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_scorecard': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'scorecards': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'my_performance_comparison': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'performance_dashboard': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_reports': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_criteria': {'admin', 'baskan', 'baskan_yardimcisi'},
    'criteria': {'admin', 'baskan', 'baskan_yardimcisi'},
    'performance_periods': {'admin', 'baskan', 'baskan_yardimcisi'},
    'performance_period_management_center': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir'},
    'periods': {'admin', 'baskan', 'baskan_yardimcisi'},
    'performance_evaluation_tasks': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'assignments': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_task_management': {'admin'},
    'performance_hierarchy_tree': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_hierarchy_assignments': {'admin'},
    'performance_team_compare': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'team_analysis': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'team_performance_comparison_history': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_feedback_meetings': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'feedback_meetings': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_publish': {'admin', 'baskan'},
    'publish': {'admin', 'baskan'},
    'performance_process_tracking': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_process_reports': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_president_approvals': {'admin', 'baskan'},
    'performance_personnel_support_publish_approval': {'admin', 'grup_baskani'},
    'performance_archive': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'performance_interim_notes': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_development_guidance': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_meeting_p3_reminders': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_kpi_dashboard': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_kpi_management': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator'},
    'performance_competency_library': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'},
    'performance_self_assessment': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel'},
    'performance_kpi_analysis': {'admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator'},
    'performance_mail_settings': {'admin'},
    'performance_mail': {'admin'},
}

# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROLE_DEFAULTS_BEGIN
# Kurumsal Portal varsayılan rol yetkileri. DB seed eksik satırları bu statik varsayılanlardan tamamlar.
_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_ALL = {
    "portal_feed", "portal_people", "portal_profiles", "portal_post_create", "portal_wall_post",
    "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_groups",
}
_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGERS = set(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_ALL) | {"portal_group_create"}
_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MODERATORS = set(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGERS) | {"portal_moderation", "portal_press_news"}
_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGER_ROLES = {
    "admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu",
}
_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MODERATOR_ROLES = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}
for _role in ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]:
    _target = ROLE_MENU_DEFAULTS.setdefault(_role, set())  # noqa: F821 - dynamic menu registry global
    if _role in _BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MODERATOR_ROLES:
        _target.update(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MODERATORS)
    elif _role in _BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGER_ROLES:
        _target.update(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_MANAGERS)
    else:
        _target.update(_BYS360_PORTAL_ROLE_DEFAULTS_V2_12_ALL)
# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_ROLE_DEFAULTS_END


# BYS360_PERFORMANCE_V2_1_3A_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "super_admin", "system_admin", "sistem_yoneticisi"):
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("performance_personnel_category_card")  # noqa: F821 - dynamic menu registry global
except Exception:
    logger.exception("Performans modulu kritik isleminde hata olustu", exc_info=True)
    pass
# BYS360_PERFORMANCE_V2_1_3A_ROLE_DEFAULTS_END

# BYS360_PERFORMANCE_V2_1_3B_FORCE_PERSONNEL_CATEGORY_MENU_BEGIN
# V2.1.3B: Personel Kategori Atama menüsünü sol şerit registry tarafında emniyete alır.
try:
    _bys360_v213b_key = "performance_personnel_category_card"
    _bys360_v213b_item = {
        "key": _bys360_v213b_key,
        "label": "Personel Kategori Atama",
        "icon": "fa-solid fa-tags",
        "endpoint": "main.performance_v2_1_3_personnel_category_card",
        "active_endpoints": ["main.performance_v2_1_3_personnel_category_card", "performance_v2_1_3_personnel_category_card"],
        "active_path_prefixes": ["/performance/v2-1-3-personnel-category-card"],
        "url": "/performance/v2-1-3-personnel-category-card",
        "href": "/performance/v2-1-3-personnel-category-card",
        "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi"],
    }
    if "MENU_SECTIONS" in globals():
        _section_found = False
        for _section in MENU_SECTIONS:  # noqa: F821 - dynamic menu registry global
            _section_key = str((_section or {}).get("key") or "").lower()
            _section_label = str((_section or {}).get("label") or "").lower()
            if _section_key in {"performans", "performance", "performance_management"} or "performans" in _section_label:
                _items = _section.setdefault("items", [])
                if not any(((_item or {}).get("key") == _bys360_v213b_key) for _item in _items):
                    _items.append(dict(_bys360_v213b_item))
                _section_found = True
                break
        if not _section_found:
            MENU_SECTIONS.append({  # noqa: F821 - dynamic menu registry global
                "key": "performans",
                "label": "Performans Yönetimi",
                "icon": "fa-solid fa-chart-line",
                "items": [dict(_bys360_v213b_item)],
            })
    if "ROLE_MENU_DEFAULTS" in globals():
        for _role in ("admin", "super_admin", "system_admin", "sistem_yoneticisi"):
            _current = ROLE_MENU_DEFAULTS.setdefault(_role, set())  # noqa: F821 - dynamic menu registry global
            try:
                _current.add(_bys360_v213b_key)
            except AttributeError:
                if _bys360_v213b_key not in _current:
                    _current.append(_bys360_v213b_key)
    if "FORCE_VISIBLE_MENU_ROLES" in globals():
        FORCE_VISIBLE_MENU_ROLES.setdefault(_bys360_v213b_key, set()).update({"admin", "super_admin", "system_admin", "sistem_yoneticisi"})  # noqa: F821 - dynamic menu registry global
    if "LIVE_SETTINGS_MENU_KEYS" in globals():
        try:
            LIVE_SETTINGS_MENU_KEYS.add(_bys360_v213b_key)  # noqa: F821 - dynamic menu registry global
        except AttributeError:
            if _bys360_v213b_key not in LIVE_SETTINGS_MENU_KEYS:  # noqa: F821 - dynamic menu registry global
                LIVE_SETTINGS_MENU_KEYS.append(_bys360_v213b_key)  # noqa: F821 - dynamic menu registry global
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    import logging as _logging
    _logging.getLogger(__name__).exception("BYS360 V2.1.3B personel kategori menü görünürlük guard uygulanamadı")
# BYS360_PERFORMANCE_V2_1_3B_FORCE_PERSONNEL_CATEGORY_MENU_END

# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "super_admin", "system_admin", "sistem_yoneticisi"):
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("performance_category_scope_visibility")  # noqa: F821 - dynamic menu registry global
except Exception:
    logger.exception("Performans modulu kritik isleminde hata olustu", exc_info=True)
    pass
# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_ROLE_DEFAULTS_END

# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "super_admin", "system_admin", "sistem_yoneticisi"):
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("performance_category_period_scope")  # noqa: F821 - dynamic menu registry global
except Exception:
    logger.exception("Performans modulu kritik isleminde hata olustu", exc_info=True)
    pass
# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_ROLE_DEFAULTS_END

# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_DEFAULTS_BEGIN
# Dönem Yönetim Merkezi statik rol varsayılanına bağlıdır. DB satırı varsa son karar Ayarlar ekranındadır.
ROLE_MENU_DEFAULTS = globals().get("ROLE_MENU_DEFAULTS", {})  # noqa: F821 - dynamic menu registry global
for _role in ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir']:
    _keys = ROLE_MENU_DEFAULTS.setdefault(_role, set())  # noqa: F821 - dynamic menu registry global
    try:
        _keys.add("performance_period_management_center")
    except AttributeError:
        if "performance_period_management_center" not in _keys:
            _keys.append("performance_period_management_center")
try:
    _BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY.setdefault("performance_period_management_center", set()).update(['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir'])
except Exception:
    logger.exception("Performans modulu kritik isleminde hata olustu", exc_info=True)
    pass
# BYS360_PERFORMANCE_V2_1_21_PERIOD_CENTER_ROLE_MATRIX_DEFAULTS_END


# BYS360_PERFORMANCE_V2_1_23_SETTINGS_ROLE_MATRIX_FULL_BEGIN
# Dönem Yönetim Merkezi hattı Ayarlar > Rol Matrisi, rol varsayılanları,
# kişi bazlı menü görünürlüğü ve birim profili listelerinde eksiksiz yer alır.
ROLE_MENU_DEFAULTS = globals().get("ROLE_MENU_DEFAULTS", {})  # noqa: F821 - dynamic menu registry global
_BYS360_V223_PERIOD_CENTER_ROLE_DEFAULTS = {'baskan': ['performance_period_management_center', 'performance_evaluation_live_tracking', 'performance_evaluator_reminder_center'], 'baskan_yardimcisi': ['performance_period_management_center', 'performance_evaluation_live_tracking', 'performance_evaluator_reminder_center'], 'mali_musavir': ['performance_period_management_center', 'performance_evaluation_live_tracking', 'performance_evaluator_reminder_center'], 'grup_baskani': ['performance_period_management_center', 'performance_evaluation_live_tracking', 'performance_evaluator_reminder_center'], 'admin': ['performance_period_management_center', 'performance_evaluation_live_tracking', 'performance_evaluator_reminder_center'], 'koordinator': ['performance_evaluation_live_tracking', 'performance_evaluator_reminder_center'], 'birim_sorumlusu': ['performance_evaluation_live_tracking', 'performance_evaluator_reminder_center']}
for _role, _keys in _BYS360_V223_PERIOD_CENTER_ROLE_DEFAULTS.items():
    _target = ROLE_MENU_DEFAULTS.setdefault(_role, set())  # noqa: F821 - dynamic menu registry global
    for _key in _keys:
        try:
            _target.add(_key)
        except AttributeError:
            if _key not in _target:
                _target.append(_key)
_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY = globals().get(
    "_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY", {}
)
_BYS360_V223_KEY_ROLES = {'performance_period_management_center': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir'], 'performance_evaluation_live_tracking': ['admin', 'baskan', 'baskan_yardimcisi', 'birim_sorumlusu', 'grup_baskani', 'koordinator', 'mali_musavir'], 'performance_evaluator_reminder_center': ['admin', 'baskan', 'baskan_yardimcisi', 'birim_sorumlusu', 'grup_baskani', 'koordinator', 'mali_musavir']}
for _key, _roles in _BYS360_V223_KEY_ROLES.items():
    _target = _BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY.setdefault(_key, set())
    try:
        _target.update(_roles)
    except AttributeError:
        for _role in _roles:
            if _role not in _target:
                _target.append(_role)
# BYS360_PERFORMANCE_V2_1_23_SETTINGS_ROLE_MATRIX_FULL_END

# BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"):
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("portal_press_news")  # noqa: F821 - dynamic menu registry global
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_performance.py:543")
    pass
# BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_ROLE_DEFAULTS_END

# BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_ROLE_DEFAULTS_BEGIN
try:
    for _role in ("admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"):
        pass  # BYS360 V3B8A: boş blok syntax düzeltmesi
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_performance.py:551")
    pass
# BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_ROLE_DEFAULTS_END

# BYS360_PORTAL_EXPERIENCE_V3B8C_RESTORE_PORTAL_ROLE_DEFAULTS_BEGIN
try:
    _bys360_portal_v3b8c_keys = {
        "portal_feed", "portal_people", "portal_profiles", "portal_post_create",
        "portal_wall_post", "portal_post_interact", "portal_post_report",
        "portal_post_delete", "portal_groups", "portal_press_news",
    }
    _bys360_portal_v3b8c_manager_keys = set(_bys360_portal_v3b8c_keys) | {"portal_group_create"}
    _bys360_portal_v3b8c_moderator_keys = set(_bys360_portal_v3b8c_manager_keys) | {"portal_moderation"}
    _bys360_portal_v3b8c_manager_roles = {
        "admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi",
        "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu",
    }
    _bys360_portal_v3b8c_moderator_roles = {
        "admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi",
        "grup_baskani", "mali_musavir",
    }
    for _role in ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]:
        _target = ROLE_MENU_DEFAULTS.setdefault(_role, set())  # noqa: F821 - dynamic menu registry global
        if _role in _bys360_portal_v3b8c_moderator_roles:
            _target.update(_bys360_portal_v3b8c_moderator_keys)
        elif _role in _bys360_portal_v3b8c_manager_roles:
            _target.update(_bys360_portal_v3b8c_manager_keys)
        else:
            _target.update(_bys360_portal_v3b8c_keys)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_performance.py:580")
    pass
# BYS360_PORTAL_EXPERIENCE_V3B8C_RESTORE_PORTAL_ROLE_DEFAULTS_END

# Compatibility guard.
# Basında Tarihi Alan varsayılan menü yetkisi yalnızca admin/admin-benzeri teknik roldedir.
try:
    _bys360_press_news_admin_roles_v1 = {"admin", "super_admin", "system_admin", "sistem_yoneticisi"}
    for _role, _keys in list(ROLE_MENU_DEFAULTS.items()):  # noqa: F821 - dynamic menu registry global
        try:
            if _role in _bys360_press_news_admin_roles_v1:
                _keys.add("portal_press_news")
            else:
                _keys.discard("portal_press_news")
        except AttributeError:
            if _role in _bys360_press_news_admin_roles_v1:
                if "portal_press_news" not in _keys:
                    _keys.append("portal_press_news")
            else:
                while "portal_press_news" in _keys:
                    _keys.remove("portal_press_news")
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_performance.py:601")
    pass
# Compatibility guard.


# Compatibility guard.
try:
    for _role in ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"]:
        ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("portal_press_news")  # noqa: F821 - dynamic menu registry global
    for _role in ["baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"]:
        _target = ROLE_MENU_DEFAULTS.setdefault(_role, set())  # noqa: F821 - dynamic menu registry global
        try:
            _target.discard("portal_press_news")
        except AttributeError:
            while "portal_press_news" in _target:
                _target.remove("portal_press_news")
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_performance.py:617")
    pass
# Compatibility guard.
