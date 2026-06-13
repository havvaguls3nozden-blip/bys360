"""Faz 1K phase1-3 aile bazlı kanonik route bridge spesifikasyonu."""

BRIDGES = [
    {
        "target_module": "phase_dashboard_routes",
        "target_relpath": "app/communication/phase_dashboard_routes.py",
        "imports": [
            ("phase1_routes", ["communication_phase1_dashboard_view"]),
            ("phase2_routes", ["communication_phase2_dashboard_view"]),
            ("phase3_routes", ["communication_phase3_dashboard_view"]),
        ],
        "ownership": ["faz dashboard", "durum özeti", "genel bakış"],
    },
    {
        "target_module": "bulletins_family_routes",
        "target_relpath": "app/communication/bulletins_family_routes.py",
        "imports": [
            ("phase1_routes", [
                "communication_phase1_bulletins",
                "communication_phase1_bulletin_new",
                "communication_phase1_bulletin_detail",
                "communication_phase1_bulletin_publish",
                "communication_phase1_bulletin_acknowledge",
            ]),
            ("phase2_routes", [
                "communication_phase2_bulletin_edit",
                "communication_phase2_bulletin_history",
                "communication_phase2_bulletin_archive",
            ]),
        ],
        "ownership": ["bulletin", "duyuru akışı", "okundu teyidi", "arşiv"],
    },
    {
        "target_module": "survey_center_routes",
        "target_relpath": "app/communication/survey_center_routes.py",
        "imports": [
            ("phase1_routes", ["communication_phase1_survey_center"]),
            ("phase2_routes", [
                "communication_phase2_surveys",
                "communication_phase2_survey_new",
                "communication_phase2_survey_edit",
                "communication_phase2_survey_duplicate",
                "communication_phase2_survey_archive",
                "communication_phase2_survey_reopen",
                "communication_phase2_survey_detail",
                "communication_phase2_survey_publish",
                "communication_phase2_survey_close",
                "communication_phase2_survey_results",
                "communication_phase2_survey_templates",
                "communication_phase2_survey_template_new",
                "communication_phase2_survey_template_edit",
            ]),
            ("phase3_routes", [
                "communication_phase3_my_surveys",
                "communication_phase3_survey_take",
                "communication_phase3_survey_remind",
            ]),
        ],
        "ownership": ["anket merkezi", "anket şablonu", "yanıtlama", "hatırlatma"],
    },
    {
        "target_module": "notification_center_routes",
        "target_relpath": "app/communication/notification_center_routes.py",
        "imports": [
            ("phase3_routes", [
                "communication_phase3_notifications",
                "communication_phase3_notifications_read_all",
                "communication_phase3_notification_read",
            ]),
        ],
        "ownership": ["bildirim merkezi", "okundu işaretle", "faz3 bildirim"],
    },
    {
        "target_module": "support_center_routes",
        "target_relpath": "app/communication/support_center_routes.py",
        "imports": [
            ("phase1_routes", ["communication_phase1_support_center"]),
            ("phase3_routes", [
                "communication_phase3_support_queue",
                "communication_phase3_support_detail",
                "communication_phase3_support_assign",
                "communication_phase3_support_status",
                "communication_phase3_help_center",
                "communication_phase3_help_article",
            ]),
        ],
        "ownership": ["destek merkezi", "yardım makalesi", "talep kuyruğu"],
    },
]

OLD_PHASE_MODULES = ["phase1_routes", "phase2_routes", "phase3_routes"]
ROUTE_MANIFEST_PATH = "app/communication/route_manifest.py"
PHASE_FAMILY_ROUTES_PATH = "app/communication/phase_family_routes.py"
COMMUNICATION_ROUTES_HUB_PATH = "app/communication/routes.py"
BACKUP_ROOT = "refactor_backups/faz1k"
STAGE_ROOT = "refactor_staging/faz1k"
REPORT_ROOT = "reports/faz1k"