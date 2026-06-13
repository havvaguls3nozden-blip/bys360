"""Faz 1L communication aile gövde eritme spesifikasyonu."""

TARGETS = [
    {
        "target_module": "phase_dashboard_routes",
        "target_relpath": "app/communication/phase_dashboard_routes.py",
        "family": "dashboard",
        "sources": [
            {
                "module": "phase1_routes",
                "include": ["communication_phase1_dashboard_view"],
            },
            {
                "module": "phase2_routes",
                "include": ["communication_phase2_dashboard_view"],
            },
            {
                "module": "phase3_routes",
                "include": ["communication_phase3_dashboard_view"],
            },
        ],
    },
    {
        "target_module": "bulletins_family_routes",
        "target_relpath": "app/communication/bulletins_family_routes.py",
        "family": "bulletins",
        "sources": [
            {
                "module": "phase1_routes",
                "include": [
                    "communication_phase1_bulletins",
                    "communication_phase1_bulletin_new",
                    "communication_phase1_bulletin_detail",
                    "communication_phase1_bulletin_publish",
                    "communication_phase1_bulletin_acknowledge",
                ],
            },
            {
                "module": "phase2_routes",
                "include": [
                    "communication_phase2_bulletin_edit",
                    "communication_phase2_bulletin_history",
                    "communication_phase2_bulletin_archive",
                ],
            },
        ],
    },
    {
        "target_module": "survey_center_routes",
        "target_relpath": "app/communication/survey_center_routes.py",
        "family": "surveys",
        "sources": [
            {
                "module": "phase1_routes",
                "include": ["communication_phase1_survey_center"],
            },
            {
                "module": "phase2_routes",
                "include": [
                    "_parse_questions_from_request",
                    "_survey_form_state_from_request",
                    "_default_survey_form_state",
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
                ],
            },
            {
                "module": "phase3_routes",
                "include": [
                    "communication_phase3_my_surveys",
                    "communication_phase3_survey_take",
                    "communication_phase3_survey_remind",
                ],
            },
        ],
    },
    {
        "target_module": "notification_center_routes",
        "target_relpath": "app/communication/notification_center_routes.py",
        "family": "notifications",
        "sources": [
            {
                "module": "phase3_routes",
                "include": [
                    "communication_phase3_notifications",
                    "communication_phase3_notifications_read_all",
                    "communication_phase3_notification_read",
                ],
            },
        ],
    },
    {
        "target_module": "support_center_routes",
        "target_relpath": "app/communication/support_center_routes.py",
        "family": "support",
        "sources": [
            {
                "module": "phase1_routes",
                "include": ["communication_phase1_support_center"],
            },
            {
                "module": "phase3_routes",
                "include": [
                    "communication_phase3_support_queue",
                    "communication_phase3_support_detail",
                    "communication_phase3_support_assign",
                    "communication_phase3_support_status",
                    "communication_phase3_help_center",
                    "communication_phase3_help_article",
                ],
            },
        ],
    },
]

ROUTE_MANIFEST_PATH = "app/communication/route_manifest.py"
PHASE_FAMILY_ROUTES_PATH = "app/communication/phase_family_routes.py"
COMMUNICATION_ROUTES_HUB_PATH = "app/communication/routes.py"
BACKUP_ROOT = "refactor_backups/faz1l"
STAGE_ROOT = "refactor_staging/faz1l"
REPORT_ROOT = "reports/faz1l"