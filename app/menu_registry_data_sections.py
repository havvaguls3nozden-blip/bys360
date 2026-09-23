"""BYS360 menu registry section data bridge module.

P11-D3 kapsamında `app/menu_registry.py` içindeki `MENU_SECTIONS`  # noqa: F821 - dynamic menu registry global
ve ona bağlı `ANNOUNCEMENT_TOOL_ROLES` veri blokları bu modüle taşınmıştır.

menu_key değerleri, sıralama mantığı ve veri içeriği değiştirilmemelidir.
"""
from __future__ import annotations

from typing import Any

ANNOUNCEMENT_TOOL_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "koordinator",
    "mali_musavir",
}

MENU_SECTIONS: list[dict[str, Any]] = [  # noqa: F821 - dynamic menu registry global
    {
        "key": "genel",
        "label": "Genel",
        "icon": "fa-solid fa-house",
        "items": [
            {
                "key": "dashboard",
                "label": "Dashboard",
                "icon": "fa-solid fa-chart-line",
                "endpoint": "main.dashboard",
                "active_endpoints": ["main.dashboard"],
            },
            {
                "key": "performance_tasks",
                "label": "Görevlerim",
                "icon": "fa-solid fa-list-check",
                "endpoint": "main.performance_tasks",
                "active_endpoints": ["main.performance_tasks", "main.performance_evaluate", "main.performance_v2_phase3_dashboard", "main.performance_v2_phase3_assignment", "main.performance_v2_phase4_dashboard", "main.performance_v2_phase4_assignment"],
            },
            {
                "key": "support_index",
                "label": "Destek & Talepler",
                "icon": "fa-solid fa-headset",
                "endpoint": "main.support_index",
                "active_endpoints": ["main.support_index", "main.support_detail", "main.support_setup"],
                "active_path_prefixes": ["/support"],
            },
            {
                "key": "support_new",
                "label": "Yeni Talep Aç",
                "icon": "fa-solid fa-plus",
                "endpoint": "main.support_new",
                "active_endpoints": ["main.support_new"],
                "active_path_prefixes": ["/support/new"],
            },
            {
                "key": "support_my_tickets",
                "label": "Taleplerim",
                "icon": "fa-solid fa-folder-open",
                "endpoint": "main.support_my_tickets",
                "active_endpoints": ["main.support_my_tickets"],
                "active_path_prefixes": ["/support/my-tickets"],
            },
            {
                "key": "support_assigned",
                "label": "Bana Atananlar",
                "icon": "fa-solid fa-user-check",
                "endpoint": "main.support_assigned",
                "active_endpoints": ["main.support_assigned"],
                "active_path_prefixes": ["/support/assigned"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "support_all",
                "label": "Tüm Talepler",
                "icon": "fa-solid fa-table-list",
                "endpoint": "main.support_all",
                "active_endpoints": ["main.support_all"],
                "active_path_prefixes": ["/support/all"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "notifications",
                "label": "Bildirimler",
                "icon": "fa-regular fa-bell",
                "dynamic_badge": "unread_notification_count",
                "endpoint": "main.notifications_list",
                "active_endpoints": ["main.notifications_list"],
                "active_endpoint_prefixes": ["main.notifications_"],
                "active_path_prefixes": ["/notifications"],
            },
            # BYS360_CORPORATE_PORTAL_V1_MENU_ITEMS
            {
                "key": "portal_feed",
                "label": "Kurumsal Portal",
                "icon": "fa-solid fa-stream",
                "endpoint": "main.portal_feed",
                "active_endpoint_prefixes": ["main.portal_"],
                "active_path_prefixes": ["/portal"],
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"],
            },
            {
                "key": "portal_profiles",
                "label": "Portal Profilim",
                "icon": "fa-regular fa-user",
                "endpoint": "main.portal_my_profile",
                "active_endpoints": ["main.portal_my_profile", "main.portal_profile"],
                "active_path_prefixes": ["/portal/profile"],
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"],
            },
            {
                "key": "portal_groups",
                "label": "Portal Grupları",
                "icon": "fa-solid fa-user-group",
                "endpoint": "main.portal_groups",
                "active_endpoints": ["main.portal_groups", "main.portal_group_detail"],
                "active_path_prefixes": ["/portal/groups"],
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"],
            },
            {
                "icon": "fa-solid fa-share-nodes",
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"],
            },
            {
                "key": "portal_press_news",
                "label": "Basında Tarihi Alan",
                "icon": "fa-regular fa-newspaper",
                "endpoint": "main.portal_press_news_review",
                "active_endpoints": ["main.portal_press_news_review"],
                "active_path_prefixes": ["/portal/press-news"],
                "roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"],
            },
            {
                "key": "portal_moderation",
                "label": "Portal Yönetimi",
                "icon": "fa-solid fa-shield-halved",
                "endpoint": "main.portal_moderation",
                "active_endpoints": ["main.portal_moderation"],
                "active_path_prefixes": ["/portal/moderation"],
                "roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"],
            },
            {
                "key": "performance_scorecard",
                "label": "Not Karnesi",
                "icon": "fa-solid fa-id-card",
                "endpoint": "main.performance_scorecard",
                "active_endpoints": ["main.performance_scorecard"],
            },
            {
                "key": "my_performance_comparison",
                "label": "Personel Analizi",
                "icon": "fa-solid fa-chart-line",
                "endpoint": "main.my_performance_comparison",
                "active_endpoints": ["main.my_performance_comparison"],
            },
            {
                "key": "performance_reports",
                "label": "Raporlar",
                "icon": "fa-solid fa-chart-pie",
                "endpoint": "main.performance_reports",
                "active_endpoint_prefixes": ["main.performance_reports"],
            },
        ],
    },
    {
        "key": "ik",
        "label": "Personel Yönetimi",
        "icon": "fa-solid fa-user-group",
        "items": [
            {
                "key": "admin_users",
                "label": "Personel Özlük Dosyaları",
                "icon": "fa-solid fa-folder-open",
                "endpoint": "main.admin_users",
                "active_endpoints": [
                    "main.admin_users",
                    "main.admin_user_create",
                    "main.admin_user_edit",
                    "main.personnel_list",
                    "main.personnel_add",
                    "main.personnel_edit",
                ],
                "active_path_prefixes": ["/admin/users", "/personnel"],
            },
            {
                "key": "org_units",
                "label": "Birim ve Pozisyon Yönetimi",
                "icon": "fa-solid fa-diagram-project",
                "endpoint": "main.admin_org_units",
                "active_endpoints": [
                    "main.admin_org_units",
                    "main.admin_org_unit_create",
                    "main.admin_org_unit_edit",
                ],
                "active_path_prefixes": ["/admin/org-units", "/org-units"],
            },
        ],
    },
    {
        "key": "performans",
        "label": "Performans Yönetimi",
        "icon": "fa-solid fa-chart-simple",
        "items": [
            {
                "key": "performance_criteria",
                "label": "Sorular / Kriterler",
                "icon": "fa-solid fa-list-ul",
                "endpoint": "main.performance_criteria",
                "active_endpoint_prefixes": ["main.performance_criteria"],
            },
            {
                "key": "performance_periods",
                "label": "Dönemler",
                "icon": "fa-solid fa-calendar-days",
                "endpoint": "main.performance_periods",
                "active_endpoint_prefixes": ["main.performance_period"],
            },
            {
                "key": "performance_period_management_center",
                "label": "Dönem Yönetim Merkezi",
                "icon": "fa-solid fa-calendar-check",
                "endpoint": "main.performance_v2_1_7_period_management_center",
                "active_endpoints": ["main.performance_v2_1_7_period_management_center"],
                "active_path_prefixes": ["/performance/v2-1-7-period-management-center", "/performans/donem-yonetim-merkezi"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"],
            },
{
    "key": "performance_evaluation_live_tracking",
    "label": "Canlı Değerlendirme Takibi",
    "icon": "fa-solid fa-chart-line",
    "endpoint": "main.performance_v2_1_10_evaluation_live_tracking",
    "active_endpoints": ['main.performance_v2_1_10_evaluation_live_tracking'],
    "active_path_prefixes": ['/performance/v2-1-10-evaluation-live-tracking', '/performans/canli-degerlendirme-takibi'],
    "required_roles": ['admin', 'baskan', 'baskan_yardimcisi', 'birim_sorumlusu', 'grup_baskani', 'koordinator', 'mali_musavir'],
},
{
    "key": "performance_evaluator_reminder_center",
    "label": "Amir Hatırlatma Merkezi",
    "icon": "fa-solid fa-bell",
    "endpoint": "main.performance_v2_1_11_evaluator_reminder_center",
    "active_endpoints": ['main.performance_v2_1_11_evaluator_reminder_center'],
    "active_path_prefixes": ['/performance/v2-1-11-evaluator-reminder-center', '/performans/amir-hatirlatma-merkezi'],
    "required_roles": ['admin', 'baskan', 'baskan_yardimcisi', 'birim_sorumlusu', 'grup_baskani', 'koordinator', 'mali_musavir'],
},
            {
                "key": "performance_evaluation_tasks",
                "label": "Değerlendirme Görevleri",
                "icon": "fa-solid fa-clipboard-check",
                "endpoint": "main.performance_evaluation_tasks",
                "active_endpoints": ["main.performance_evaluation_tasks"],
            },

            # BYS360_PHASE9_REMINDERS_MENU_REGISTRY_ITEM
            {
                "key": "performance_meeting_p3_reminders",
                "label": "Hatırlatma ve Aksatan Amirler",
                "icon": "fa-solid fa-bell",
                "endpoint": "main.performance_meeting_p3_reminders",
                "active_endpoints": [
                    "main.performance_meeting_p3_reminders",
                    "main.performance_meeting_p3_reminders_tr",
                    "main.performance_meeting_p3_reminders_apply",
                    "main.performance_meeting_p3_reminders_apply_tr",
                ],
                "active_path_prefixes": [
                    "/performance/meeting-development/faz9",
                    "/performans/toplanti-gelistirme/faz9-hatirlatma",
                ],
                "required_roles": [
                    "admin",
                    "super_admin",
                    "system_admin",
                    "sistem_yoneticisi",
                    "baskan",
                    "baskan_yardimcisi",
                    "grup_baskani",
                    "mali_musavir",
                    "koordinator",
                    "birim_sorumlusu",
                ],
            },
            # /BYS360_PHASE9_REMINDERS_MENU_REGISTRY_ITEM
            {
                "key": "performance_interim_notes",
                "label": "Dönem İçi Notlar",
                "icon": "fa-regular fa-note-sticky",
                "endpoint": "main.performance_interim_notes",
                "active_endpoints": ["main.performance_interim_notes", "main.performance_interim_notes_tr", "main.performance_interim_notes_create", "main.performance_interim_notes_create_tr"],
                "active_endpoint_prefixes": ["main.performance_interim_notes"],
                "active_path_prefixes": ["/performance/interim-notes", "/performans/donem-ici-notlar"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "performance_development_guidance",
                "label": "Gelişim Rehberi",
                "icon": "fa-solid fa-seedling",
                "endpoint": "main.performance_meeting_p4_development_guidance",
                "active_endpoints": ["main.performance_meeting_p4_development_guidance", "main.performance_meeting_p4_development_guidance_tr"],
                "active_path_prefixes": ["/performance/meeting-development/faz10", "/performans/toplanti-gelistirme/faz10-gelisim-rehberi"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            # BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_1
            {
                "key": "performance_meeting_development",
                "label": "Toplantı Geliştirme",
                "icon": "fa-solid fa-chalkboard-user",
                "endpoint": "main.performance_meeting_development",
                "active_endpoints": [
                    "main.performance_meeting_development",
                    "main.performance_meeting_development_tr",
                ],
                "active_path_prefixes": [
                    "/performance/meeting-development",
                    "/performans/toplanti-gelistirme",
                ],
                "required_roles": [
                    "admin",
                    "super_admin",
                    "system_admin",
                    "sistem_yoneticisi",
                    "baskan",
                    "baskan_yardimcisi",
                    "grup_baskani",
                    "mali_musavir",
                    "koordinator",
                    "birim_sorumlusu",
                ],
            },
            # /BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_1
            # BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_2
            {
                "key": "performance_meeting_test_scenarios",
                "label": "Toplantı Testleri",
                "icon": "fa-solid fa-vial",
                "endpoint": "main.performance_meeting_test_scenarios",
                "active_endpoints": [
                    "main.performance_meeting_test_scenarios",
                    "main.performance_meeting_test_scenarios_tr",
                ],
                "active_path_prefixes": [
                    "/performance/meeting-development/test-scenarios",
                    "/performans/toplanti-test-senaryolari",
                ],
                "required_roles": [
                    "admin",
                    "super_admin",
                    "system_admin",
                    "sistem_yoneticisi",
                    "baskan",
                    "baskan_yardimcisi",
                    "grup_baskani",
                    "mali_musavir",
                    "koordinator",
                    "birim_sorumlusu",
                ],
            },
            # /BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_2
            # BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_3
            {
                "key": "performance_meeting_development_faz3",
                "label": "Toplantı Derinleştirme",
                "icon": "fa-solid fa-diagram-project",
                "endpoint": "main.performance_meeting_development_faz3",
                "active_endpoints": [
                    "main.performance_meeting_development_faz3",
                    "main.performance_meeting_development_faz3_tr",
                ],
                "active_path_prefixes": [
                    "/performance/meeting-development/faz3",
                    "/performans/toplanti-gelistirme/derinlestirme",
                ],
                "required_roles": [
                    "admin",
                    "super_admin",
                    "system_admin",
                    "sistem_yoneticisi",
                    "baskan",
                    "baskan_yardimcisi",
                    "grup_baskani",
                    "mali_musavir",
                    "koordinator",
                    "birim_sorumlusu",
                ],
            },
            # /BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_3
            # BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_4
            {
                "key": "performance_meeting_final_gate",
                "label": "Final Kontrol",
                "icon": "fa-solid fa-shield-halved",
                "endpoint": "main.performance_meeting_final_gate",
                "active_endpoints": [
                    "main.performance_meeting_final_gate",
                    "main.performance_meeting_final_gate_tr",
                ],
                "active_path_prefixes": [
                    "/performance/meeting-development/final-gate",
                    "/performans/toplanti-gelistirme/final-kontrol",
                ],
                "required_roles": [
                    "admin",
                    "super_admin",
                    "system_admin",
                    "sistem_yoneticisi",
                    "baskan",
                    "baskan_yardimcisi",
                    "grup_baskani",
                    "mali_musavir",
                    "koordinator",
                    "birim_sorumlusu",
                ],
            },
            # /BYS360_MEETING_DEV_P0_NAV_FIX_ITEM_4
            {
                "key": "performance_task_management",
                "label": "Görev Yönetimi",
                "icon": "fa-solid fa-screwdriver-wrench",
                "endpoint": "main.performance_task_management",
                "active_endpoint_prefixes": ["main.performance_task_management"],
                "admin_only": True,
            },
            {
                "key": "performance_hierarchy_tree",
                "label": "Hiyerarşi Ağacı",
                "icon": "fa-solid fa-sitemap",
                "endpoint": "main.performance_hierarchy_tree",
                "active_endpoints": ["main.performance_hierarchy_tree", "main.hierarchy_tree"],
                "active_path_prefixes": ["/performance/hierarchy-tree"],
            },
            {
                "key": "performance_hierarchy_assignments",
                "label": "Hiyerarşi Atamaları & Ayarları",
                "icon": "fa-solid fa-code-branch",
                "endpoint": "main.performance_hierarchy_settings",
                "active_endpoints": [
                    "main.performance_hierarchy_settings",
                    "main.performance_hierarchy_assignments",
                    "main.hierarchy_assignments",
                    "main.performance_hierarchy_assignment_edit",
                ],
                "active_path_prefixes": ["/performance/hierarchy-settings", "/performance/hierarchy-assignments"],
            },
            {
                "key": "performance_team_compare",
                "label": "Personel Analizi",
                "icon": "fa-solid fa-people-arrows",
                "endpoint": "main.performance_team_compare",
                "active_endpoints": ["main.performance_team_compare"],
            },
            {
                "key": "performance_feedback_meetings",
                "label": "Randevu Sistemi",
                "icon": "fa-solid fa-calendar-week",
                "endpoint": "main.feedback_meetings_list",
                "active_endpoints": [
                    "main.feedback_meetings_list",
                    "main.feedback_meeting_detail",
                    "main.feedback_meeting_update",
                    "main.manager_feedback_request_schedule",
                    "main.manager_feedback_request_schedule_preview",
                    "main.feedback_operations_dashboard",
                    "main.feedback_audit_dashboard",
                    "main.feedback_watch_dashboard",
                    "main.feedback_watch_run_alerts",
                    "main.feedback_executive_summary_dashboard",
                    "main.feedback_executive_summary_run_digest",
                    "main.performance_go_live_center",
                ],
                "active_path_prefixes": [
                    "/performance/feedback-meetings",
                    "/performance/feedback-requests",
                    "/performance/feedback-ops",
                    "/performance/feedback-audit",
                    "/performance/feedback-watch",
                    "/performance/feedback-executive-summary",
                    "/performance/go-live-center",
                ],
            },
            {
                "key": "team_performance_comparison_history",
                "label": "Personel Dönem Analizi",
                "icon": "fa-solid fa-code-compare",
                "endpoint": "main.team_performance_comparison_history",
                "active_endpoints": ["main.team_performance_comparison_history"],
            },
            {
                "key": "performance_publish",
                "label": "Yayın Yönetimi",
                "icon": "fa-solid fa-bullhorn",
                "endpoint": "main.performance_publish_dashboard",
                "active_endpoint_prefixes": ["main.performance_publish", "main.performance_unpublish"],
            },
            {
                "key": "performance_president_approvals",
                "label": "Başkan Onayları",
                "icon": "fa-solid fa-stamp",
                "endpoint": "main.performance_president_approvals",
                "active_endpoints": ["main.performance_president_approvals", "main.performance_president_approval_approve", "main.performance_president_approval_return", "main.performance_president_card_review"],
                "active_path_prefixes": ["/performans/baskan-onaylari", "/performance/president-approvals"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan"],
            },
            {
                "key": "performance_archive",
                "label": "Geçmiş Karne Arşivi",
                "icon": "fa-solid fa-box-archive",
                "endpoint": "main.performance_archive",
                "active_endpoints": ["main.performance_archive", "main.performance_archive_new", "main.performance_archive_detail"],
                "active_path_prefixes": ["/performance/archive", "/performans/gecmis-karne-arsivi"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"],
            },
            # BYS360_PERFORMANCE_V2_1_3A_PERSONNEL_CATEGORY_SIDEBAR_ITEM
            {
                "key": "performance_personnel_category_card",
                "label": "Personel Kategori Atama",
                "icon": "fa-solid fa-tags",
                "endpoint": "main.performance_v2_1_3_personnel_category_card",
                "active_endpoints": ["main.performance_v2_1_3_personnel_category_card"],
                "active_path_prefixes": ["/performance/v2-1-3-personnel-category-card"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi"],
            },
            {
                "key": "performance_kpi_dashboard",
                "label": "KPI Dashboardu",
                "icon": "fa-solid fa-gauge-high",
                "endpoint": "strategic_performance.kpi_dashboard",
                "active_path_prefixes": ["/performans/stratejik/kpi-dashboard"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator"],
            },
            {
                "key": "performance_kpi_management",
                "label": "KPI ve Hedef Yönetimi",
                "icon": "fa-solid fa-bullseye",
                "endpoint": "strategic_performance.target_list",
                "active_path_prefixes": ["/performans/stratejik/hedefler"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator"],
            },
            {
                "key": "performance_competency_library",
                "label": "Yetkinlik Kütüphanesi",
                "icon": "fa-solid fa-book-open",
                "endpoint": "strategic_performance.competency_library",
                "active_path_prefixes": ["/performans/stratejik/yetkinlik-kutuphanesi"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "performance_self_assessment",
                "label": "Öz Değerlendirme",
                "icon": "fa-solid fa-user-check",
                "endpoint": "strategic_performance.kpi_dashboard",
                "active_path_prefixes": ["/performans/stratejik/oz-degerlendirme"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "performance_kpi_analysis",
                "label": "KPI Analiz Merkezi",
                "icon": "fa-solid fa-chart-column",
                "endpoint": "strategic_performance.kpi_dashboard",
                "active_path_prefixes": ["/performans/stratejik/kpi-analiz"],
                "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator"],
            },
        ],
    },
    {
        "key": "iletisim",
        "label": "İletişim ve Anket Yönetimi",
        "icon": "fa-solid fa-comments",
        "items": [
            {
                "key": "messages",
                "label": "Mesajlar",
                "icon": "fa-solid fa-envelope",
                "endpoint": "main.messages_inbox",
                "active_endpoint_prefixes": ["main.messages_"],
                "active_path_prefixes": ["/messages"],
            },
            {
                "key": "surveys",
                "label": "Anketler",
                "icon": "fa-solid fa-square-poll-vertical",
                "endpoint": "main.surveys_list",
                "active_endpoints": ["main.surveys_list", "main.survey_take", "main.survey_submit"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"],
            },
            {
                "key": "feedback_dashboard",
                "label": "Kurumsal Geri Bildirim",
                "icon": "fa-solid fa-heart-pulse",
                "endpoint": "main.feedback_dashboard",
                "active_endpoints": ["main.feedback_dashboard"],
                "active_path_prefixes": ["/feedback"],
            },
            {
                "key": "feedback_pulse",
                "label": "Nabız Yoklaması",
                "icon": "fa-solid fa-wave-square",
                "endpoint": "main.feedback_pulse",
                "active_endpoints": ["main.feedback_pulse"],
                "active_path_prefixes": ["/feedback/pulse"],
            },
            {
                "key": "feedback_campaigns",
                "label": "Geri Bildirim Kampanyaları",
                "icon": "fa-solid fa-clipboard-question",
                "endpoint": "main.feedback_campaigns",
                "active_endpoints": ["main.feedback_campaigns", "main.feedback_campaign_detail"],
                "active_path_prefixes": ["/feedback/campaigns"],
            },
            {
                "key": "feedback_results",
                "label": "Geri Bildirim Sonuçları",
                "icon": "fa-solid fa-chart-column",
                "endpoint": "main.feedback_results",
                "active_endpoints": ["main.feedback_results", "main.feedback_results_export"],
                "active_path_prefixes": ["/feedback/results"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "feedback_actions",
                "label": "İyileştirme Aksiyonları",
                "icon": "fa-solid fa-list-check",
                "endpoint": "main.feedback_actions",
                "active_endpoints": ["main.feedback_actions", "main.feedback_action_new"],
                "active_path_prefixes": ["/feedback/actions"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "feedback_manager",
                "label": "Yönetici Görünümü",
                "icon": "fa-solid fa-users-viewfinder",
                "endpoint": "main.feedback_manager",
                "active_endpoints": ["main.feedback_manager"],
                "active_path_prefixes": ["/feedback/manager"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "feedback_admin",
                "label": "Geri Bildirim Yönetimi",
                "icon": "fa-solid fa-sliders",
                "endpoint": "main.feedback_campaign_manage",
                "active_endpoints": ["main.feedback_campaign_manage", "main.feedback_campaign_new", "main.feedback_campaign_status"],
                "active_path_prefixes": ["/feedback/admin"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "survey_manage",
                "label": "Anket Yönetimi",
                "icon": "fa-solid fa-list-check",
                "endpoint": "main.survey_manage",
                "active_endpoints": ["main.survey_manage", "main.survey_create", "main.survey_edit"],
                "active_path_prefixes": ["/survey-manage"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "survey_results",
                "label": "Anket Sonuçları",
                "icon": "fa-solid fa-chart-column",
                "endpoint": "main.survey_results",
                "active_endpoints": ["main.survey_results"],
                "active_path_prefixes": ["/survey-results"],
                "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"],
            },
            {
                "key": "announcements",
                "label": "Duyurular",
                "icon": "fa-solid fa-bullhorn",
                "href": "/announcements",
                "active_endpoints": ["main.announcements_list"],
                "active_path_prefixes": ["/announcements"],
            },
            {
                "key": "announcements_create",
                "settings_key": "announcements",
                "label": "Duyuru Gönder",
                "icon": "fa-solid fa-paper-plane",
                "endpoint": "main.announcements_new",
                "active_endpoints": ["main.announcements_new"],
                "required_roles": sorted(ANNOUNCEMENT_TOOL_ROLES),
                "show_in_settings": False,
            },
        ],
    },
{
    "key": "ai",
    "label": "AI Karar Destek Merkezi",
    "icon": "fa-solid fa-brain",
    "items": [
        {
            "key": "ai_center",
            "label": "AI Kontrol Merkezi",
            "icon": "fa-solid fa-brain",
            "endpoint": "main.admin_ai_center",
            "active_endpoints": [
                "main.admin_ai_center",
                "main.admin_ai_operations_report",
                "main.admin_ai_module_health",
                "main.admin_ai_preflight",
                "main.admin_ai_smoke",
                "main.admin_ai_feedback",
                "main.admin_ai_settings",
                "main.admin_ai_governance_settings",
                "main.admin_ai_decision_history",
            ],
            "required_roles": ["admin"],
        },
    ],
},
{
        "key": "kullanici",
        "label": "Kullanıcı",
        "icon": "fa-solid fa-user-gear",
        "items": [
            {
                "key": "account",
                "label": "Hesabım",
                "icon": "fa-solid fa-user",
                "endpoint": "main.account",
                "active_endpoint_prefixes": ["main.account"],
            },
            {
                "key": "settings",
                "label": "Ayarlar",
                "icon": "fa-solid fa-sliders",
                "endpoint": "main.settings_page",
                "active_endpoints": ["main.settings_page"],
                "admin_only": True,
            },
            {
                "key": "db_check",
                "label": "DB Kontrol",
                "icon": "fa-solid fa-database",
                "endpoint": "main.db_check",
                "active_endpoints": ["main.db_check"],
                "admin_only": True,
            },
            {
                "key": "logout",
                "label": "Güvenli Çıkış",
                "icon": "fa-solid fa-right-from-bracket",
                "href": "#",
                "onclick": "submitLogoutForm(); return false;",
            },
        ],
    },
    # BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_SECTION
    {
        "key": "executive_summary",
        "label": "Yönetici Özeti",
        "icon": "fa-solid fa-chart-pie",
        "required_roles": ['admin', 'super_admin', 'system_admin', 'sistem_yoneticisi'],
        "items": [
            # BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_MENU_ITEM
            {
                "key": "daily_weather_mail",
                "label": "Günlük Personel Bilgilendirme",
                "icon": "fa-solid fa-cloud-sun-rain",
                "endpoint": "main.daily_weather_mail_settings",
                "url": "/executive-summary/daily-weather-mail",
                "active_endpoints": [
                    "main.daily_weather_mail_settings",
                    "main.daily_weather_mail_save_settings",
                    "main.daily_weather_mail_send_now",
                    "main.daily_weather_mail_dry_run",
                ],
                "active_path_prefixes": ["/executive-summary/daily-weather-mail", "/yonetici-ozeti/gunluk-hava-maili", "/communication/daily-weather-mail", "/iletisim/gunluk-hava-maili"],
                "required_roles": ['admin', 'super_admin', 'system_admin', 'sistem_yoneticisi'],
                "system_admin_only": True,
            },
            # /BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_MENU_ITEM
        ],
    },
    # /BYS360_DAILY_WEATHER_MAIL_V1_0_7_SYSTEM_ADMIN_SECTION

]

# BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_BEGIN
# Yönetici Özeti ailesi statik rol politikası: yalnız sistem yöneticisi / teknik admin.
try:
    _BYS360_EXEC_ADMIN_ONLY_ROLES = {'admin', 'administrator', 'sistem_yoneticisi', 'super_admin', 'system_admin'}
    _BYS360_EXEC_KNOWN_KEYS = {'daily_weather_mail', 'executive_summary_tasks', 'executive_summary_automatic_emails', 'executive_summary_auto_emails', 'executive_summary_logs', 'executive_summary_mail_logs', 'executive_summary_panel', 'executive_summary_test_send', 'executive_daily_weather_mail', 'executive_summary_scheduled_jobs', 'executive_summary_test', 'executive_summary', 'executive_summary_admin_panel', 'executive_summary_dashboard'}
    for _policy_name in ["ROLE_MENU_DEFAULTS", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY", "PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY"]:
        _policy = globals().get(_policy_name)
        if isinstance(_policy, dict):
            for _key in _BYS360_EXEC_KNOWN_KEYS:
                if _key in _policy or _key.startswith("executive") or _key == "daily_weather_mail":
                    _policy[_key] = set(_BYS360_EXEC_ADMIN_ONLY_ROLES)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_sections.py:675")
    pass
# BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_END

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

# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_MENU_BEGIN
try:
    _bys360_v214_key = "performance_category_scope_visibility"
    _bys360_v214_item = {
        "key": _bys360_v214_key,
        "label": "Kategori Kapsam Hazırlığı",
        "icon": "fa-solid fa-layer-group",
        "endpoint": "main.performance_v2_1_4_category_scope",
        "active_endpoints": ["main.performance_v2_1_4_category_scope", "performance_v2_1_4_category_scope"],
        "active_path_prefixes": ["/performance/v2-1-4-category-scope"],
        "url": "/performance/v2-1-4-category-scope",
        "href": "/performance/v2-1-4-category-scope",
        "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi"],
    }
    if "MENU_SECTIONS" in globals():
        _section_found = False
        for _section in MENU_SECTIONS:  # noqa: F821 - dynamic menu registry global
            _section_key = str((_section or {}).get("key") or "").lower()
            _section_label = str((_section or {}).get("label") or "").lower()
            if _section_key in {"performans", "performance", "performance_management"} or "performans" in _section_label:
                _items = _section.setdefault("items", [])
                if not any(((_item or {}).get("key") == _bys360_v214_key) for _item in _items):
                    _inserted = False
                    for _idx, _item in enumerate(list(_items)):
                        if ((_item or {}).get("key") == "performance_personnel_category_card"):
                            _items.insert(_idx + 1, dict(_bys360_v214_item))
                            _inserted = True
                            break
                    if not _inserted:
                        _items.append(dict(_bys360_v214_item))
                _section_found = True
                break
        if not _section_found:
            MENU_SECTIONS.append({"key": "performans", "label": "Performans Yönetimi", "icon": "fa-solid fa-chart-line", "items": [dict(_bys360_v214_item)]})  # noqa: F821 - dynamic menu registry global
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_sections.py:767")
    pass
# BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_MENU_END

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
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_sections.py:787")
            pass
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_sections.py:788")
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
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_sections.py:808")
            pass
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/menu_registry_data_sections.py:809")
    pass
# BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_MENU_END
# BYS360_PORTAL_EXPERIENCE_V3B8C_MENU_KEYS_DOCUMENTATION_BEGIN
# Portal menü anahtarları V3B8C ile korunur:
# portal_feed, portal_people, portal_profiles, portal_groups, portal_press_news, portal_moderation
# Sosyal medya link havuzu sayfası bilinçli olarak geri getirilmez: portal_social_import yok.
# BYS360_PORTAL_EXPERIENCE_V3B8C_MENU_KEYS_DOCUMENTATION_END

