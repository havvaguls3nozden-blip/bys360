from __future__ import annotations



ROUTE_FAMILY = "institutional"

REQUIRED_ROUTE_MODULES = [
    "routes",
    "org_unit_routes",
    "repository_routes",
    "strategy_core_routes",
    "strategy_reports_routes",
    "strategy_phase3_routes",
    "strategy_lifecycle_routes",
    "strategy_workflow_routes",
    "strategy_archive_routes",
    "strategy_executive_routes",
    "strategy_governance_routes",
    "strategy_quality_routes",
    "strategy_review_routes",
    "strategy_notification_routes",
    "strategy_evidence_routes",
    "strategy_map_routes",
    "strategy_budget_routes",
    "strategy_stakeholder_routes",
    "strategy_indicator_routes",
    "strategy_coordination_routes",
    "strategy_launchpad_routes",
    "strategy_publication_routes",
    "strategy_readiness_routes",
    "strategy_management_pack_routes",
    "strategy_system_scan_routes",
    "strategy_hardening_routes",
    "education_video_routes",
    "education_video_stable_routes",
    "education_ebook_routes",
    "publication_routes",
    "education_certificate_routes",
]

OPTIONAL_ROUTE_MODULES = [
    "education_reports_routes",
    "education_suite_routes",
    "education_career_routes",
]

ROUTE_BUCKETS = {
    "strategy": [name for name in REQUIRED_ROUTE_MODULES if name.startswith("strategy_")],
    "education": [
        name
        for name in REQUIRED_ROUTE_MODULES + OPTIONAL_ROUTE_MODULES
        if name.startswith("education_") or name == "publication_routes"
    ],
    "core": ["routes", "org_unit_routes", "repository_routes"],
}