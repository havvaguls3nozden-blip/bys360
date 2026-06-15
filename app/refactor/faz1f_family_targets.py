from __future__ import annotations

CANONICAL_TARGETS = {
    "communication_routes": [
        "app/communication/messages_routes.py",
        "app/communication/announcements_routes.py",
        "app/communication/notifications_routes.py",
        "app/communication/surveys_routes.py",
        "app/communication/feedback_routes.py",
        "app/communication/routes.py",
    ],
    "communication_services": [
        "app/services/communication_service.py",
        "app/services/communication/messages_service.py",
        "app/services/communication/announcements_service.py",
        "app/services/communication/notifications_service.py",
        "app/services/communication/surveys_service.py",
    ],
    "communication_models": [
        "app/models/communication_models.py",
    ],
    "institutional_routes": [
        "app/institutional/repository_routes.py",
        "app/institutional/publication_routes.py",
        "app/institutional/org_unit_routes.py",
        "app/institutional/routes.py",
        "app/institutional/strategy_core_routes.py",
        "app/institutional/strategy_reports_routes.py",
        "app/institutional/strategy_review_routes.py",
        "app/institutional/education_suite_routes.py",
        "app/institutional/education_reports_routes.py",
    ],
    "admin_ai_routes": [
        "app/admin/ai_routes.py",
        "app/admin/routes.py",
        "app/admin/ops_routes.py",
    ],
    "root_hotfix_targets": [
        "app/schema_guard.py",
        "app/services/performance/common.py",
        "app/refactor/hotfix_merge_registry.py",
    ],
    "models": [
        "app/models/core_models.py",
        "app/models/performance_models.py",
        "app/models/communication_models.py",
        "app/models/education_models.py",
        "app/models/strategy_models.py",
        "app/models/repository_models.py",
    ],
}

PROTECTED_PATTERNS = [
    "__pycache__/",
    ".venv/",
    "migrations/",
    "reports/",
    "instance/",
    "uploads/",
]

REVIEW_ONLY_PATTERNS = [
    "strategy_phase3_routes.py",
    "education_phase",
    "schema_guard_phase",
    "ai_phase",
]