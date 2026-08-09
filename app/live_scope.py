
"""Canlı kapsam filtreleri.

Ayarlar ekranında yalnızca canlıda kalan BYS360 omurgasının görünmesini sağlar.
Pasif / kademeli modüller veri katmanında kalabilir; ancak canlı yönetim
arayüzünde varsayılan olarak gösterilmez.
"""
from __future__ import annotations

LIVE_SETTINGS_MENU_KEYS: set[str] = {  # noqa: F821 - dynamic menu registry global
    # Genel
    "dashboard",
    "notifications",
    "announcements",
    "support_index",
    "support_new",
    "support_my_tickets",
    "support_assigned",
    "support_all",
    "about_bys360",

    # Kimlik, kullanıcı, yetki ve ayarlar
    "admin_users",
    "org_units",
    "account",
    "settings",
    "db_check",
    "logout",

    # Personel yönetimi

    # Performans yönetimi
    "performance_scorecard",
    "performance_reports",
    "performance_tasks",
    "performance_criteria",
    "performance_periods",
    "performance_evaluation_tasks",
    "performance_task_management",
    "performance_hierarchy_tree",
    "performance_hierarchy_assignments",
    "performance_team_compare",
    "performance_feedback_meetings",
    "performance_publish",
    "performance_president_approvals",
    "performance_history_import",
    "team_performance_comparison_history",
    # BYS360_PERFORMANCE_V2_1_3A_LIVE_SCOPE_MENU_KEY
    "performance_personnel_category_card",
    # BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_LIVE_SCOPE_MENU_KEY
    "performance_category_scope_visibility",

    # Stratejik Performans — KPI, Hedef, Yetkinlik, Öz Değerlendirme
    "performance_kpi_dashboard",
    "performance_kpi_management",
    "performance_competency_library",
    "performance_self_assessment",
    "performance_kpi_analysis",

    # İletişim, anket ve geri bildirim
    "messages",
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

    # Sanal asistan
    "assistant_center",
    "assistant_my_reminders",
    "assistant_scheduled_tasks",
    "assistant_report_generate",
    "assistant_report_share",
    "assistant_ai_summary",
    "assistant_process_alerts",
    "assistant_logs",
    "assistant_settings",

    # AI karar destek merkezi
    "ai_center",
}

LIVE_SETTINGS_MODULE_KEYS: set[str] = {
    # Kimlik, kullanıcı, yetki ve genel görünüm
    "identity_access",
    "support_center",

    # Personel ve izin/vekâlet
    "personnel_management",
    "leave_delegation",

    # Performans
    "performance_core",
    "performance_scoring",
    "performance_flow",
    "performance_period",
    "performance_feedback",
    "reporting_analytics",

    # İletişim, anket ve geri bildirim
    "communication_messaging",
    "survey_management",
    "feedback_pulse",
    "feedback_campaign",

    # AI ve otomasyon
    "ai_decision_support",
    "mail_automation",
    "assistant",
}


def is_live_settings_menu_key(menu_key: str | None) -> bool:
    return (menu_key or "").strip() in LIVE_SETTINGS_MENU_KEYS  # noqa: F821 - dynamic menu registry global


def is_live_settings_module_key(module_key: str | None) -> bool:
    return (module_key or "").strip() in LIVE_SETTINGS_MODULE_KEYS

# Faz 8 - Canlı kapsam görünürlük anahtarı
PERFORMANCE_PROCESS_TRACKING_SCOPE_KEY = 'performance_process_tracking'
# BYS360 Faz 10 görünürlük anahtarı: performance_process_reports

# BYS360_PRESIDENT_MENU_CARD_HISTORY_STATUS_FINAL_V1

# BYS360_SETTINGS_MANUAL_V1_LIVE_SCOPE_BEGIN
_BYS360_MANUAL_MENU_KEYS = ['performance_meeting_p3_reminders', 'performance_interim_notes', 'performance_development_guidance', 'performance_archive', 'performance_process_tracking', 'performance_process_reports', 'performance_personnel_support_publish_approval']
_BYS360_MANUAL_MODULE_KEYS = ['performance_archive', 'performance_category', 'performance_process', 'performance_reminders', 'performance_development', 'performance_interim_notes', 'performance_visibility']

for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS"]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_MANUAL_MENU_KEYS)
    elif isinstance(_value, list):
        _value.extend([_k for _k in _BYS360_MANUAL_MENU_KEYS if _k not in _value])

for _name in ["LIVE_SETTINGS_MODULE_KEYS", "LIVE_ALLOWED_MODULE_KEYS", "LIVE_MODULE_KEYS", "LIVE_PERFORMANCE_MODULE_KEYS"]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_MANUAL_MODULE_KEYS)
    elif isinstance(_value, list):
        _value.extend([_k for _k in _BYS360_MANUAL_MODULE_KEYS if _k not in _value])
# BYS360_SETTINGS_MANUAL_V1_LIVE_SCOPE_END

# BYS360_PROCESS_TRACKING_REPORTS_LIVE_SCOPE_V1_BEGIN
_BYS360_PROCESS_MENU_KEYS = ['performance_process_tracking', 'performance_process_reports']

for _name in [
    "LIVE_SETTINGS_MENU_KEYS",
    "LIVE_ALLOWED_MENU_KEYS",
    "LIVE_MENU_KEYS",
    "LIVE_PERFORMANCE_MENU_KEYS",
]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_PROCESS_MENU_KEYS)
    elif isinstance(_value, list):
        _value.extend([_k for _k in _BYS360_PROCESS_MENU_KEYS if _k not in _value])
# BYS360_PROCESS_TRACKING_REPORTS_LIVE_SCOPE_V1_END

# BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TABS_V1_LIVE_SCOPE_BEGIN
_BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_KEYS = ['performance_process_tracking', 'performance_process_reports', 'performance_interim_notes', 'performance_development_guidance', 'performance_meeting_p3_reminders', 'performance_archive', 'performance_personnel_support_publish_approval', 'performance_president_approvals']

for _name in [
    "LIVE_SETTINGS_MENU_KEYS",
    "LIVE_ALLOWED_MENU_KEYS",
    "LIVE_MENU_KEYS",
    "LIVE_PERFORMANCE_MENU_KEYS",
    "PERFORMANCE_ROLE_MATRIX_KEYS",
]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_KEYS)
    elif isinstance(_value, list):
        _value.extend([_k for _k in _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_KEYS if _k not in _value])
# BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TABS_V1_LIVE_SCOPE_END


# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_LIVE_SCOPE_BEGIN
_BYS360_ROLE_MATRIX_V12_MENU_KEYS = {
    "support_index", "support_new", "support_my_tickets", "support_assigned", "support_all",
    "performance_process_tracking", "performance_process_reports", "performance_personnel_support_publish_approval",
    "performance_president_approvals", "performance_archive", "performance_interim_notes", "performance_development_guidance", "performance_meeting_p3_reminders",
    "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
    "assistant_performance_guidance", "assistant_president_approval_guidance", "assistant_publish_preapproval_guidance",
    "assistant_interim_notes_guidance", "assistant_development_guidance", "assistant_archive_guidance",
    "assistant_process_alerts", "assistant_my_reminders", "assistant_scheduled_tasks", "assistant_report_generate",
    "assistant_report_share", "assistant_ai_summary", "assistant_logs", "assistant_settings",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS"]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_ROLE_MATRIX_V12_MENU_KEYS)
    elif isinstance(_value, list):
        _value.extend([_key for _key in _BYS360_ROLE_MATRIX_V12_MENU_KEYS if _key not in _value])
# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_LIVE_SCOPE_END


# BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1_LIVE_SCOPE_BEGIN
# Personel Yönetimi canlı kapsamında yalnızca izin/devamsızlık/vekâlet anahtarı tutulur.
_BYS360_PERSONEL_ALLOWED_LIVE_KEYS = {"hr_leave_tracking"}
_BYS360_PERSONEL_DISALLOWED_LIVE_KEYS = {
    "hr_management",
    "hr_reports",
    "hr_personnel_operations",
    "hr_career_planning",
    "hr_reward_discipline",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.difference_update(_BYS360_PERSONEL_DISALLOWED_LIVE_KEYS)
        _target.update(_BYS360_PERSONEL_ALLOWED_LIVE_KEYS)
    elif isinstance(_target, list):
        _target[:] = [_key for _key in _target if _key not in _BYS360_PERSONEL_DISALLOWED_LIVE_KEYS]
        _target.extend([_key for _key in _BYS360_PERSONEL_ALLOWED_LIVE_KEYS if _key not in _target])
# BYS360_PERSONEL_LIVE_SCOPE_NARROW_V1_LIVE_SCOPE_END

# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_LIVE_SCOPE_BEGIN
# Güncel canlı personel rol matrisi yalnızca bu üç anahtarı görünür kapsamda tutar.
_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_MENU_KEYS = {"admin_users", "org_units", "hr_leave_tracking"}
_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_BLOCKED_MENU_KEYS = {
    "hr_management", "hr_reports", "hr_personnel_operations", "hr_career_planning", "hr_reward_discipline",
    "personnel_dashboard", "personnel_create", "personnel_edit", "organization_unit_versions", "hierarchy",
    "leave", "attendance", "delegation", "personnel_reports",
    "personnel_requests", "personnel_validity", "personnel_assets", "personnel_checklists",
    "personnel_reminders", "personnel_lifecycle", "personnel_handover", "personnel_approvals",
    "personnel_request_analytics", "personnel_request_tasks",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS"]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_MENU_KEYS)
        _value.difference_update(_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_BLOCKED_MENU_KEYS)
    elif isinstance(_value, list):
        _value[:] = [key for key in _value if key not in _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_BLOCKED_MENU_KEYS]
        _value.extend([key for key in _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_MENU_KEYS if key not in _value])
# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_LIVE_SCOPE_END

# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_BEGIN
# Ayarlar ve rol matrisi canlı kapsamı tek merkezden güncellendi.
# Bu listeye giren her sekme Ayarlar > Modül Bazlı Rol Matrisleri içinde açılıp kapatılabilir.
_BYS360_ALL_MENU_ROLE_MATRIX_LIVE_KEYS = {'home', 'dashboard', 'notifications', 'announcements', 'account', 'settings', 'db_check', 'logout', 'support_index', 'support_new', 'support_my_tickets', 'support_assigned', 'support_all', 'support_help_admin', 'admin_users', 'org_units', 'hr_leave_tracking', 'performance_scorecard', 'my_performance_comparison', 'performance_reports', 'performance_tasks', 'performance_criteria', 'performance_periods', 'performance_evaluation_tasks', 'performance_task_management', 'performance_hierarchy_tree', 'performance_hierarchy_assignments', 'performance_team_compare', 'team_performance_comparison_history', 'performance_feedback_meetings', 'performance_publish', 'performance_president_approvals', 'performance_personnel_support_publish_approval', 'performance_process_tracking', 'performance_process_reports', 'performance_interim_notes', 'performance_development_guidance', 'performance_meeting_p3_reminders', 'performance_archive', 'performance_history_import', 'performance_mail_settings', 'performance_kpi_dashboard', 'performance_kpi_management', 'performance_competency_library', 'performance_self_assessment', 'performance_kpi_analysis', 'messages', 'surveys', 'survey_manage', 'survey_results', 'feedback_dashboard', 'feedback_pulse', 'feedback_campaigns', 'feedback_results', 'feedback_actions', 'feedback_manager', 'feedback_admin', 'ai_center', 'ai_agent_panel', 'ai_teaching_center', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_president_approval_guidance', 'assistant_publish_preapproval_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_archive_guidance', 'assistant_process_alerts', 'assistant_my_reminders', 'assistant_scheduled_tasks', 'assistant_report_generate', 'assistant_report_share', 'assistant_ai_summary', 'assistant_logs', 'assistant_settings'}
_BYS360_ALL_MENU_ROLE_MATRIX_MODULE_KEYS = {
    "identity_access", "support_center", "personnel_management", "leave_delegation",
    "performance_core", "performance_scoring", "performance_flow", "performance_period",
    "performance_feedback", "performance_process", "performance_archive", "performance_category",
    "performance_reminders", "performance_development", "performance_interim_notes",
    "performance_visibility", "strategic_performance", "communication_messaging",
    "survey_management", "feedback_pulse", "feedback_campaign", "ai_decision_support",
    "mail_automation", "assistant", "settings_security",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_ALL_MENU_ROLE_MATRIX_LIVE_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_ALL_MENU_ROLE_MATRIX_LIVE_KEYS if _key not in _target])
for _name in ["LIVE_SETTINGS_MODULE_KEYS", "LIVE_ALLOWED_MODULE_KEYS", "LIVE_MODULE_KEYS", "LIVE_PERFORMANCE_MODULE_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_ALL_MENU_ROLE_MATRIX_MODULE_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_ALL_MENU_ROLE_MATRIX_MODULE_KEYS if _key not in _target])
# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_END

# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_BEGIN
# BYS360 Asistanı gerçek sekmeleri canlı ayar/rol matrisi kapsamına eklendi.
_BYS360_ASSISTANT_TABS_ROLE_MATRIX_KEYS = {'assistant_module', 'ai_agent_panel', 'ai_agent_knowledge', 'ai_agent_teaching_center', 'ai_teaching_center', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_president_approval_guidance', 'assistant_publish_preapproval_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_archive_guidance', 'assistant_process_alerts', 'assistant_my_reminders', 'assistant_scheduled_tasks', 'assistant_report_generate', 'assistant_report_share', 'assistant_ai_summary', 'assistant_logs', 'assistant_settings'}
_BYS360_ASSISTANT_TABS_MODULE_KEYS = {"assistant", "ai_agent", "assistant_knowledge", "assistant_teaching"}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_ASSISTANT_TABS_ROLE_MATRIX_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_ASSISTANT_TABS_ROLE_MATRIX_KEYS if _key not in _target])
for _name in ["LIVE_SETTINGS_MODULE_KEYS", "LIVE_ALLOWED_MODULE_KEYS", "LIVE_MODULE_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_ASSISTANT_TABS_MODULE_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_ASSISTANT_TABS_MODULE_KEYS if _key not in _target])
# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_END

# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_BEGIN
# Performans Yönetimi ana anahtarı ve güncel sekmeler canlı kapsam anahtarlarına dahil edildi.
_BYS360_PERFORMANCE_MAIN_SWITCH_LIVE_KEYS = {'performance_module', 'performance_management', 'performans_yonetimi', 'performance_tasks', 'performance_scorecard', 'scorecards', 'my_performance_comparison', 'performance_dashboard', 'performance_reports', 'performance_criteria', 'criteria', 'performance_periods', 'periods', 'performance_evaluation_tasks', 'assignments', 'performance_task_management', 'performance_hierarchy_tree', 'performance_hierarchy_assignments', 'performance_team_compare', 'team_analysis', 'team_performance_comparison_history', 'performance_feedback_meetings', 'feedback_meetings', 'performance_publish', 'publish', 'performance_mail_settings', 'performance_mail', 'performance_process_tracking', 'performance_process_reports', 'performance_president_approvals', 'performance_personnel_support_publish_approval', 'performance_archive', 'performance_interim_notes', 'performance_development_guidance', 'performance_meeting_p3_reminders', 'performance_kpi_dashboard', 'performance_kpi_management', 'performance_competency_library', 'performance_self_assessment', 'performance_kpi_analysis'}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PERFORMANCE_MAIN_SWITCH_LIVE_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_PERFORMANCE_MAIN_SWITCH_LIVE_KEYS if _key not in _target])
# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_END

# BYS360_GENERAL_SECTION_RESTORE_V4_BEGIN
# Genel bölüm ve çekirdek menü anahtarları canlı kapsamda kalır.
_BYS360_GENERAL_CORE_KEYS_V4 = {'general_section', 'home', 'dashboard', 'notifications', 'support_index', 'support_new', 'support_my_tickets'}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "GENERAL_MENU_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_GENERAL_CORE_KEYS_V4)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_GENERAL_CORE_KEYS_V4 if _key not in _target])
# BYS360_GENERAL_SECTION_RESTORE_V4_END

# BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_BEGIN
# Personel Yönetimi rol matrisi canlı kapsam düzeltmesi.
# Seçili personel sekmeleri artık canlı kapsam filtresinde düşürülmez.
_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS = {"admin_users", "org_units", "hr_management", "hr_leave_tracking", "hr_reports"}
_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS = {
    "hr_personnel_operations", "hr_career_planning", "hr_reward_discipline",
    "personnel_dashboard", "personnel_create", "personnel_edit", "organization_unit_versions", "hierarchy",
    "leave", "attendance", "delegation", "personnel_reports",
    "personnel_requests", "personnel_validity", "personnel_assets", "personnel_checklists",
    "personnel_reminders", "personnel_lifecycle", "personnel_handover", "personnel_approvals",
    "personnel_request_analytics", "personnel_request_tasks",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS)
        _target.difference_update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS)
    elif isinstance(_target, list):
        _target[:] = [_key for _key in _target if _key not in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS]
        _target.extend([_key for _key in _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS if _key not in _target])
try:
    _BYS360_PERSONEL_DISALLOWED_LIVE_KEYS.difference_update({"hr_management", "hr_reports"})
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_BLOCKED_MENU_KEYS.difference_update({"hr_management", "hr_reports"})
    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_MENU_KEYS.update(_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/live_scope.py)")
# BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_END

# BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_BEGIN
# Güncel Performans Yönetimi sol menü ve rol matrisi anahtarları canlı ayar kapsamına eklendi.
_BYS360_PERF_RM_V8_LIVE_KEYS = {
    "performance_module", "performance_management", "performans_yonetimi",
    "performance_tasks", "performance_scorecard", "scorecards", "my_performance_comparison",
    "performance_dashboard", "performance_reports", "performance_archive",
    "performance_criteria", "criteria", "performance_periods", "periods",
    "performance_evaluation_tasks", "assignments", "performance_task_management",
    "performance_hierarchy_tree", "performance_hierarchy_assignments", "performance_team_compare", "team_analysis",
    "team_performance_comparison_history", "performance_feedback_meetings", "feedback_meetings",
    "performance_publish", "publish", "performance_mail_settings", "performance_mail",
    "performance_process_tracking", "performance_process_reports", "performance_president_approvals",
    "performance_personnel_support_publish_approval", "performance_interim_notes", "performance_development_guidance",
    "performance_meeting_p3_reminders", "performance_feedback_aftercare", "performance_feedback_aftercare_new",
    "performance_feedback_meeting_guide", "performance_feedback_followup",
    "performance_kpi_dashboard", "performance_kpi_management", "performance_competency_library",
    "performance_self_assessment", "performance_kpi_analysis", "performance_history_import",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PERF_RM_V8_LIVE_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_PERF_RM_V8_LIVE_KEYS if _key not in _target])
# BYS360_PERFORMANCE_ROLE_MATRIX_PERSONNEL_V8_END

# BYS360_SETTINGS_ROLE_MATRIX_ALL_FEATURES_FINAL_FIX_V1_BEGIN
# Ayarlar ve rol matrisi ekranlarının canlı kapsam filtresine sonradan eklenen
# gerçek/sentetik sekme anahtarları dahil edilir. Kapsam dışı eski modüller açılmaz;
# yalnızca mevcut sol menü ve rol matrisi anahtarları güvenli şekilde yönetilir.
LIVE_SETTINGS_MENU_KEYS.update({  # noqa: F821 - dynamic menu registry global
    "general_section", "home",
    "performance_module", "performance_management", "performans_yonetimi",
    "performance_dashboard", "my_performance_comparison", "performance_archive",
    "performance_process_tracking", "performance_process_reports",
    "performance_personnel_support_publish_approval",
    "performance_interim_notes", "performance_development_guidance",
    "performance_meeting_p3_reminders",
    "performance_feedback_aftercare", "performance_feedback_aftercare_new",
    "performance_feedback_meeting_guide", "performance_feedback_followup",
    "performance_mail_settings", "performance_mail",
    "scorecards", "criteria", "periods", "assignments", "publish", "team_analysis",
    "hr_management", "hr_reports", "hr_leave_tracking",
    "support_help_admin", "feedback_meetings",
    "assistant_module", "ai_agent_panel", "ai_agent_knowledge", "ai_agent_teaching_center", "ai_teaching_center",
    "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
    "assistant_performance_guidance", "assistant_president_approval_guidance",
    "assistant_publish_preapproval_guidance", "assistant_interim_notes_guidance",
    "assistant_development_guidance", "assistant_archive_guidance",
    "analysis_center", "ai_decision_support",
})
# BYS360_SETTINGS_ROLE_MATRIX_ALL_FEATURES_FINAL_FIX_V1_END

# BYS360_GENERAL_CATEGORY_VISIBILITY_FIX_V1_BEGIN
# Genel kategori anahtarlarini canli ayar/rol matrisi kapsaminda tut.
_BYS360_GENERAL_CATEGORY_LIVE_KEYS_V1 = {"general_section", "genel", "general", "home", "dashboard", "notifications", "support_index", "support_new", "support_my_tickets"}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "GENERAL_MENU_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_GENERAL_CATEGORY_LIVE_KEYS_V1)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_GENERAL_CATEGORY_LIVE_KEYS_V1 if _key not in _target])
# BYS360_GENERAL_CATEGORY_VISIBILITY_FIX_V1_END

# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_LIVE_SCOPE_BEGIN
# Kurumsal Portal ve portal işlem yetkileri Ayarlar > Rol Matrisi ve kişi bazlı rol matrisi kapsamına alındı.
_BYS360_PORTAL_ROLE_MATRIX_V2_12_KEYS = {
    "portal_feed", "portal_people", "portal_profiles", "portal_post_create", "portal_wall_post",
    "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_groups",
    "portal_group_create", "portal_moderation",
}
for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "GENERAL_MENU_KEYS"]:
    _target = globals().get(_name)
    if isinstance(_target, set):
        _target.update(_BYS360_PORTAL_ROLE_MATRIX_V2_12_KEYS)
    elif isinstance(_target, list):
        _target.extend([_key for _key in _BYS360_PORTAL_ROLE_MATRIX_V2_12_KEYS if _key not in _target])
# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_LIVE_SCOPE_END

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
    import logging as _logging
    _logging.getLogger(__name__).exception("BYS360 V2.1.3B personel kategori menü görünürlük guard uygulanamadı")
# BYS360_PERFORMANCE_V2_1_3B_FORCE_PERSONNEL_CATEGORY_MENU_END

# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_MENU_BEGIN
try:
    _bys360_v215_item = {"key":"performance_category_period_scope","label":"Kategori Dönem Kapsamı","endpoint":"main.performance_v2_1_5_category_period_scope","url":"/performance/v2-1-5-category-period-scope","icon":"fa-calendar-check"}
    if "MENU_SECTIONS" in globals():
        _perf = next((_section for _section in MENU_SECTIONS if isinstance(_section, dict) and (_section.get("key") == "performans" or _section.get("label") == "Performans Yönetimi")), None)  # noqa: F821 - dynamic menu registry global
        if _perf is None:
            _perf = {"key": "performans", "label": "Performans Yönetimi", "icon": "fa-solid fa-chart-line", "items": []}
            MENU_SECTIONS.append(_perf)  # noqa: F821 - dynamic menu registry global
        _items = _perf.setdefault("items", [])
        if not any(isinstance(_i, dict) and _i.get("key") == "performance_category_period_scope" for _i in _items):
            _items.append(dict(_bys360_v215_item))
    if "ROLE_MENU_DEFAULTS" in globals():
        for _role in ("admin", "super_admin", "system_admin", "sistem_yoneticisi"):
            ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("performance_category_period_scope")  # noqa: F821 - dynamic menu registry global
    if "LIVE_MENU_SCOPE" in globals():
        try:
            LIVE_MENU_SCOPE.add("performance_category_period_scope")  # noqa: F821 - dynamic menu registry global
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/live_scope.py:489")
            pass
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/live_scope.py:490")
    pass
# BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_MENU_END

# BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_MENU_BEGIN
try:
    _bys360_v216_item = {"key":"performance_category_period_integration","label":"Kategori Dönem Entegrasyonu","endpoint":"main.performance_v2_1_6_category_period_integration","url":"/performance/v2-1-6-category-period-integration","icon":"fa-link"}
    if "MENU_SECTIONS" in globals():
        _perf = next((_section for _section in MENU_SECTIONS if isinstance(_section, dict) and (_section.get("key") == "performans" or _section.get("label") == "Performans Yönetimi")), None)  # noqa: F821 - dynamic menu registry global
        if _perf is None:
            _perf = {"key": "performans", "label": "Performans Yönetimi", "icon": "fa-solid fa-chart-line", "items": []}
            MENU_SECTIONS.append(_perf)  # noqa: F821 - dynamic menu registry global
        _items = _perf.setdefault("items", [])
        if not any(isinstance(_i, dict) and _i.get("key") == "performance_category_period_integration" for _i in _items):
            _items.append(dict(_bys360_v216_item))
    if "ROLE_MENU_DEFAULTS" in globals():
        for _role in ("admin", "super_admin", "system_admin", "sistem_yoneticisi"):
            ROLE_MENU_DEFAULTS.setdefault(_role, set()).add("performance_category_period_integration")  # noqa: F821 - dynamic menu registry global
    if "LIVE_MENU_SCOPE" in globals():
        try:
            LIVE_MENU_SCOPE.add("performance_category_period_integration")  # noqa: F821 - dynamic menu registry global
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/live_scope.py:510")
            pass
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/live_scope.py:511")
    pass
# BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_MENU_END

# BYS360_MEETING_DEV_P0_NAV_FIX_LIVE_SCOPE_BEGIN
# Toplantı Geliştirme / Testleri / Derinleştirme / Final Kontrol ekranları
# performance_meeting_p3_reminders ve performance_development_guidance ile aynı
# canlı ayar/rol matrisi kapsamına eklendi.
_BYS360_MEETING_DEV_P0_NAV_FIX_KEYS = ['performance_meeting_development', 'performance_meeting_test_scenarios', 'performance_meeting_development_faz3', 'performance_meeting_final_gate']

for _name in ["LIVE_SETTINGS_MENU_KEYS", "LIVE_ALLOWED_MENU_KEYS", "LIVE_MENU_KEYS", "LIVE_PERFORMANCE_MENU_KEYS"]:
    _value = globals().get(_name)
    if isinstance(_value, set):
        _value.update(_BYS360_MEETING_DEV_P0_NAV_FIX_KEYS)
    elif isinstance(_value, list):
        _value.extend([_k for _k in _BYS360_MEETING_DEV_P0_NAV_FIX_KEYS if _k not in _value])
# BYS360_MEETING_DEV_P0_NAV_FIX_LIVE_SCOPE_END

